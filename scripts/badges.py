"""Link badges under the banner, one small SVG per link and theme.

Run: python scripts/badges.py  (needs fonttools and brotli)
Output: assets/badges/<name>-<theme>.svg
"""

from __future__ import annotations

from pathlib import Path

from svgkit import THEMES, esc, font_face, icon_svg, text_width, write

OUT = Path(__file__).resolve().parent.parent / "assets" / "badges"

# name, label, icon, filled
BADGES = [
    ("portfolio", "anamcode.space", "lucide-globe", True),
    ("cv", "CV", "lucide-file-text", False),
    ("linkedin", "LinkedIn", "linkedin-in", False),
    ("email", "Email", "lucide-mail", False),
    ("medium", "Medium", "medium", False),
    ("googleplay", "Google Play", "googleplay", False),
]

H = 34
SIZE = 14


def build(theme_name: str, label: str, icon_name: str, filled: bool) -> str:
    theme = THEMES[theme_name]
    tw = text_width(label, SIZE, "sans", 600)
    w = 14 + 16 + 8 + tw + 16
    if filled:
        fill = "url(#g)"
        stroke = "none"
        color = "#FFFFFF" if theme_name == "light" else "#0F172A"
    else:
        fill = theme["card"]
        stroke = theme["border"]
        color = theme["fg"]
    icon_color = color if filled else theme["primary"]
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{H}" viewBox="0 0 {w:.0f} {H}" role="img" aria-label="{esc(label)}">
<title>{esc(label)}</title>
<style>{font_face("sans", "O", label)}text{{font-family:O,system-ui,sans-serif;font-size:{SIZE}px;font-weight:600}}</style>
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{theme["primary"]}"/><stop offset="1" stop-color="{theme["secondary"]}"/></linearGradient></defs>
<rect x="0.5" y="0.5" width="{w - 1:.1f}" height="{H - 1}" rx="{(H - 1) / 2}" fill="{fill}" stroke="{stroke}"/>
{icon_svg(icon_name, 14, 9, 16, icon_color)}
<text x="38" y="22" fill="{color}">{esc(label)}</text>
</svg>
"""


if __name__ == "__main__":
    for theme_name in THEMES:
        for name, label, icon_name, filled in BADGES:
            write(OUT / f"{name}-{theme_name}.svg", build(theme_name, label, icon_name, filled))
