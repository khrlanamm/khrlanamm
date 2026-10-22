# Profile assets

Generators for the SVGs in the profile README. Colors follow the theme tokens of [anamcode.space](https://anamcode.space).

| Script | Output | When |
|---|---|---|
| `banner.py` | `assets/banner-*.svg` | By hand, after changing the text |
| `stack.py` | `assets/stack-*.svg` | By hand, after changing the stack |
| `badges.py` | `assets/badges/*.svg` | By hand, after changing a link |
| `stats.py` | `activity-*.svg`, `languages-*.svg` on the `output` branch | Daily, by `.github/workflows/stats.yml` |
| `blog.py` | Medium list in `README.md` | Weekly, by `.github/workflows/blog.yml` |

```sh
pip install fonttools brotli
cd scripts
python banner.py && python stack.py && python badges.py
STATS_TOKEN=... python stats.py ../dist   # local preview of the cards
```

Fonts: Outfit and JetBrains Mono (SIL Open Font License, see `fonts/`), subset to the characters each SVG uses. Icons: [Simple Icons](https://simpleicons.org) (CC0) and [Lucide](https://lucide.dev) (ISC). `linkedin-in.svg` is drawn for this repository.
