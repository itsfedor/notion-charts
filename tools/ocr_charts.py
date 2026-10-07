"""OCR both charts + detect text colors per line (TSV + pixel sampling)."""
import subprocess, struct, zlib, sys
from collections import defaultdict

def png_pixels(path):
    """Minimal PNG decoder (grey/RGB/palette/RGBA, non-interlaced) via zlib."""
    raw = open(path, "rb").read()
    pos = 8
    w = h = None
    idat = b""
    plte = None
    bitdepth = colortype = None
    while pos < len(raw):
        ln = struct.unpack(">I", raw[pos:pos+4])[0]
        typ = raw[pos+4:pos+8]
        data = raw[pos+8:pos+8+ln]
        if typ == b"IHDR":
            w, h, bitdepth, colortype = struct.unpack(">IIBB", data[:10])
        elif typ == b"PLTE":
            plte = data
        elif typ == b"IDAT":
            idat += data
        elif typ == b"IEND":
            break
        pos += 12 + ln
    assert bitdepth == 8, bitdepth
    nch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[colortype]
    dec = zlib.decompress(idat)
    stride = w * nch
    # unfilter
    out = bytearray(w * h * nch)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = dec[p]; p += 1
        line = bytearray(dec[p:p+stride]); p += stride
        if f == 1:
            for i in range(nch, stride):
                line[i] = (line[i] + line[i-nch]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i-nch] if i >= nch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i-nch] if i >= nch else 0
                b = prev[i]
                c = prev[i-nch] if i >= nch else 0
                pp = a + b - c
                pa, pb, pc = abs(pp-a), abs(pp-b), abs(pp-c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out[y*stride:(y+1)*stride] = line
        prev = line
    if colortype == 3:
        # expand palette indices to RGB
        rgb = bytearray(w * h * 3)
        for i in range(w * h):
            idx = out[i] * 3
            rgb[i*3:i*3+3] = plte[idx:idx+3]
        return w, h, 3, bytes(rgb)
    return w, h, nch, bytes(out)

def ocr_lines(path):
    tsv = subprocess.run(["tesseract", path, "stdout", "--psm", "3", "tsv"],
                         capture_output=True, text=True).stdout
    lines = defaultdict(list)
    for row in tsv.splitlines()[1:]:
        parts = row.split("\t")
        if len(parts) < 12:
            continue
        level, page, block, par, line, word = map(int, parts[:6])
        left, top, wd, ht, conf = int(parts[6]), int(parts[7]), int(parts[8]), int(parts[9]), float(parts[10])
        text = parts[11]
        if level == 5 and text.strip() and conf > 30:
            lines[(block, par, line)].append((left, top, wd, ht, text))
    out = []
    for key in sorted(lines):
        words = sorted(lines[key])
        top = min(w[1] for w in words); bot = max(w[1]+w[3] for w in words)
        left = min(w[0] for w in words); right = max(w[0]+w[2] for w in words)
        out.append({"top": top, "bot": bot, "left": left, "right": right,
                    "text": " ".join(w[4] for w in words)})
    return sorted(out, key=lambda r: (r["top"], r["left"]))

def line_colors(pix, w, h, nch, rows):
    """Mean color of non-background pixels in each text line band."""
    res = []
    for r in rows:
        y0, y1 = max(0, r["top"]-2), min(h, r["bot"]+2)
        x0, x1 = max(0, r["left"]-2), min(w, r["right"]+2)
        acc = defaultdict(int); n = 0
        for y in range(y0, y1, 2):
            base = y * w * nch
            for x in range(x0, x1, 2):
                i = base + x * nch
                R, G, B = pix[i], pix[i+1], pix[i+2]
                if R > 235 and G > 235 and B > 235:
                    continue                      # white/near-white bg
                if abs(R-G) < 18 and abs(G-B) < 18 and R < 90:
                    acc["black"] += 1            # dark text
                elif G > R + 25 and G > B + 25:
                    acc["green"] += 1
                elif R > G + 40 and R > B + 40:
                    acc["red"] += 1
                elif B > R + 20 and B > G + 10:
                    acc["blue"] += 1
                elif R > 200 and G > 200 and B < 200:
                    acc["yellow"] += 1
                else:
                    acc["other"] += 1
                n += 1
        res.append((r, dict(acc), n))
    return res


if __name__ == "__main__":
    import sys as _sys
    for fn in _sys.argv[1:]:
        print("=" * 30, fn)
        w, h, nch, pix = png_pixels(fn)
        rows = ocr_lines(fn)
        colors = line_colors(pix, w, h, nch, rows)
        for r, cc, n in colors:
            tot = sum(cc.values()) or 1
            dom = max(cc, key=cc.get)
            share = {k: round(v*100/tot) for k, v in sorted(cc.items(), key=lambda x: -x[1])[:3] if v}
            print("y%-4d x%-4d | %-60s | %s %s" % (r["top"], r["left"], r["text"][:60], dom, share))
    
