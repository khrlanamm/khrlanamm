"""Latest Medium posts in README.md, run weekly by .github/workflows/blog.yml.

Run: python scripts/blog.py  (stdlib only)
Rewrites the lines between the BLOG-POST-LIST markers. Links drop Medium's
tracking query string, and nothing changes when the list is the same.
"""

from __future__ import annotations

import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

FEED = "https://medium.com/feed/@khoirulanam1604"
README = Path(__file__).resolve().parent.parent / "README.md"
LIMIT = 3
START, END = "<!-- BLOG-POST-LIST:START -->", "<!-- BLOG-POST-LIST:END -->"


def posts() -> list[str]:
    req = urllib.request.Request(FEED, headers={"User-Agent": "Mozilla/5.0 (profile README updater)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        root = ET.fromstring(resp.read())
    lines = []
    for item in root.iter("item"):
        title = item.findtext("title", "").strip().replace("[", "(").replace("]", ")")
        url = item.findtext("link", "").split("?")[0]
        date = parsedate_to_datetime(item.findtext("pubDate", "")).strftime("%b %Y")
        lines.append(f"- [{title}]({url}) <sub>{date}</sub>")
        if len(lines) == LIMIT:
            break
    return lines


def main() -> None:
    text = README.read_text()
    block = START + "\n" + "\n".join(posts()) + "\n" + END
    updated = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
    if updated != text:
        README.write_text(updated)
        print("README updated")
    else:
        print("No new posts")


if __name__ == "__main__":
    main()
