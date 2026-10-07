# Spec reference

`chartgen.py` turns a JSON spec into the house Notion-style chart: a
transparent canvas, 880px wide, Inter, the pastel Notion palette defined in
`base.css`.

```
python3 chartgen.py spec.json out.html          # → html only
python3 render_one.py spec.json out.png         # → html + 2x PNG + QA (use this)
```

`render_one.py` writes `<out>.html`, copies `base.css` next to it, renders
`.chart` at deviceScaleFactor 2 (a PNG of roughly 1760–1840px wide) and prints
a QA JSON. **Exit code 2 = overflow or a missing font → fix the spec and
re-render.** Run `render_one.py` from the repo root so its imports resolve.

## Spec shape

```json
{
  "eyebrow": "Present simple · form",            // small gray caps (optional)
  "title": "The verb **be** — am / is / are",    // big headline (required)
  "blocks": [ ... ]                              // rendered top → bottom
}
```

Rich-text markers usable in ANY text value (paired, inside one string):
`**green highlight**` · `~~red highlight~~` · `__blue highlight__` ·
`==gray highlight==`. Plain text, unicode arrows (→ ⇒) and emojis pass
straight through.

### Block kinds

**table** — the workhorse (form tables, "short answers", spelling rules):

```json
{"kind": "table",
 "caps": "Short answers",                     // optional card caption
 "cols": ["", "Positive", "Negative"],        // header row; OMIT for no header
 "grid": "96px 1.1fr 1.5fr .95fr",            // CSS grid columns (default 78px 1fr 1fr 1fr)
 "col_colors": ["", "green", "orange"],       // default pill colour per column
 "rows": [{"head": "I", "cells": ["I was", "I was not|I wasn't"]}]}
```

A cell string `"a|b|c"` = pills a, b, c. Optional per-pill colour prefix:
`"green:Yes, I was."`. A cell can also be `{"text": "plain **rich** text"}`.
Keep one grid + one col_colors consistent within a table.

**cards** — grid of coloured use-cards (each = emoji + small caps label + lines):

```json
{"kind": "cards", "cols": 2,
 "cards": [{"color": "blue", "emoji": "👋", "title": "Introducing people",
            "lines": ["**I'm** Steven, and this **is** Isabella."]}]}
```

**pills** — label + pills rows (paradigm-like content):

```json
{"kind": "pills", "caps": "", "groups": [
  {"label": "I / You / We / They", "pills": "work|don't work|Do … work?"}]}
```

**note** — the callout (tips, common mistakes; ✓/✗ marks):

```json
{"kind": "note", "color": "yellow", "title": "Common mistakes",
 "lines": [{"mark": "✗", "text": "He **didn't was** at home."},
           {"mark": "✓", "text": "He **wasn't** at home."}]}
```

**list** — plain lines in a card: `{"kind": "list", "lines": ["…", "…"]}`

**illustration** — quadrants/matrix with big figures (rare; only for
scene/quadrant charts, keep the source's near-square scale):

```json
{"kind": "illustration",
 "cols": [{"emoji": "👈", "title": "here", "color": "red"},
          {"emoji": "👉", "title": "there", "color": "blue"}],
 "rows": [{"label": "singular",
           "cells": [{"figure": "🐵", "word": "this", "caption": "**This** is a monster.", "color": "red"}]}]}
```

**images** — raw `<img>` row (rare): `{"kind": "images", "srcs": ["file or url", ...]}`

Colours available: gray, green, red, blue, orange, purple, yellow, brown, pink.

## House rules

1. **English only**; no source names and no URLs inside the chart.
2. A chart is a real redesign of the teaching point, not a copy of the
   surrounding explanation text: title + structured blocks + highlights.
3. Reference designs ship in `examples/`: `be-form.spec.json` (form table +
   short answers + note), `there-vs-it.spec.json` (use cards + common
   mistakes), `this-that.spec.json` (illustration matrix).
4. Highlight the TARGET forms with `**…**` (green); that is what makes the
   chart readable. Errors go red `~~…~~`.
5. Content accuracy beats art fidelity. If a source chart is too
   graphic-heavy to transcribe, rebuild the same teaching point from the
   lesson text in the house style.
6. Keep charts light: for small content, no more than one note and two
   tables. Merge where sensible instead of stacking.
7. **Punctuation goes INSIDE the highlight chip**: `**It’s** fine`, not
   `**It**’s fine`. A chip that ends right before `, . :` renders a ~5px gap
   (chip padding) that reads as a space before the punctuation.
