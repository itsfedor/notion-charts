"""Coarse color-grid map of a chart: each cell -> legend letter."""
import sys
from collections import Counter
from ocr_charts import png_pixels

LEGEND = [
    (' ', (255, 255, 255), 26),   # white
    ('.', (245, 245, 245), 20),   # light gray
    (',', (235, 235, 235), 18),   # gray
    ('B', (18, 121, 182), 60),    # blue
    ('b', (54, 80, 112), 60),     # dark blue-gray
    ('G', (0, 176, 80), 60),      # green
    ('g', (21, 167, 58), 60),     # green2
    ('O', (232, 81, 16), 60),     # orange
    ('R', (199, 0, 4), 60),       # red
    ('Y', (254, 197, 9), 60),     # yellow
    ('P', (151, 50, 135), 60),    # purple
    ('K', (0, 0, 0), 30),         # black text
    ('p', (237, 234, 240), 12),   # purple tint
    ('r', (244, 233, 233), 12),   # red tint
    ('e', (239, 243, 234), 12),   # green tint
    ('y', (254, 254, 237), 12),   # yellow tint
    ('u', (233, 242, 245), 12),   # blue tint
    ('o', (251, 243, 221), 12),   # orange tint
]

def classify(rgb):
    best, bd = '?', 10**9
    for ch, col, boost in LEGEND:
        d = sum((a-b)**2 for a, b in zip(rgb, col))
        if d < bd:
            bd = d; best = ch
    return best

def gridmap(fn, cols=56):
    w, h, nch, pix = png_pixels(fn)
    rows = int(cols * h / w / 2.1)
    cw, chh = w / cols, h / rows
    print('#' * 20, fn.split('/')[-1], '(%dx%d)' % (w, h), 'grid %dx%d' % (cols, rows))
    for ry in range(rows):
        line = ''
        for rx in range(cols):
            cnt = Counter()
            for y in range(int(ry*chh), int((ry+1)*chh), 2):
                base = y * w * nch
                for x in range(int(rx*cw), int((rx+1)*cw), 2):
                    i = base + x * nch
                    cnt[classify((pix[i], pix[i+1], pix[i+2]))] += 1
            # prefer non-background letters when present in >=15% of cells
            tot = sum(cnt.values())
            pick = ''
            for ch, n in cnt.most_common():
                if ch not in ' .,' or not pick:
                    if n >= tot * 0.15 or not pick:
                        pick = pick or ch
                        if ch not in ' .,':
                            pick = ch
                            break
            line += pick or ' '
        print(line)

if __name__ == "__main__":
    for fn in sys.argv[1:]:
        gridmap(fn)
        print()
