#!/usr/bin/env python3
"""Notion-style chart generator for course and lesson materials.

Takes a small JSON spec and produces the house-style HTML (base.css tokens,
transparent canvas, 880px wide) that render_chart.py turns into a 2x PNG.

Usage:
  python3 chartgen.py spec.json out.html            # write html
  python3 chartgen.py spec.json                     # write <spec>.html next to spec
  python3 render_one.py spec.json out.png           # html + render + QA (preferred)

Spec (all fields optional except title):
{
  "eyebrow": "Present simple · form",         # small gray caps above the title
  "title": "The verb **be** — am / is / are", # **x** = green highlight
  "blocks": [ ... ]                           # rendered top→bottom
}

Rich-text markers usable in ANY text field:
  **x** green highlight | ~~x~~ red highlight | __x__ blue | ==x== gray
  (HTML entities and plain unicode/emoji pass straight through)

Block kinds:
  {"kind":"table", "caps":"Short answers",
   "cols": ["", "Positive", "Negative"],      # header row (omit for no header)
   "col_colors": ["", "green", "orange"],     # pill colour per column
   "rows": [{"head":"I", "cells":["Yes, I am|Yes, I'm", "No, I'm not"]}]}
  {"kind":"cards", "cols": 2,
   "cards":[{"color":"blue","emoji":"👋","title":"Introducing people",
             "lines":["**I'm** Steven, and this **is** Isabella."]}]}
  {"kind":"list", "lines":["line 1", "line 2"]}
  {"kind":"pills", "caps":"", "groups":[{"label":"I / You / We / They","pills":"work|don't work|Do … work?"}]}
  {"kind":"note", "color":"yellow", "title":"...",
   "lines":[{"mark":"✓","text":"..."},{"mark":"✗","text":"..."}]}
  {"kind":"illustration", "cols":[{"emoji":"👈","title":"here"},{"emoji":"👉","title":"there"}],
   "rows":[{"label":"singular","cells":[{"figure":"🐵","word":"this","caption":"**This** is a monster."}]}]}
  {"kind":"images", "srcs":["file or url", ...]}   # raw <img> row (rare)
"""
import html
import json
import os
import re
import sys

COLORS = {
    "gray": ("var(--fill2)", "var(--tx2)"),
    "green": ("var(--green-bg)", "var(--green-tx)"),
    "red": ("var(--red-bg)", "var(--red-tx)"),
    "blue": ("var(--blue-bg)", "var(--blue-tx)"),
    "orange": ("var(--orange-bg)", "var(--orange-tx)"),
    "purple": ("var(--purple-bg)", "var(--purple-tx)"),
    "yellow": ("var(--yellow-bg)", "var(--yellow-tx)"),
    "brown": ("var(--brown-bg)", "var(--brown-tx)"),
    "pink": ("var(--pink-bg)", "var(--pink-tx)"),
}
HL = {"**": "hl-green", "~~": "hl-red", "__": "hl-blue", "==": "hl-gray"}


def rich(text):
    """Escape + apply the highlight markers (markers are paired)."""
    if text is None:
        return ""
    t = html.escape(str(text), quote=False)
    for mark, cls in HL.items():
        pat = re.escape(mark) + r"(.+?)" + re.escape(mark)
        t = re.sub(pat, lambda m: '<span class="hl %s">%s</span>' % (cls, m.group(1)), t, flags=re.S)
    t = t.replace("\n", "<br>")
    return t


def pills(cell, default_color="gray"):
    """A cell -> pills html. 'a|b' splits; per-pill colour via 'color:text'."""
    out = []
    items = cell if isinstance(cell, list) else str(cell).split("|")
    for it in items:
        it = it.strip()
        if not it:
            continue
        c = default_color
        m = re.match(r"^(gray|green|red|blue|orange|purple|yellow|brown|pink):(.*)$",
                     it, re.S)
        if m:
            c, it = m.group(1), m.group(2)
        bg, tx = COLORS.get(c, COLORS["gray"])
        out.append('<span class="pill" style="background:%s;color:%s">%s</span>'
                   % (bg, tx, rich(it)))
    return "".join(out)


def block_html(b):
    k = b.get("kind")
    if k == "table":
        cols = b.get("cols") or []
        cc = b.get("col_colors") or []
        head = ""
        if cols:
            head = ('<div class="thead" style="grid-template-columns:%s">%s</div>'
                    % (b.get("grid", "78px 1fr 1fr 1fr"),
                       "".join("<span>%s</span>" % rich(c) for c in cols)))
        rows = []
        for r in b.get("rows") or []:
            cells = r.get("cells") or []
            tds = []
            for i, cell in enumerate(cells):
                dflt = cc[i] if i < len(cc) and cc[i] else "gray"
                if isinstance(cell, dict) and "text" in cell:
                    inner = rich(cell["text"])
                else:
                    inner = pills(cell, dflt)
                tds.append('<div class="cell">%s</div>' % inner)
            rows.append('<div class="trow" style="grid-template-columns:%s">'
                        '<div class="pron">%s</div>%s</div>'
                        % (b.get("grid", "78px 1fr 1fr 1fr"),
                           rich(r.get("head", "")), "".join(tds)))
        caps = ('<div class="caps">%s</div>' % rich(b["caps"])) if b.get("caps") else ""
        return '<div class="card">%s%s%s</div>' % (caps, head, "".join(rows))

    if k == "cards":
        cards = []
        for c in b.get("cards") or []:
            color = c.get("color", "gray")
            bg, tx = COLORS.get(color, COLORS["gray"])
            lines = "".join("<p>%s</p>" % rich(l) for l in c.get("lines") or [])
            emo = ('<span class="emo">%s</span>' % c["emoji"]) if c.get("emoji") else ""
            cards.append('<div class="ucard" style="background:%s">'
                         '<div class="cat" style="color:%s">%s%s</div>%s</div>'
                         % (bg, tx, emo, rich(c.get("title", "")), lines))
        n = int(b.get("cols", 2))
        return '<div class="grid%d">%s</div>' % (n, "".join(cards))

    if k == "list":
        lines = "".join('<p class="ll">%s</p>' % rich(l) for l in b.get("lines") or [])
        return '<div class="card"><div class="list">%s</div></div>' % lines

    if k == "pills":
        rows = []
        for g in b.get("groups") or []:
            color = g.get("color", "gray")
            lab = ('<div class="ghead">%s</div>' % rich(g["label"])) if g.get("label") else ""
            rows.append('<div class="grow">%s<div class="cell">%s</div></div>'
                        % (lab, pills(g.get("pills", ""), color)))
        caps = ('<div class="caps">%s</div>' % rich(b["caps"])) if b.get("caps") else ""
        return '<div class="card">%s%s</div>' % (caps, "".join(rows))

    if k == "note":
        color = b.get("color", "yellow")
        bg, tx = COLORS.get(color, COLORS["yellow"])
        lines = []
        for l in b.get("lines") or []:
            if isinstance(l, dict):
                mark = l.get("mark", "")
                cls = {"✓": "mk-v", "✗": "mk-x", "+": "mk-v", "-": "mk-x"}.get(mark, "")
                mk = ('<span class="mk %s">%s</span>&nbsp; ' % (cls, html.escape(mark))
                      if mark else "")
                lines.append('<div class="dial">%s%s</div>' % (mk, rich(l.get("text", ""))))
            else:
                lines.append('<div class="dial">%s</div>' % rich(l))
        ttl = ('<div class="nt" style="color:%s">%s</div>' % (tx, rich(b["title"]))
               if b.get("title") else "")
        return '<div class="note" style="background:%s">%s%s</div>' % (bg, ttl, "".join(lines))

    if k == "illustration":
        cols = b.get("cols") or []
        grid = "92px " + " ".join(["1fr"] * max(1, len(cols)))
        out = ['<div class="matrix" style="grid-template-columns:%s">' % grid,
               '<div class="corner"></div>']
        for c in cols:
            emo = ('<span class="emo">%s</span>' % c["emoji"]) if c.get("emoji") else ""
            color = c.get("color", "gray")
            _, tx = COLORS.get(color, COLORS["gray"])
            out.append('<div class="colh" style="color:%s">%s%s</div>'
                       % (tx, emo, rich(c.get("title", ""))))
        for r in b.get("rows") or []:
            out.append('<div class="rowh">%s</div>' % rich(r.get("label", "")))
            for cell in r.get("cells") or []:
                color = cell.get("color", "gray")
                bg, tx = COLORS.get(color, COLORS["gray"])
                word = rich(cell.get("word", ""))
                cap = ('<div class="ex">%s</div>' % rich(cell["caption"])) if cell.get("caption") else ""
                out.append('<div class="q" style="background:%s">'
                           '<div class="mon">%s</div>'
                           '<div class="fw" style="color:%s">%s</div>%s</div>'
                           % (bg, cell.get("figure", ""), tx, word, cap))
        out.append("</div>")
        return "".join(out)

    if k == "images":
        srcs = b.get("srcs") or []
        imgs = "".join('<img src="%s" style="max-width:100%%">' % s for s in srcs)
        return '<div class="card">%s</div>' % imgs

    raise ValueError("unknown block kind: %r" % k)


CSS = """
  .chart { width: 880px; }
  .eyebrow { font-size: 11.5px; font-weight: 600; letter-spacing: .1em;
             text-transform: uppercase; color: var(--tx2); margin: 2px 0 7px 2px; }
  h1 { font-size: 27px; font-weight: 700; letter-spacing: -.02em; margin: 1px 0 17px 2px; color: var(--tx); }
  h1 .hl { padding: 2px 10px 3px; }
  .card { padding: 14px 18px 10px; margin-bottom: 12px; }
  .caps { font-size: 11px; font-weight: 600; letter-spacing: .08em;
          text-transform: uppercase; color: var(--tx2); margin-bottom: 10px; }
  .thead { display: grid; padding: 0 0 7px; border-bottom: 1px solid var(--line);
           font-size: 11px; font-weight: 600; letter-spacing: .08em;
           text-transform: uppercase; color: var(--tx2); }
  .trow { display: grid; padding: 9px 0; border-bottom: 1px solid #F1F1EF; align-items: start; }
  .trow:last-child { border-bottom: 0; padding-bottom: 4px; }
  .pron { font-size: 13.5px; font-weight: 500; color: var(--tx); padding-top: 3px; }
  .cell { line-height: 1.9; font-size: 13.5px; color: var(--tx); }
  .pill { display: inline-block; border-radius: 4px; padding: 2px 8px 3px;
          font-size: 12.5px; font-weight: 600; margin: 0 4px 4px 0; letter-spacing: -.005em; }
  .grow { display: grid; grid-template-columns: 200px 1fr; gap: 10px;
          padding: 7px 0; border-bottom: 1px solid #F1F1EF; align-items: start; }
  .grow:last-child { border-bottom: 0; }
  .ghead { font-size: 13px; font-weight: 600; color: var(--tx); padding-top: 3px; }
  .grid1, .grid2, .grid3 { display: grid; gap: 10px; margin-bottom: 12px; }
  .grid1 { grid-template-columns: 1fr; }
  .grid2 { grid-template-columns: 1fr 1fr; }
  .grid3 { grid-template-columns: 1fr 1fr 1fr; }
  .grid1 .ucard, .grid2 .ucard, .grid3 .ucard { border-radius: 8px; padding: 12px 15px 13px; }
  .cat { font-size: 11px; font-weight: 600; letter-spacing: .08em;
         text-transform: uppercase; margin-bottom: 7px;
         display: flex; align-items: center; gap: 6px; }
  .emo { font-size: 14.5px; letter-spacing: 0;
         font-family: 'Noto Color Emoji', 'Apple Color Emoji', 'Segoe UI Emoji', sans-serif; }
  .ucard p, .ll { font-size: 13.5px; line-height: 1.75; color: var(--tx); }
  .ucard p + p, .ll + .ll { margin-top: 2px; }
  .card .list { padding-bottom: 4px; }
  .card .ll { padding: 3px 0; }
  .hl { border-radius: 3px; padding: 1px 5px; font-weight: 600; }
  .hl-green { background: var(--green-bg); color: var(--green-tx); }
  .hl-red   { background: var(--red-bg);   color: var(--red-tx); }
  .hl-blue  { background: var(--blue-bg);  color: var(--blue-tx); }
  .hl-gray  { background: var(--fill2);    color: var(--tx); }
  .note { border-radius: 8px; padding: 13px 16px 12px; margin-bottom: 12px; }
  .note .nt { font-size: 13.5px; font-weight: 600; margin-bottom: 8px; }
  .note .dial { font-size: 13px; color: var(--tx); margin: 3px 0; }
  .mk { font-weight: 700; }
  .mk-x { color: var(--red-tx); }
  .mk-v { color: var(--green-tx); }
  .matrix { display: grid; gap: 14px 12px; margin-bottom: 12px; }
  .colh { display: flex; align-items: center; justify-content: center; gap: 7px;
          font-size: 12.5px; font-weight: 600; letter-spacing: .1em;
          text-transform: uppercase; padding-bottom: 12px; }
  .colh .emo { font-size: 21px; }
  .rowh { display: flex; align-items: center; justify-content: flex-end;
          padding-right: 5px; font-size: 11px; font-weight: 600;
          letter-spacing: .08em; text-transform: uppercase; color: var(--tx2); }
  .q { border-radius: 10px; padding: 18px; min-height: 150px;
       display: flex; flex-direction: column; align-items: center; justify-content: center; }
  .mon { display: flex; gap: 10px; align-items: center; justify-content: center;
         font-size: 64px; line-height: 1.15; margin-bottom: 14px;
         font-family: 'Noto Color Emoji', 'Apple Color Emoji', 'Segoe UI Emoji', sans-serif; }
  .fw { font-size: 27px; font-weight: 700; letter-spacing: -.01em; }
  .ex { font-size: 15.5px; color: var(--tx); margin-top: 7px; }
"""

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="base.css">
<style>%s</style>
</head>
<body>
<div class="chart">
%s
</div>
</body>
</html>
"""


def build_html(spec):
    parts = []
    if spec.get("eyebrow"):
        parts.append('<div class="eyebrow">%s</div>' % rich(spec["eyebrow"]))
    if spec.get("title"):
        parts.append("<h1>%s</h1>" % rich(spec["title"]))
    for b in spec.get("blocks") or []:
        parts.append(block_html(b))
    return PAGE % (CSS, "\n".join(parts))


def main():
    spec_path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(spec_path)[0] + ".html"
    spec = json.load(open(spec_path, encoding="utf-8"))
    html_txt = build_html(spec)
    # base.css lives next to this script
    open(out, "w", encoding="utf-8").write(html_txt)
    print("wrote", out)


if __name__ == "__main__":
    main()
