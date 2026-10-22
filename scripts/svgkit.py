"""Shared helpers for the profile SVGs: themes, fonts, icons, and text width.

Colors follow the tokens of anamcode.space (src/app/globals.css). Fonts are
subset to the characters each SVG uses and embedded as woff2 data URIs, because
GitHub shows these files as <img>, which cannot load external fonts.
"""

from __future__ import annotations

import base64
import io
import re
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent
ICONS = ROOT / "icons"
FONTS = {
    "sans": ROOT / "fonts" / "Outfit.ttf",
    "mono": ROOT / "fonts" / "JetBrainsMono.ttf",
}

THEMES = {
    "dark": {
        "bg": "#020617",
        "card": "#0F172A",
        "card2": "#1E293B",
        "fg": "#F1F5F9",
        "muted": "#94A3B8",
        "border": "#1E293B",
        "primary": "#A78BFA",
        "secondary": "#60A5FA",
        "accent": "#F472B6",
        "track": "#1E293B",
    },
    "light": {
        "bg": "#F8FAFC",
        "card": "#FFFFFF",
        "card2": "#F1F5F9",
        "fg": "#0F172A",
        "muted": "#475569",
        "border": "#E2E8F0",
        "primary": "#7C3AED",
        "secondary": "#2563EB",
        "accent": "#DB2777",
        "track": "#E2E8F0",
    },
}


def esc(text: str) -> str:
    return escape(text, {'"': "&quot;"})


@lru_cache(maxsize=None)
def _font(kind: str) -> TTFont:
    return TTFont(FONTS[kind])


@lru_cache(maxsize=None)
def _instance(kind: str, weight: int) -> TTFont:
    return instancer.instantiateVariableFont(TTFont(FONTS[kind]), {"wght": weight})


def text_width(text: str, size: float, kind: str = "sans", weight: int = 400) -> float:
    """Advance width of `text` in px, without kerning."""
    font = _instance(kind, weight)
    cmap = font.getBestCmap()
    hmtx = font["hmtx"]
    upm = font["head"].unitsPerEm
    total = 0
    for ch in text:
        glyph = cmap.get(ord(ch))
        if glyph is None:
            glyph = cmap[ord("?")]
        total += hmtx[glyph][0]
    return total * size / upm


def font_face(kind: str, family: str, text: str) -> str:
    """@font-face rule with the variable font subset to `text`."""
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["kern", "liga"]
    options.name_IDs = []
    options.notdef_outline = True
    font = TTFont(FONTS[kind])
    subsetter = subset.Subsetter(options)
    subsetter.populate(text=text + " ?")
    subsetter.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    data = base64.b64encode(buf.getvalue()).decode()
    return (
        f"@font-face{{font-family:{family};font-weight:100 900;"
        f"src:url(data:font/woff2;base64,{data}) format('woff2')}}"
    )


def icon(name: str) -> dict:
    """Return {'paths': [...], 'stroke': bool} for an icon in scripts/icons."""
    raw = (ICONS / f"{name}.svg").read_text()
    stroke = 'stroke="currentColor"' in raw
    shapes = re.findall(r"<(path|circle|rect)\b([^>]*?)/?>", raw)
    return {"shapes": shapes, "stroke": stroke}


def icon_svg(name: str, x: float, y: float, size: float, color: str) -> str:
    """Draw an icon (24x24 viewBox) at x, y with the given size."""
    data = icon(name)
    scale = size / 24
    parts = []
    for tag, attrs in data["shapes"]:
        attrs = attrs.strip()
        parts.append(f"<{tag} {attrs}/>")
    if data["stroke"]:
        style = (
            f'fill="none" stroke="{color}" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round"'
        )
    else:
        style = f'fill="{color}"'
    return (
        f'<g transform="translate({x:.2f} {y:.2f}) scale({scale:.4f})" {style}>'
        + "".join(parts)
        + "</g>"
    )


def brand_hex(name: str) -> str:
    """Brand color from simple-icons, stored in scripts/icons/colors.txt."""
    for line in (ICONS / "colors.txt").read_text().splitlines():
        key, _, value = line.partition(" ")
        if key == name:
            return "#" + value.strip()
    raise KeyError(name)


def luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))

    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def mix(a: str, b: str, amount: float) -> str:
    """Blend color a toward color b by `amount` (0 to 1)."""
    ca = [int(a.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(x + (y - x) * amount):02X}" for x, y in zip(ca, cb))


def icon_color(name: str, theme: str) -> str:
    """Brand color, lightened or darkened until it reads on the theme's cards."""
    color = brand_hex(name)
    if luminance(color) < 0.01:
        return THEMES[theme]["fg"]
    card = THEMES[theme]["card"]
    target, minimum = ("#FFFFFF", 3.2) if theme == "dark" else ("#000000", 2.0)
    step = 0.0
    out = color
    while contrast(out, card) < minimum and step < 1:
        step += 0.1
        out = mix(color, target, step)
    return out


def mulberry32(seed: int):
    """Same seeded generator as the portfolio site (src/lib/random.ts)."""
    state = seed & 0xFFFFFFFF

    def rand() -> float:
        nonlocal state
        state = (state + 0x6D2B79F5) & 0xFFFFFFFF
        t = state
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296

    return rand


def write(path: Path, svg: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    svg = re.sub(r">\s+<", "><", svg.strip())
    path.write_text(svg + "\n")
    print(f"{path.name}  {len(svg.encode()) / 1024:.1f} KB")
