#!/usr/bin/env python3
"""
Convert source-prepped.png (grayscale, white background) into a monochrome
ASCII-art SVG that "types" itself in: each row wipes left-to-right via a
clip-path animation, staggered top to bottom, with a small block cursor
riding the wipe edge. Prints once and freezes (no looping).
"""
import os

import numpy as np
from PIL import Image

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
IN_PATH = os.path.join(REPO_ROOT, "source-prepped.png")
OUT_PATH = os.path.join(REPO_ROOT, "avi-ascii.svg")

# bright (sparse) -> dark (dense); leading space clears background to nothing
RAMP = " .`:-=+*cs#%@"

# Target column count; row count is derived from the actual image aspect
# ratio (so portrait crops aren't squashed the way a fixed 100x53 grid
# assumes landscape source photos). NOTE: legibility is governed by the
# final DISPLAY width in the README (~370-490px), not by raw column count —
# going much above ~90-100 cols just makes each character smaller once
# scaled down, which reads as noisier rather than more detailed.
COLS = 92
MAX_ROWS = 110
FONT_SIZE = 8
CHAR_W = FONT_SIZE * 0.6
CHAR_H = FONT_SIZE * 1.0
FILL_COLOR = "#c9d1d9"
CURSOR_COLOR = "#39d353"


def compute_rows(img: Image.Image, cols: int) -> int:
    img_w, img_h = img.size
    aspect_ratio_correction = CHAR_W / CHAR_H
    rows = round(cols * (img_h / img_w) * aspect_ratio_correction)
    return max(10, min(rows, MAX_ROWS))


def image_to_ascii_grid(img: Image.Image, cols: int, rows: int):
    img = img.convert("L").resize((cols, rows), Image.LANCZOS)
    arr = np.array(img).astype(np.float32)
    # normalize brightness to full 0-255 range for consistent ramp mapping
    lo, hi = arr.min(), arr.max()
    if hi > lo:
        arr = (arr - lo) / (hi - lo) * 255.0

    ramp_len = len(RAMP)
    grid = []
    for row in arr:
        line = []
        for val in row:
            # val=255 (white/bright) -> ramp index 0 (space); val=0 (dark) -> last char
            idx = int((255 - val) / 255 * (ramp_len - 1))
            idx = max(0, min(idx, ramp_len - 1))
            line.append(RAMP[idx])
        grid.append(line)
    return grid


def esc(ch):
    if ch == "&":
        return "&amp;"
    if ch == "<":
        return "&lt;"
    if ch == ">":
        return "&gt;"
    if ch == " ":
        return " "
    return ch


def build_svg(grid):
    cols = len(grid[0])
    rows = len(grid)
    width = cols * CHAR_W
    height = rows * CHAR_H

    row_groups = []
    for r, row in enumerate(grid):
        text = "".join(esc(c) for c in row)
        y = (r + 1) * CHAR_H - 2
        delay = r * 0.045
        row_width = cols * CHAR_W
        cursor_x = row_width  # cursor ends at right edge once wipe completes

        row_groups.append(f'''
  <g class="ascii-row" style="animation-delay:{delay:.3f}s">
    <clipPath id="clip-row-{r}">
      <rect x="0" y="{r * CHAR_H}" width="0" height="{CHAR_H}" class="wipe" style="animation-delay:{delay:.3f}s" />
    </clipPath>
    <text x="0" y="{y}" xml:space="preserve" class="ascii-text" clip-path="url(#clip-row-{r})">{text}</text>
    <rect class="cursor" y="{r * CHAR_H}" width="{CHAR_W}" height="{CHAR_H}" style="animation-delay:{delay:.3f}s" />
  </g>''')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" width="{width:.1f}" height="{height:.1f}">
  <style>
    .ascii-text {{
      font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
      font-size: {FONT_SIZE}px;
      fill: {FILL_COLOR};
      white-space: pre;
    }}
    .wipe {{
      animation: wipeIn 0.5s steps(30) forwards;
    }}
    @keyframes wipeIn {{
      to {{ width: {cols * CHAR_W:.1f}px; }}
    }}
    .cursor {{
      fill: {CURSOR_COLOR};
      opacity: 0;
      animation: cursorRide 0.5s steps(30) forwards, cursorFade 0.15s ease-in forwards;
      animation-fill-mode: forwards;
    }}
    @keyframes cursorRide {{
      from {{ transform: translateX(0); opacity: 1; }}
      to   {{ transform: translateX({cols * CHAR_W:.1f}px); opacity: 1; }}
    }}
    @keyframes cursorFade {{
      to {{ opacity: 0; }}
    }}
  </style>
  <rect x="0" y="0" width="{width:.1f}" height="{height:.1f}" fill="#0d1117" />
  {''.join(row_groups)}
</svg>'''
    return svg


def main():
    if not os.path.exists(IN_PATH):
        print(f"[make_ascii_svg] {IN_PATH} not found. Run prep_photo.py first.")
        return 1

    img = Image.open(IN_PATH)
    rows = compute_rows(img, COLS)
    grid = image_to_ascii_grid(img, COLS, rows)
    svg = build_svg(grid)

    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"[make_ascii_svg] Wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
