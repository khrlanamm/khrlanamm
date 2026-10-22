"""Tech stack grid, grouped like the Skills section of anamcode.space.

Run: python scripts/stack.py  (needs fonttools and brotli)
Output: assets/stack-dark.svg, assets/stack-light.svg
"""

from __future__ import annotations

from pathlib import Path

from svgkit import THEMES, esc, font_face, icon_color, icon_svg, text_width, write

OUT = Path(__file__).resolve().parent.parent / "assets"

GROUPS = [
    ("Mobile", [("flutter", "Flutter"), ("dart", "Dart"), ("kotlin", "Kotlin"), ("jetpackcompose", "Compose"), ("android", "Android"), ("apple", "iOS")]),
    ("Web", [("nextdotjs", "Next.js"), ("react", "React"), ("typescript", "TypeScript"), ("tailwindcss", "Tailwind")]),
    ("Backend", [("firebase", "Firebase"), ("supabase", "Supabase"), ("postgresql", "PostgreSQL")]),
    ("AI and ML", [("googlegemini", "Gemini"), ("python", "Python")]),
    ("Tools", [("git", "Git"), ("githubactions", "GitHub Actions"), ("androidstudio", "Android Studio"), ("xcode", "Xcode"), ("figma", "Figma")]),
]

W = 880
PAD = 24
LABEL_W = 112
TILE_H = 40
GAP = 10
ROW_GAP = 14


def build(theme_name: str) -> str:
    theme = THEMES[theme_name]
    rows = []
    y = PAD
    delay = 0.0
    text = "".join(g for g, _ in GROUPS) + "".join(n for _, items in GROUPS for _, n in items)
    for group, items in GROUPS:
        rows.append(
            f'<text x="{PAD}" y="{y + 25}" class="label" fill="{theme["muted"]}">{esc(group)}</text>'
        )
        x = PAD + LABEL_W
        for slug, name in items:
            w = 14 + 20 + 8 + text_width(name, 14, "sans", 500) + 14
            rows.append(
                f'<g class="pop" style="animation-delay:{delay:.2f}s">'
                f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{TILE_H}" rx="12" '
                f'fill="{theme["card"]}" stroke="{theme["border"]}"/>'
                + icon_svg(slug, x + 14, y + 10, 20, icon_color(slug, theme_name))
                + f'<text x="{x + 42:.1f}" y="{y + 25.5}" class="name" fill="{theme["fg"]}">{esc(name)}</text></g>'
            )
            x += w + GAP
            delay += 0.04
        y += TILE_H + ROW_GAP
    height = y - ROW_GAP + PAD
    css = (
        font_face("sans", "O", text)
        + ".label{font-family:O,system-ui,sans-serif;font-size:13px;font-weight:600;letter-spacing:.06em;text-transform:uppercase}"
        + ".name{font-family:O,system-ui,sans-serif;font-size:14px;font-weight:500}"
        + ".pop{animation:pop .5s ease-out both}"
        + "@keyframes pop{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
        + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"
    )
    names = ", ".join(n for _, items in GROUPS for _, n in items)
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" role="img" aria-labelledby="title">
<title id="title">Tech stack: {esc(names)}</title>
<style>{css}</style>
<rect x="0.5" y="0.5" width="{W - 1}" height="{height - 1}" rx="20" fill="{theme["bg"]}" stroke="{theme["border"]}"/>
{"".join(rows)}
</svg>
"""


if __name__ == "__main__":
    for name in THEMES:
        write(OUT / f"stack-{name}.svg", build(name))
