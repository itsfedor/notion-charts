# Redesigning an existing chart

Sometimes the chart already exists as an image (a textbook scan, a screenshot,
a page export) and you want it in the house style. The pipeline reads the
source without a vision model: OCR gives you the content, a colour map gives
you the structure, and you write a spec.

## 1. Transcribe the source

```bash
python3 tools/ocr_charts.py source.png
```

Prints every text line with its position and the dominant colour bucket of
that line (black / green / red / blue / yellow + tints). That is enough to
recover both the content and the highlight logic: which forms are green
(target), which are marked wrong, what is a note or a callout.

Requires `tesseract` (`apt-get install tesseract-ocr`).

## 2. Map the layout

```bash
python3 tools/color_map.py source.png
```

Prints a coarse letter grid of the image: each cell classified into the
nearest legend colour. Letter `B` = blue, `e` = green tint, `r` = red tint and
so on. Use it to see where the boxes, chips and panels sit before you design.

## 3. Write the spec

Design the spec (see [spec-reference.md](spec-reference.md)): keep the content
and the teaching point, rebuild the structure as title + blocks + highlights.
Do not flatten a scene into a banner, and do not copy surrounding prose into
the chart.

## 4. Render and QA

```bash
python3 render_one.py spec.json out.png
```

Exit code 0 with `"ok": true` means the chart is ready: no overflow, Inter
loaded, PNG at 2×. Iterate on the spec, not on the PNG. Never hand-edit the
render.

## Rule of thumb

Content accuracy beats art fidelity. If the OCR of a graphic-heavy chart is
too sparse to rebuild faithfully, rebuild the same teaching point from the
lesson text instead of guessing at the art.
