#!/usr/bin/env python3
"""
Hand-authored neofetch-style info card: a title bar + colored key/value rows
that fade/slide in on a stagger. Set STATIC=1 to emit a frozen frame
(all rows fully visible, no animation) for local preview tools.
"""
import os

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "info-card.svg")
STATIC = os.environ.get("STATIC") == "1"

TITLE = "divyasri0629@github"

ROWS = [
    ("Now", "B.Tech IT @ Aditya Engineering College"),
    ("Prev", "Frontend Intern @ NUNC Systems"),
    ("Stack", "Python · Dart · Java · C"),
    ("Mobile", "Flutter · Dart · Firebase"),
    ("ML/AI", "Python · scikit-learn · AI/ML"),
    ("Focus", "Software Engineering / AI/ML"),
    ("CGPA", "9.09 / 10.0"),
]

WIDTH = 490
LINE_H = 26
TOP_BAR_H = 34
PADDING_TOP = 20
PADDING_LEFT = 22
HEIGHT = TOP_BAR_H + PADDING_TOP + len(ROWS) * LINE_H + 20

KEY_COLOR = "#39d353"
VAL_COLOR = "#c9d1d9"
BG = "#0d1117"
BAR_BG = "#161b22"
BORDER = "#30363d"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg():
    rows_svg = []
    for i, (key, val) in enumerate(ROWS):
        y = TOP_BAR_H + PADDING_TOP + i * LINE_H
        delay = i * 0.18
        anim = "" if STATIC else f' style="animation-delay:{delay:.2f}s"'
        cls = "" if STATIC else ' class="line"'
        rows_svg.append(
            f'<g{cls}{anim}>'
            f'<text x="{PADDING_LEFT}" y="{y}" class="key">{esc(key)}</text>'
            f'<text x="{PADDING_LEFT + 78}" y="{y}" class="val">{esc(val)}</text>'
            f'</g>'
        )

    animation_css = "" if STATIC else '''
    .line {
      opacity: 0;
      transform: translateX(-8px);
      animation: lineIn 0.4s ease-out forwards;
    }
    @keyframes lineIn {
      to { opacity: 1; transform: translateX(0); }
    }'''

    static_override = '' if not STATIC else '\n    .line { opacity: 1; }'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" font-family="'Cascadia Code', 'Fira Code', Consolas, monospace">
  <style>
    .bg {{ fill: {BG}; stroke: {BORDER}; stroke-width: 1; }}
    .bar {{ fill: {BAR_BG}; }}
    .dot {{ opacity: 0.9; }}
    .title-text {{ fill: #8b949e; font-size: 12px; }}
    .key {{ fill: {KEY_COLOR}; font-size: 13px; font-weight: 600; }}
    .val {{ fill: {VAL_COLOR}; font-size: 13px; }}{animation_css}{static_override}
  </style>
  <rect class="bg" x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="8" ry="8" />
  <path class="bar" d="M1,8 a7,7 0 0 1 7,-7 h{WIDTH - 16} a7,7 0 0 1 7,7 v{TOP_BAR_H - 8} h-{WIDTH - 2} z" />
  <circle class="dot" cx="20" cy="17" r="5" fill="#ff5f56" />
  <circle class="dot" cx="38" cy="17" r="5" fill="#ffbd2e" />
  <circle class="dot" cx="56" cy="17" r="5" fill="#27c93f" />
  <text x="{WIDTH / 2}" y="21" text-anchor="middle" class="title-text">{esc(TITLE)}</text>
  {''.join(rows_svg)}
</svg>'''
    return svg


def main():
    svg = build_svg()
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"[make_info_card] Wrote {OUT_PATH} (STATIC={STATIC})")


if __name__ == "__main__":
    main()
