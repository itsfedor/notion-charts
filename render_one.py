#!/usr/bin/env python3
"""spec.json -> HTML -> 2x transparent PNG + QA checks (Notion chart pipeline).

Usage: python3 render_one.py spec.json out.png [--width 920]
Prints a QA json (root size, fonts, overflow, element counts, png size).
Exit code != 0 when overflow or a missing font is detected.
"""
import json
import os
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chartgen  # noqa: E402
from render_chart import render  # noqa: E402


def png_size(path):
    raw = open(path, "rb").read()
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", "not a png"
    w, h = struct.unpack(">II", raw[16:24])
    return w, h


def main():
    spec_path = sys.argv[1]
    out_png = sys.argv[2]
    width = 920
    if "--width" in sys.argv:
        width = int(sys.argv[sys.argv.index("--width") + 1])
    spec = json.load(open(spec_path, encoding="utf-8"))
    outdir = os.path.dirname(os.path.abspath(out_png))
    os.makedirs(outdir, exist_ok=True)
    base = os.path.join(outdir, "base.css")
    if os.path.abspath(base) != os.path.join(HERE, "base.css"):
        shutil.copy(os.path.join(HERE, "base.css"), base)
    html_path = os.path.splitext(out_png)[0] + ".html"
    open(html_path, "w", encoding="utf-8").write(chartgen.build_html(spec))
    qa = render(html_path, out_png, width)
    w, h = png_size(out_png)
    qa["png"] = "%dx%d" % (w, h)
    fonts = [f for f in qa.get("fonts", []) if "Inter" in f]
    unloaded = [f for f in fonts if not f.endswith("loaded")]
    qa["inter_missing"] = unloaded
    qa["ok"] = (not qa.get("overflow")) and (not unloaded) and w == 2 * width - 12 or w > 1500
    print(json.dumps(qa, ensure_ascii=False, indent=1))
    if qa.get("overflow") or unloaded:
        sys.exit(2)


if __name__ == "__main__":
    main()
