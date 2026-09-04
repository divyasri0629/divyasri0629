#!/usr/bin/env python3
"""
Render data/contributions.json as an animated SVG contribution heatmap:
a 53-week x 7-day grid of rounded boxes that reveal diagonally on load,
plus a legend and a stats footer line.
"""
import json
import os
from collections import defaultdict
from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "contrib-heatmap.svg")

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 11
GAP = 3
STEP = CELL + GAP
LEFT_PAD = 28
TOP_PAD = 34
RIGHT_PAD = 16
BOTTOM_PAD = 46
MONTH_LABEL_ROW_H = 16

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_data():
    with open(DATA_PATH) as f:
        return json.load(f)


def bucket_by_week(days):
    """Arrange days into GitHub-style weekly columns starting on Sunday."""
    parsed = []
    for d in days:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        parsed.append((dt, d["level"], d["count"]))
    parsed.sort(key=lambda t: t[0])

    if not parsed:
        return []

    # Find the Sunday on/before the first date, so week columns align like GitHub.
    first_dt = parsed[0][0]
    offset = (first_dt.weekday() + 1) % 7  # Python Monday=0 -> shift so Sunday=0
    weeks = []
    current_week = [None] * offset
    for dt, level, count in parsed:
        current_week.append((dt, level, count))
        if len(current_week) == 7:
            weeks.append(current_week)
            current_week = []
    if current_week:
        while len(current_week) < 7:
            current_week.append(None)
        weeks.append(current_week)
    return weeks


def month_label_positions(weeks):
    labels = []
    last_month = None
    for week_idx, week in enumerate(weeks):
        for day in week:
            if day is None:
                continue
            dt = day[0]
            if dt.day <= 7 and dt.month != last_month:
                labels.append((week_idx, MONTH_ABBR[dt.month - 1]))
                last_month = dt.month
            break
    return labels


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def build_svg(data):
    days = data["days"]
    stats = data["stats"]
    username = data.get("username", "")

    weeks = bucket_by_week(days)
    n_weeks = len(weeks)

    width = LEFT_PAD + n_weeks * STEP + RIGHT_PAD
    height = TOP_PAD + 7 * STEP + BOTTOM_PAD

    rects = []
    total_cells = 0
    for week_idx, week in enumerate(weeks):
        for day_idx, day in enumerate(week):
            if day is None:
                continue
            dt, level, count = day
            level = max(0, min(level, len(PALETTE) - 1))
            color = PALETTE[level]
            x = LEFT_PAD + week_idx * STEP
            y = TOP_PAD + day_idx * STEP
            delay = (week_idx + day_idx) * 0.006
            title = f"{count} contribution{'s' if count != 1 else ''} on {dt.strftime('%b %-d, %Y') if hasattr(dt, 'strftime') else dt}"
            rects.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" ry="2.5" '
                f'fill="{color}" class="cell" style="animation-delay:{delay:.3f}s">'
                f'<title>{esc(title)}</title></rect>'
            )
            total_cells += 1

    month_labels = month_label_positions(weeks)
    month_texts = []
    for week_idx, label in month_labels:
        x = LEFT_PAD + week_idx * STEP
        month_texts.append(
            f'<text x="{x}" y="{TOP_PAD - 12}" class="month-label">{label}</text>'
        )

    legend_x = LEFT_PAD
    legend_y = height - 20
    legend_items = [f'<text x="{legend_x}" y="{legend_y + 9}" class="legend-text">Less</text>']
    lx = legend_x + 34
    for i, color in enumerate(PALETTE[:5]):
        legend_items.append(
            f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2.5" ry="2.5" fill="{color}" />'
        )
        lx += STEP
    legend_items.append(f'<text x="{lx + 6}" y="{legend_y + 9}" class="legend-text">More</text>')

    footer_text = (
        f"{stats['total_last_year']} contributions in the last year "
        f"&#183; current streak {stats['current_streak']}d "
        f"&#183; longest streak {stats['longest_streak']}d"
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" font-family="'Segoe UI', Helvetica, Arial, sans-serif">
  <style>
    .bg {{ fill: #0d1117; }}
    .month-label {{ fill: #8b949e; font-size: 10px; }}
    .legend-text {{ fill: #8b949e; font-size: 10px; }}
    .footer-text {{ fill: #8b949e; font-size: 11px; }}
    .cell {{
      opacity: 0;
      transform-box: fill-box;
      transform-origin: center;
      animation: reveal 0.35s ease-out forwards;
    }}
    @keyframes reveal {{
      0%   {{ opacity: 0; transform: translate(-6px, -6px) scale(0.4); }}
      100% {{ opacity: 1; transform: translate(0, 0) scale(1); }}
    }}
  </style>
  <rect class="bg" x="0" y="0" width="{width}" height="{height}" rx="6" ry="6" />
  {''.join(month_texts)}
  {''.join(rects)}
  {''.join(legend_items)}
  <text x="{width - RIGHT_PAD}" y="{legend_y + 9}" text-anchor="end" class="footer-text">{footer_text}</text>
</svg>'''
    return svg


def main():
    data = load_data()
    svg = build_svg(data)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"[render_heatmap_svg] Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
