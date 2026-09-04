#!/usr/bin/env python3
"""
Fetch a GitHub user's public contribution calendar with no token/API needed.
GitHub serves the calendar as an HTML fragment at:
    https://github.com/users/<username>/contributions
This is the same markup the profile page itself embeds.
"""
import json
import os
import sys
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USERNAME", "divyasri0629")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")


def fetch_html(username: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (profile-readme-bot)"}
    resp = requests.get(URL, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.text


import re

_COUNT_RE = re.compile(r"^(No|\d+)\s+contributions?\s+on\s", re.IGNORECASE)


def _count_from_tooltip_text(text: str):
    """Parse '3 contributions on September 7th.' / 'No contributions on Aug 31st.'"""
    text = text.strip()
    m = _COUNT_RE.match(text)
    if not m:
        return None
    token = m.group(1)
    if token.lower() == "no":
        return 0
    try:
        return int(token)
    except ValueError:
        return None


def parse_days(html: str):
    soup = BeautifulSoup(html, "html.parser")
    days = []

    # Current GitHub markup: each day is a <td class="ContributionCalendar-day">
    # with data-date/data-level but NO count attribute. The actual count lives
    # in a sibling <tool-tip for="...">N contributions on <date>.</tool-tip>.
    tooltip_by_id = {}
    for tip in soup.select("tool-tip[for]"):
        tooltip_by_id[tip.get("for")] = tip.get_text()

    cells = soup.select("td.ContributionCalendar-day, td[data-date]")
    if not cells:
        cells = soup.select("rect.ContributionCalendar-day, rect[data-date]")

    for cell in cells:
        date_str = cell.get("data-date")
        if not date_str:
            continue
        level = cell.get("data-level")
        if level is None:
            classes = cell.get("class", [])
            level = next(
                (c.split("-")[-1] for c in classes if c.startswith("day-")), "0"
            )
        try:
            level = int(level)
        except (TypeError, ValueError):
            level = 0

        count = None
        cell_id = cell.get("id")
        if cell_id and cell_id in tooltip_by_id:
            count = _count_from_tooltip_text(tooltip_by_id[cell_id])
        if count is None:
            # fall back to any data-count attribute if a future markup adds one
            count_attr = cell.get("data-count")
            count = int(count_attr) if count_attr and count_attr.isdigit() else 0

        days.append({"date": date_str, "level": level, "count": count})

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days):
    total = sum(d["count"] or 0 for d in days)

    # current streak: consecutive days with count > 0, ending today/yesterday
    current_streak = 0
    for d in reversed(days):
        if (d["count"] or 0) > 0:
            current_streak += 1
        else:
            break

    # longest streak
    longest_streak = 0
    running = 0
    for d in days:
        if (d["count"] or 0) > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    best_day = max(days, key=lambda d: d["count"] or 0, default=None)

    # monthly totals for the last 12 months
    monthly = {}
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly[month_key] = monthly.get(month_key, 0) + (d["count"] or 0)

    return {
        "total_last_year": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly": monthly,
    }


def main():
    try:
        html = fetch_html(USERNAME)
        days = parse_days(html)
        if not days:
            raise ValueError("No contribution cells parsed — GitHub markup may differ.")
    except Exception as exc:
        print(f"[fetch_contributions] Failed to fetch/parse live data: {exc}", file=sys.stderr)
        # Fail soft: keep any existing data file rather than crash the workflow.
        if os.path.exists(OUT_PATH):
            print("[fetch_contributions] Keeping previous data/contributions.json", file=sys.stderr)
            sys.exit(0)
        else:
            sys.exit(1)

    stats = compute_stats(days)
    payload = {
        "username": USERNAME,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[fetch_contributions] Wrote {len(days)} days -> {OUT_PATH}")
    print(f"[fetch_contributions] Total: {stats['total_last_year']}, "
          f"current streak: {stats['current_streak']}, "
          f"longest streak: {stats['longest_streak']}")


if __name__ == "__main__":
    main()
