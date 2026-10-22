"""GitHub activity and language cards, rebuilt daily by .github/workflows/stats.yml.

Run: STATS_TOKEN=... python scripts/stats.py [out_dir]  (needs fonttools and brotli)
Output: activity-<theme>.svg and languages-<theme>.svg in out_dir (default dist/).
The language card needs STATS_TOKEN and is skipped without it.

The cards show totals only. Private repositories count toward the numbers and
the language mix, but their names never appear in the output.
"""

from __future__ import annotations

import json
import math
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from svgkit import THEMES, esc, font_face, mix, text_width, write

LOGIN = "khrlanamm"

# Repositories left out of the language mix: writing (thesis text, CV) and a
# thesis manuscript written for someone else.
SKIP_REPOS = {"skripsi-bayu", "skripsi-naskah", "cv"}
# Generated or platform glue code that would distort the mix: notebooks store
# outputs inline, and Flutter projects carry native runner code for every platform.
SKIP_LANGUAGES = {"Jupyter Notebook", "CMake", "C++", "C", "Swift", "Objective-C", "Ruby", "Batchfile", "Makefile", "Dockerfile", "Shell", "PowerShell"}
TOP_LANGUAGES = 7

W, H = 440, 228


def graphql(query: str, variables: dict) -> dict:
    token = os.environ.get("STATS_TOKEN") or os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.load(resp)
    if body.get("errors"):
        raise RuntimeError(body["errors"])
    return body["data"]


CALENDAR = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    createdAt
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
  }
}
"""

REPOS = """
query($login: String!, $after: String) {
  user(login: $login) {
    repositories(first: 100, after: $after, ownerAffiliations: OWNER, isFork: false) {
      pageInfo { hasNextPage endCursor }
      nodes { name languages(first: 25) { edges { size node { name color } } } }
    }
  }
}
"""


def fetch_days() -> tuple[dict[str, int], int]:
    """Contribution count per day since the account was created, plus the last-year total."""
    now = datetime.now(timezone.utc)
    last_year = graphql(CALENDAR, {"login": LOGIN, "from": (now - timedelta(days=365)).isoformat(), "to": now.isoformat()})
    user = last_year["user"]
    recent_total = user["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    created = datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
    days: dict[str, int] = {}
    for year in range(created.year, now.year + 1):
        start = max(created, datetime(year, 1, 1, tzinfo=timezone.utc))
        end = min(now, datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc))
        data = graphql(CALENDAR, {"login": LOGIN, "from": start.isoformat(), "to": end.isoformat()})
        for week in data["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for day in week["contributionDays"]:
                days[day["date"]] = day["contributionCount"]
    return days, recent_total


def fetch_languages() -> list[tuple[str, int, str]]:
    sizes: dict[str, int] = {}
    colors: dict[str, str] = {}
    after = None
    while True:
        repos = graphql(REPOS, {"login": LOGIN, "after": after})["user"]["repositories"]
        for repo in repos["nodes"]:
            if repo["name"] in SKIP_REPOS:
                continue
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                if name in SKIP_LANGUAGES:
                    continue
                sizes[name] = sizes.get(name, 0) + edge["size"]
                colors[name] = edge["node"]["color"] or "#94A3B8"
        if not repos["pageInfo"]["hasNextPage"]:
            break
        after = repos["pageInfo"]["endCursor"]
    ranked = sorted(sizes.items(), key=lambda kv: kv[1], reverse=True)
    return [(name, size, colors[name]) for name, size in ranked]


def streaks(days: dict[str, int]) -> tuple[int, int]:
    today = date.today()
    current = 0
    day = today if days.get(today.isoformat(), 0) else today - timedelta(days=1)
    while days.get(day.isoformat(), 0) > 0:
        current += 1
        day -= timedelta(days=1)
    longest = run = 0
    for key in sorted(days):
        run = run + 1 if days[key] > 0 else 0
        longest = max(longest, run)
    return current, longest


def weekly(days: dict[str, int]) -> list[int]:
    end = date.today()
    totals = []
    for w in range(52, 0, -1):
        start = end - timedelta(days=w * 7 - 1)
        totals.append(sum(days.get((start + timedelta(days=i)).isoformat(), 0) for i in range(7)))
    return totals


def smooth_path(points: list[tuple[float, float]]) -> str:
    """Catmull-Rom spline through the points, as cubic Bezier segments."""
    d = f"M{points[0][0]:.1f} {points[0][1]:.1f}"
    for i in range(len(points) - 1):
        p0 = points[max(i - 1, 0)]
        p1, p2 = points[i], points[i + 1]
        p3 = points[min(i + 2, len(points) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d


def fmt(n: int) -> str:
    return f"{n:,}"


BASE_CSS = (
    "text{font-family:O,system-ui,sans-serif}"
    ".title{font-size:15px;font-weight:600}"
    ".sub{font-size:12px;font-weight:400}"
    ".big{font-size:36px;font-weight:700}"
    ".num{font-size:19px;font-weight:600}"
    ".lbl{font-size:12px;font-weight:400}"
    ".fade{animation:fade .8s ease-out both}"
    "@keyframes fade{from{opacity:0}to{opacity:1}}"
    "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
)


def card(theme: dict, title: str, sub: str, body: str, css: str, text: str, label: str) -> str:
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title">
<title id="title">{esc(label)}</title>
<style>{font_face("sans", "O", text + title + sub)}{BASE_CSS}{css}</style>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="20" fill="{theme["bg"]}" stroke="{theme["border"]}"/>
<text x="24" y="38" class="title" fill="{theme["fg"]}">{esc(title)}</text>
<text x="{W - 24}" y="38" class="sub" fill="{theme["muted"]}" text-anchor="end">{esc(sub)}</text>
{body}
</svg>
"""


def activity_card(theme_name: str, days: dict[str, int], recent: int) -> str:
    theme = THEMES[theme_name]
    current, longest = streaks(days)
    all_time = sum(days.values())
    weeks = weekly(days)
    top = max(weeks) or 1
    x0, x1, y0, y1 = 24, W - 24, 104, 156
    pts = [(x0 + (x1 - x0) * i / (len(weeks) - 1), y1 - (y1 - y0) * v / top) for i, v in enumerate(weeks)]
    line = smooth_path(pts)
    area = line + f"L{x1} {y1}L{x0} {y1}Z"
    length = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)) * 1.15
    stats = [(fmt(all_time), "all time"), (f"{current} days", "current streak"), (f"{longest} days", "longest streak")]
    cols = "".join(
        f'<text x="{24 + i * 136}" y="192" class="num" fill="{theme["fg"]}">{esc(v)}</text>'
        f'<text x="{24 + i * 136}" y="211" class="lbl" fill="{theme["muted"]}">{esc(k)}</text>'
        for i, (v, k) in enumerate(stats)
    )
    big = fmt(recent)
    big_w = text_width(big, 36, "sans", 700)
    body = (
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{theme["primary"]}"/>'
        f'<stop offset="1" stop-color="{theme["secondary"]}"/></linearGradient>'
        f'<linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{theme["primary"]}" stop-opacity="0.35"/>'
        f'<stop offset="1" stop-color="{theme["primary"]}" stop-opacity="0"/></linearGradient></defs>'
        f'<text x="24" y="82" class="big" fill="url(#g)">{big}</text>'
        f'<text x="{24 + big_w + 10:.1f}" y="82" class="lbl" fill="{theme["muted"]}">contributions in the last year</text>'
        f'<line x1="{x0}" y1="{y1 + 0.5}" x2="{x1}" y2="{y1 + 0.5}" stroke="{theme["border"]}"/>'
        f'<path class="fade" d="{area}" fill="url(#a)" style="animation-delay:.6s"/>'
        f'<path class="draw" d="{line}" fill="none" stroke="url(#g)" stroke-width="2.2" stroke-linecap="round" '
        f'stroke-dasharray="{length:.0f}" stroke-dashoffset="0"/>'
        + cols
    )
    css = (
        # The line is drawn by default and only hidden while the animation runs,
        # so renderers without CSS animation still show it.
        f".draw{{animation:draw 2s ease-out .2s both}}"
        f"@keyframes draw{{from{{stroke-dashoffset:{length:.0f}}}to{{stroke-dashoffset:0}}}}"
    )
    text = big + "contributions in the last year" + "".join(v + k for v, k in stats) + "0123456789,"
    updated = date.today().strftime("%-d %b %Y")
    label = f"{recent} contributions in the last year, {all_time} all time, current streak {current} days, longest streak {longest} days"
    return card(theme, "Contributions", f"weekly, updated {updated}", body, css, text, label)


def languages_card(theme_name: str, langs: list[tuple[str, int, str]]) -> str:
    theme = THEMES[theme_name]
    total = sum(size for _, size, _ in langs) or 1
    # Eight legend slots: the top seven plus "Other", or the top eight when the
    # remainder would round to nothing.
    rest = sum(size for _, size, _ in langs[TOP_LANGUAGES:])
    if rest / total < 0.005:
        items = list(langs[: TOP_LANGUAGES + 1])
    else:
        items = list(langs[:TOP_LANGUAGES]) + [("Other", rest, theme["muted"])]
    items = [item for item in items if item[1] / total >= 0.001]
    x, bar_w = 24.0, W - 48
    segments = []
    for i, (name, size, color) in enumerate(items):
        w = bar_w * size / total
        segments.append(
            f'<rect class="grow" style="animation-delay:{0.15 + i * 0.08:.2f}s" x="{x:.2f}" y="58" '
            f'width="{max(w - 2, 1):.2f}" height="10" fill="{color}"/>'
        )
        x += w
    legend = []
    for i, (name, size, color) in enumerate(items):
        col, row = i % 2, i // 2
        lx, ly = 24 + col * 204, 104 + row * 32
        dot = color if theme_name == "light" else mix(color, "#FFFFFF", 0.1)
        legend.append(
            f'<g class="fade" style="animation-delay:{0.3 + i * 0.06:.2f}s">'
            f'<circle cx="{lx + 5}" cy="{ly - 5}" r="5" fill="{dot}"/>'
            f'<text x="{lx + 18}" y="{ly}" class="name" fill="{theme["fg"]}">{esc(name)}</text>'
            f'<text x="{lx + 190}" y="{ly}" class="pct" fill="{theme["muted"]}" text-anchor="end">{100 * size / total:.1f}%</text></g>'
        )
    body = (
        f'<clipPath id="bar"><rect x="24" y="58" width="{bar_w}" height="10" rx="5"/></clipPath>'
        f'<rect x="24" y="58" width="{bar_w}" height="10" rx="5" fill="{theme["track"]}"/>'
        f'<g clip-path="url(#bar)">{"".join(segments)}</g>' + "".join(legend)
    )
    css = (
        ".name{font-size:14px;font-weight:500}.pct{font-size:13px;font-weight:400}"
        ".grow{transform-box:fill-box;transform-origin:0 50%;animation:grow .7s ease-out both}"
        "@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
    )
    text = "".join(name for name, _, _ in items) + "0123456789.%"
    label = "Languages by code size: " + ", ".join(f"{n} {100 * s / total:.1f}%" for n, s, _ in items)
    return card(theme, "Languages", "by code size, all repositories", body, css, text, label)


def main() -> None:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    days, recent = fetch_days()
    for name in THEMES:
        write(out / f"activity-{name}.svg", activity_card(name, days, recent))
    # Private repositories are only visible with STATS_TOKEN. Without it the
    # workflow keeps the last language card instead of a public-only one.
    if not os.environ.get("STATS_TOKEN"):
        print("STATS_TOKEN not set, skipping the language card")
        return
    langs = fetch_languages()
    for name in THEMES:
        write(out / f"languages-{name}.svg", languages_card(name, langs))


if __name__ == "__main__":
    main()
