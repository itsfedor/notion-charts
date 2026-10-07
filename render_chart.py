"""Render Notion-style chart HTML files to transparent PNGs at 2x.
Usage: python3 render_chart.py chart-form.html out-form.png [--width 880]
Checks: fonts loaded, no horizontal overflow, element inventory printed.
"""
import sys, json, os
from playwright.sync_api import sync_playwright


def render(html_path, out_png, width):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(viewport={"width": width, "height": 900},
                        device_scale_factor=2)
        pg.goto("file://" + os.path.abspath(html_path), wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(1200)
        try:
            pg.evaluate("document.fonts.ready")
        except Exception:
            pass
        pg.wait_for_timeout(800)
        qa = pg.evaluate(r"""() => {
          const root = document.querySelector('.chart');
          const fonts = document.fonts ? [...document.fonts].map(f => f.family + ' ' + f.weight + ' ' + f.status) : [];
          const overflow = [];
          document.querySelectorAll('.chart *').forEach(el => {
            if (el.scrollWidth > el.clientWidth + 2 && el.clientWidth > 0)
              overflow.push(((el.className||'').toString().slice(0, 40)) + ' ' + el.scrollWidth + '>' + el.clientWidth);
          });
          const count = (sel) => document.querySelectorAll(sel).length;
          return {
            rootW: root ? Math.round(root.getBoundingClientRect().width) : null,
            rootH: root ? Math.round(root.getBoundingClientRect().height) : null,
            fonts: [...new Set(fonts)],
            overflow: overflow.slice(0, 10),
            greens: count('.hl-green'), reds: count('.hl-red'), rows: count('.row, .case'),
            bodyFont: root ? getComputedStyle(root).fontFamily : null,
            text: (document.body.innerText || '').slice(0, 120).replace(/\n/g, ' | ')
          };
        }""")
        el = pg.query_selector(".chart")
        el.screenshot(path=out_png, omit_background=True)
        b.close()
        return qa


if __name__ == "__main__":
    html = sys.argv[1]
    out = sys.argv[2]
    width = 880
    if "--width" in sys.argv:
        width = int(sys.argv[sys.argv.index("--width") + 1])
    qa = render(html, out, width)
    print(json.dumps(qa, ensure_ascii=False, indent=1))
