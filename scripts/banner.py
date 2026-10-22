"""Animated header banner, one SVG per theme.

Run: python scripts/banner.py  (needs fonttools and brotli)
Output: assets/banner-dark.svg, assets/banner-light.svg
"""

from __future__ import annotations

from pathlib import Path

from svgkit import THEMES, esc, font_face, icon_color, icon_svg, mulberry32, text_width, write

OUT = Path(__file__).resolve().parent.parent / "assets"

W, H = 1200, 300
X0 = 72

HELLO = "Hello, I'm"
FIRST, LAST = "Khoirul", "Anam"
ROLE = "Mobile Developer for Android and iOS"
PHRASES = [
    "Software Developer at PT Petrokimia Gresik",
    "Shipping Flutter apps to Google Play and the App Store",
    "Computer Science, Universitas Gadjah Mada",
]
CHIPS = [("flutter", "Flutter", 812, 64), ("kotlin", "Kotlin", 1062, 118), ("googlegemini", "Gemini", 822, 210)]

MONO = 17
TYPE_Y = 252
TYPE_STEP, DELETE_STEP, HOLD, GAP = 0.05, 0.02, 2.4, 0.5


def typing_timeline() -> tuple[float, list[list[tuple[float, int]]]]:
    """Per phrase, a list of (time, visible chars) events. Returns total duration too."""
    t = 0.4
    timelines = []
    for phrase in PHRASES:
        events = [(0.0, 0)]
        for n in range(1, len(phrase) + 1):
            events.append((t, n))
            t += TYPE_STEP
        t += HOLD
        for n in range(len(phrase) - 1, -1, -1):
            events.append((t, n))
            t += DELETE_STEP
        t += GAP
        timelines.append(events)
    return t, timelines


def discrete(attr: str, total: float, events: list[tuple[float, float]]) -> str:
    times = ";".join(f"{e[0] / total:.4f}" for e in events)
    values = ";".join(f"{e[1]:.1f}" for e in events)
    return (
        f'<animate attributeName="{attr}" dur="{total:.2f}s" repeatCount="indefinite" '
        f'calcMode="discrete" keyTimes="{times}" values="{values}"/>'
    )


def typing(theme: dict) -> str:
    cw = text_width("M", MONO, "mono", 500)
    start = X0 + 2 * cw
    total, timelines = typing_timeline()
    parts = [f'<text x="{X0}" y="{TYPE_Y}" class="mono" fill="{theme["accent"]}">&gt;</text>']
    cursor_events: list[tuple[float, float]] = []
    for i, (phrase, events) in enumerate(zip(PHRASES, timelines)):
        widths = [(t, n * cw) for t, n in events]
        # Renderers without SMIL (the GitHub mobile app) ignore the clip and the
        # animation, so the static state shows the first phrase only.
        shown = [(0.0, 0), (events[1][0], 1), (events[-1][0], 0)]
        parts.append(
            f'<clipPath id="type{i}"><rect x="{start:.1f}" y="{TYPE_Y - 16}" height="22" width="{len(phrase) * cw if i == 0 else 0:.1f}">'
            + discrete("width", total, widths)
            + "</rect></clipPath>"
            f'<text x="{start:.1f}" y="{TYPE_Y}" class="mono" fill="{theme["fg"]}" '
            f'fill-opacity="0.85" opacity="{1 if i == 0 else 0}" clip-path="url(#type{i})">{esc(phrase)}'
            + discrete("opacity", total, shown)
            + "</text>"
        )
        cursor_events += [(t, start + w + 2) for t, w in widths[1:]]
    cursor_events = [(0.0, start + 2)] + sorted(cursor_events)
    parts.append(
        f'<rect class="blink" x="{start + len(PHRASES[0]) * cw + 2:.1f}" y="{TYPE_Y - 14}" width="9" height="18" rx="1.5" '
        f'fill="{theme["primary"]}">' + discrete("x", total, cursor_events) + "</rect>"
    )
    return "".join(parts)


def stars(theme_name: str, theme: dict) -> str:
    rand = mulberry32(1604)
    out = []
    if theme_name == "dark":
        for _ in range(80):
            x, y = rand() * W, rand() * H
            r = rand() * 1.2 + 0.5
            dur, delay = rand() * 3 + 2, rand() * 5
            out.append(
                f'<circle class="tw" cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="#FFFFFF" '
                f'style="animation-duration:{dur:.2f}s;animation-delay:-{delay:.2f}s"/>'
            )
    else:
        for _ in range(16):
            x, y = rand() * W, rand() * H
            s = rand() * 4 + 3
            dur, delay = rand() * 3 + 3, rand() * 5
            d = f"M{x:.1f} {y - s:.1f}Q{x:.1f} {y:.1f} {x + s:.1f} {y:.1f}Q{x:.1f} {y:.1f} {x:.1f} {y + s:.1f}Q{x:.1f} {y:.1f} {x - s:.1f} {y:.1f}Q{x:.1f} {y:.1f} {x:.1f} {y - s:.1f}Z"
            out.append(
                f'<path class="tw" d="{d}" fill="{theme["primary"]}" fill-opacity="0.45" '
                f'style="animation-duration:{dur:.2f}s;animation-delay:-{delay:.2f}s"/>'
            )
    return "".join(out)


def shooting_stars(theme_name: str, theme: dict) -> str:
    color = "#FFFFFF" if theme_name == "dark" else theme["primary"]
    out = [
        f'<linearGradient id="tail" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="90" y2="-90">'
        f'<stop offset="0" stop-color="{color}" stop-opacity="0.95"/>'
        f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient>'
    ]
    for x, y, delay in ((1040, 10, 1.5), (560, -30, 7.0)):
        out.append(
            f'<g transform="translate({x} {y})"><g class="shoot" style="animation-delay:{delay}s">'
            f'<line x1="0" y1="0" x2="90" y2="-90" stroke="url(#tail)" stroke-width="1.6" stroke-linecap="round"/>'
            f'<circle r="1.8" fill="{color}"/></g></g>'
        )
    return "".join(out)


def nebula(theme_name: str, theme: dict) -> str:
    if theme_name == "dark":
        blobs = [(160, 80, 300, 150, theme["primary"], 0.30), (1010, 190, 320, 170, theme["secondary"], 0.26), (640, 310, 260, 90, theme["accent"], 0.12)]
    else:
        blobs = [(170, 70, 280, 150, theme["primary"], 0.16), (1000, 200, 320, 170, theme["secondary"], 0.14), (640, 300, 260, 90, theme["accent"], 0.10)]
    out = []
    for i, (cx, cy, rx, ry, color, alpha) in enumerate(blobs):
        out.append(
            f'<radialGradient id="neb{i}"><stop offset="0" stop-color="{color}" stop-opacity="{alpha}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></radialGradient>'
            f'<ellipse class="drift" style="animation-delay:-{i * 5}s" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#neb{i})"/>'
        )
    return "".join(out)


def phone(theme_name: str, theme: dict) -> str:
    cx = 985
    x, y, w, h = cx - 62, 34, 124, 232
    dark = theme_name == "dark"
    frame = "#0B1222" if dark else "#FFFFFF"
    frame_stroke = "#334155" if dark else "#CBD5E1"
    screen = "#020617" if dark else "#F8FAFC"
    line = theme["muted"]
    rows = []
    for i, color in enumerate((theme["primary"], theme["secondary"], theme["accent"])):
        ry = y + 98 + i * 26
        rows.append(
            f'<rect x="{x + 18}" y="{ry}" width="18" height="18" rx="5" fill="{color}" fill-opacity="0.3"/>'
            f'<rect x="{x + 44}" y="{ry + 3}" width="{52 - i * 8}" height="5" rx="2.5" fill="{line}" fill-opacity="0.55"/>'
            f'<rect x="{x + 44}" y="{ry + 11}" width="{34 + i * 6}" height="4" rx="2" fill="{line}" fill-opacity="0.3"/>'
        )
    bars = []
    for i, (bh, color) in enumerate(((18, theme["primary"]), (28, theme["secondary"]), (14, theme["primary"]), (32, theme["accent"]), (24, theme["secondary"]))):
        bx = x + 22 + i * 17
        bars.append(
            f'<rect class="bar" style="animation-delay:{i * 0.25}s" x="{bx}" y="{y + 206 - bh}" '
            f'width="10" height="{bh}" rx="3" fill="{color}" fill-opacity="0.75"/>'
        )
    orbit = "M -175 0 A 175 52 0 1 1 175 0 A 175 52 0 1 1 -175 0"
    return (
        f'<radialGradient id="halo"><stop offset="0" stop-color="{theme["primary"]}" stop-opacity="{0.35 if dark else 0.18}"/>'
        f'<stop offset="1" stop-color="{theme["primary"]}" stop-opacity="0"/></radialGradient>'
        f'<circle cx="{cx}" cy="150" r="150" fill="url(#halo)"/>'
        f'<g transform="translate({cx} 150) rotate(-14)">'
        f'<path d="{orbit}" fill="none" stroke="{theme["primary"]}" stroke-opacity="0.4" stroke-dasharray="2 7"/>'
        f'<circle r="4.5" fill="{theme["accent"]}"><animateMotion dur="11s" repeatCount="indefinite" path="{orbit}"/></circle>'
        f'<circle r="3.5" fill="{theme["secondary"]}"><animateMotion dur="17s" begin="-6s" repeatCount="indefinite" path="{orbit}"/></circle>'
        "</g>"
        '<g class="float">'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="24" fill="{frame}" stroke="{frame_stroke}" stroke-width="2"/>'
        f'<rect x="{x + 7}" y="{y + 7}" width="{w - 14}" height="{h - 14}" rx="18" fill="{screen}"/>'
        f'<rect x="{cx - 18}" y="{y + 14}" width="36" height="9" rx="4.5" fill="{"#000000" if dark else "#0F172A"}"/>'
        f'<linearGradient id="card" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{theme["primary"]}"/>'
        f'<stop offset="1" stop-color="{theme["secondary"]}"/></linearGradient>'
        f'<rect x="{x + 16}" y="{y + 34}" width="{w - 32}" height="54" rx="12" fill="url(#card)"/>'
        f'<rect x="{x + 26}" y="{y + 48}" width="44" height="6" rx="3" fill="#FFFFFF" fill-opacity="0.9"/>'
        f'<rect x="{x + 26}" y="{y + 60}" width="58" height="5" rx="2.5" fill="#FFFFFF" fill-opacity="0.6"/>'
        f'<rect x="{x + 26}" y="{y + 71}" width="30" height="5" rx="2.5" fill="#FFFFFF" fill-opacity="0.45"/>'
        + "".join(rows)
        + "".join(bars)
        + f'<rect x="{cx - 20}" y="{y + h - 15}" width="40" height="4" rx="2" fill="{line}" fill-opacity="0.5"/>'
        "</g>"
    )


def chips(theme_name: str, theme: dict) -> str:
    out = []
    for i, (slug, label, x, y) in enumerate(CHIPS):
        tw = text_width(label, 13, "sans", 600)
        w = 11 + 14 + 7 + tw + 13
        out.append(
            f'<g class="float" style="animation-delay:-{i * 2}s;animation-duration:{5 + i}s">'
            f'<rect x="{x}" y="{y}" width="{w:.1f}" height="30" rx="15" fill="{theme["card"]}" '
            f'fill-opacity="{0.9 if theme_name == "dark" else 0.95}" stroke="{theme["border"]}"/>'
            + icon_svg(slug, x + 11, y + 8, 14, icon_color(slug, theme_name))
            + f'<text x="{x + 32}" y="{y + 19.5}" class="chip" fill="{theme["fg"]}">{esc(label)}</text></g>'
        )
    return "".join(out)


def build(theme_name: str) -> str:
    theme = THEMES[theme_name]
    sans_text = HELLO + FIRST + LAST + ROLE + "".join(c[1] for c in CHIPS)
    mono_text = ">" + "".join(PHRASES)
    first_w = text_width(FIRST + " ", 60, "sans", 700)
    full_w = text_width(f"{FIRST} {LAST}", 60, "sans", 700)
    css = (
        font_face("sans", "O", sans_text)
        + font_face("mono", "M", mono_text)
        + ".sans{font-family:O,system-ui,sans-serif}"
        + ".mono{font-family:M,ui-monospace,monospace;font-size:17px;font-weight:500}"
        + ".chip{font-family:O,system-ui,sans-serif;font-size:13px;font-weight:600}"
        + ".tw{animation:tw 3s ease-in-out infinite}"
        + "@keyframes tw{0%,100%{opacity:.2}50%{opacity:1}}"
        + ".shoot{opacity:0;animation:shoot 10s linear infinite}"
        + "@keyframes shoot{0%{transform:translate(0,0);opacity:0}1%{opacity:1}"
        + "13%{transform:translate(-380px,380px);opacity:0}100%{transform:translate(-380px,380px);opacity:0}}"
        + ".drift{animation:drift 16s ease-in-out infinite alternate}"
        + "@keyframes drift{from{transform:translate(-18px,10px)}to{transform:translate(18px,-10px)}}"
        + ".float{animation:float 6s ease-in-out infinite}"
        + "@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}"
        + ".bar{transform-box:fill-box;transform-origin:50% 100%;animation:bar 3s ease-in-out infinite}"
        + "@keyframes bar{0%,100%{transform:scaleY(1)}50%{transform:scaleY(.6)}}"
        + ".blink{animation:blink 1s steps(1) infinite}"
        + "@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}"
        + ".fade{animation:fade .9s ease-out both}"
        + "@keyframes fade{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}"
        + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    )
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
<title id="title">Khoirul Anam, {ROLE}</title>
<desc id="desc">{esc(". ".join(PHRASES))}.</desc>
<style>{css}</style>
<defs>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="24"/></clipPath>
<linearGradient id="name" gradientUnits="userSpaceOnUse" x1="{X0 + first_w:.1f}" y1="0" x2="{X0 + full_w:.1f}" y2="0">
<stop offset="0" stop-color="{theme["primary"]}"/><stop offset="1" stop-color="{theme["secondary"]}"/></linearGradient>
</defs>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="{theme["bg"]}"/>
{nebula(theme_name, theme)}
{stars(theme_name, theme)}
{shooting_stars(theme_name, theme)}
{phone(theme_name, theme)}
{chips(theme_name, theme)}
<g class="fade">
<text x="{X0}" y="92" class="sans" font-size="20" font-weight="500" fill="{theme["primary"]}">{esc(HELLO)}</text>
<text x="{X0}" y="158" class="sans" font-size="60" font-weight="700" fill="{theme["fg"]}">{FIRST}</text>
<text x="{X0 + first_w:.1f}" y="158" class="sans" font-size="60" font-weight="700" fill="url(#name)">{LAST}</text>
<text x="{X0}" y="202" class="sans" font-size="24" font-weight="500" fill="{theme["fg"]}" fill-opacity="0.9">{esc(ROLE)}</text>
</g>
{typing(theme)}
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="23.5" fill="none" stroke="{theme["border"]}"/>
</svg>
"""


if __name__ == "__main__":
    for name in THEMES:
        write(OUT / f"banner-{name}.svg", build(name))
