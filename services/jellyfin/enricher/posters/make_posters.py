"""Render collection posters from template.svg into ../collection-images/.

Each poster is template.svg with its placeholders filled from posters.yaml: colours, an icon from
icons/, a label and the title, fitted to the width. The enricher uploads the results.

  pip install -r requirements.txt
  python make_posters.py                      # the collections listed in posters.yaml
  python make_posters.py --all --out /tmp/p   # every collection, e.g. to preview the defaults
  python make_posters.py "Aviation Collection"
  python make_posters.py --preview --watch    # samples into preview/, re-rendered on every save
"""

import argparse
import base64
import colorsys
import hashlib
import io
import json
import os
import re
import string
import sys
import time
import urllib.parse
from xml.sax.saxutils import escape

import resvg_py
import yaml
from fontTools.ttLib import TTFont
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")

# Title box, in template pixels: lines are fitted to TITLE_WIDTH, and stacked upwards from the
# baseline at TITLE_BOTTOM no higher than TITLE_HEIGHT.
TITLE_X, TITLE_WIDTH, TITLE_BOTTOM, TITLE_HEIGHT = 90, 820, 1370, 560
MAX_SIZE, LINE_HEIGHT, MAX_LINES = 300, 0.9, 4


class Font:
    """Advance widths from a font file, to measure text without rendering it."""

    def __init__(self, path):
        font = TTFont(path)
        self.units = font["head"].unitsPerEm
        self.cap_height = font["OS/2"].sCapHeight / self.units
        self.cmap = font.getBestCmap()
        self.advance = font["hmtx"].metrics

    def width(self, text):
        """Width of `text` at a font size of 1."""
        space = self.advance[self.cmap[ord(" ")]][0]
        return sum(self.advance[self.cmap[ord(c)]][0] if ord(c) in self.cmap else space for c in text) / self.units


def splits(words, n):
    """Every way to break `words` into `n` non-empty lines, in order."""
    if n == 1:
        yield [" ".join(words)]
        return
    for i in range(1, len(words) - n + 2):
        for rest in splits(words[i:], n - 1):
            yield [" ".join(words[:i])] + rest


def fit_title(text, font, width=TITLE_WIDTH):
    """Break `text` into lines (or keep a given list of lines) and pick the largest font size that
    fits the title box, `width` wide. Returns (lines, size); fewer lines win a tie."""
    candidates = [text] if isinstance(text, list) else [
        lines for n in range(1, min(MAX_LINES, len(text.split())) + 1) for lines in splits(text.split(), n)]
    best = None
    for lines in candidates:
        widest = max(font.width(line.upper()) for line in lines)
        size = min(MAX_SIZE, width / widest, TITLE_HEIGHT / (font.cap_height + LINE_HEIGHT * (len(lines) - 1)))
        if best is None or size > best[1] + 1:
            best = (lines, size)
    return best


def hue_colours(name):
    """A background and accent from a hue derived from the name, so unlisted posters differ."""
    hue = int(hashlib.sha256(name.encode()).hexdigest()[:4], 16) / 0xFFFF
    return hls(hue, 0.18, 0.45), hls(hue, 0.66, 0.85)


def hls(h, l, s):
    return "#" + "".join(f"{round(c * 255):02x}" for c in colorsys.hls_to_rgb(h, l, s))


def darken(colour, factor=0.45):
    r, g, b = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(c * factor):02x}" for c in (r, g, b))


def svg_markup(folder, name):
    """The drawing inside <folder>/<name>.svg, without its outer <svg> element."""
    with open(os.path.join(HERE, folder, f"{name}.svg")) as f:
        svg = f.read()
    m = re.search(r"<svg\b[^>]*>(.*)</svg>", svg, re.S)
    if not m:
        raise ValueError(f"{folder}/{name}.svg has no <svg> element")
    return m.group(1)


LOGO_TYPES = {".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg"}
LOGO_BOX = (130, 230, 740, 440)  # x, y, width, height the logo is fitted into


def logo_markup(name, tint, box=LOGO_BOX):
    """An <image> of logos/<name>.svg (or .png/.jpg), embedded and fitted into `box` (x, y, width,
    height). With `tint`, it is recoloured in the accent colour, for logos that are black."""
    def find():
        for ext, mime in LOGO_TYPES.items():
            path = os.path.join(HERE, "logos", name + ext)
            if os.path.exists(path):
                return path, mime
        return None, None

    path, mime = find()
    if path is None:  # logos aren't kept in git; download it (logos/sources.yaml)
        import fetch_logos
        fetch_logos.ensure([name])
        path, mime = find()
    if path is None:
        raise FileNotFoundError(f"no logos/{name}.svg, .png or .jpg")
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    x, y, w, h = box
    return (f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet"'
            f'{' filter="url(#tint)"' if tint else ""} href="data:{mime};base64,{data}"/>')


def backdrop_markup(settings):
    """What sits behind the poster: a flag, or a logo drawn large and faded (`backdrop_logo`,
    `backdrop_box`, `backdrop_opacity`), with the dark fade over it so the title stays readable."""
    if settings.get("flag"):
        art = svg_markup("flags", settings["flag"])
    elif settings.get("backdrop_logo"):
        art = (f'<g opacity="{settings.get("backdrop_opacity", 0.35)}">'
               + logo_markup(str(settings["backdrop_logo"]), settings.get("backdrop_tint", True),
                             settings.get("backdrop_box", [-100, 40, 1200, 1200])) + "</g>")
    else:
        return ""
    return art + '<rect width="1000" height="1500" fill="url(#shade)"/>'


def poster_svg(name, settings, template, title_font):
    title = settings.get("title") or re.sub(r"\s+Collection$", "", name)
    inset = settings.get("title_inset", 0)  # narrows the title box on both sides, e.g. for art
    title_x = TITLE_X + inset
    lines, size = fit_title(title, title_font, TITLE_WIDTH - 2 * inset)
    background, accent = hue_colours(name)
    background = settings.get("background", background)
    baselines = [TITLE_BOTTOM - size * LINE_HEIGHT * (len(lines) - 1 - i) for i in range(len(lines))]
    title_top = baselines[0] - size * title_font.cap_height
    tspans = "".join(f'<text x="{title_x}" y="{y:.0f}" font-size="{size:.0f}">{escape(line.upper())}</text>'
                     for line, y in zip(lines, baselines))
    return string.Template(template).substitute(
        background=background,
        background_dark=settings.get("background_dark", darken(background)),
        accent=settings.get("accent", accent),
        foreground=settings.get("foreground", "#f4f1ea"),
        icon="" if settings.get("icon") == "none" else svg_markup("icons", settings.get("icon", "rings")),
        art=svg_markup("art", settings["art"]) if settings.get("art") else "",
        logo=(logo_markup(settings["logo"], settings.get("logo_tint", True), settings.get("logo_box", LOGO_BOX))
              if settings.get("logo") else ""),
        backdrop=backdrop_markup(settings),
        label=escape(settings.get("label", "COLLECTION").upper()),
        title_x=title_x,
        rule_y=f"{title_top - 56:.0f}",
        label_y=f"{title_top - 86:.0f}",
        title=tspans,
    )


def render(svg, path):
    # Relative image references resolve in flags/, e.g. the Mexican flag's coat of arms.
    png = resvg_py.svg_to_bytes(svg_string=svg, skip_system_fonts=True, font_dirs=[FONTS],
                                resources_dir=os.path.join(HERE, "flags"))
    Image.open(io.BytesIO(bytes(png))).convert("RGB").save(path, quality=90, optimize=True)


PREVIEW_PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Poster preview</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body {{ margin: 0; padding: 16px; background: #1c1c1c; color: #ccc; font: 14px system-ui, sans-serif; }}
  main {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }}
  figure {{ margin: 0; }} img {{ width: 100%; display: block; }} figcaption {{ padding-top: 6px; }}
</style></head>
<body><p>Rendered {when}. This page reloads every 3 seconds.</p><main>
{figures}
</main><script>setTimeout(() => location.reload(), 3000)</script></body></html>
"""


def write_preview_page(out, paths):
    """An index.html showing the posters side by side; cache-busted so a reload shows new renders."""
    stamp = int(time.time())
    figures = "\n".join(
        f'<figure><img src="{escape(urllib.parse.quote(os.path.basename(p)))}?{stamp}" alt=""><figcaption>'
        f"{escape(os.path.basename(p)[:-4])}</figcaption></figure>" for p in paths)
    with open(os.path.join(out, "index.html"), "w") as f:
        f.write(PREVIEW_PAGE.format(when=time.strftime("%H:%M:%S"), figures=figures))


def watched_mtimes():
    files = [os.path.join(HERE, n) for n in ("template.svg", "posters.yaml")]
    for folder in ("icons", "flags", "art", "logos"):
        files += [os.path.join(HERE, folder, n) for n in os.listdir(os.path.join(HERE, folder))]
    return {f: os.path.getmtime(f) for f in files}


def render_all(args):
    with open(os.path.join(HERE, "posters.yaml")) as f:
        cfg = yaml.safe_load(f) or {}
    with open(os.path.join(HERE, "..", "auto-collections.json")) as f:
        collections = [c["CollectionName"] for c in json.load(f)["ExpressionCollections"]]
    with open(os.path.join(HERE, "template.svg")) as f:
        template = f.read()
    posters = dict(cfg.get("posters") or {})
    for extra in args.settings or []:  # more posters, e.g. a batch being designed separately
        with open(extra) as f:
            posters.update((yaml.safe_load(f) or {}).get("posters") or {})
    unknown = sorted(set(posters) - set(collections))
    if unknown:
        sys.exit(f"posters.yaml names collections not in auto-collections.json: {unknown}")
    if args.names:
        names = args.names
    elif args.all:
        names = collections
    elif args.preview:
        names = list(dict.fromkeys(list(posters) + (cfg.get("preview") or [])))
    else:
        names = list(posters)
    if args.keep:  # collections that already have an image there, e.g. one made by hand, are skipped
        kept = {os.path.splitext(f)[0].casefold() for f in os.listdir(args.keep)
                if os.path.splitext(f)[1].lower() in (".jpg", ".jpeg", ".png", ".webp")}
        for name in [n for n in names if n.casefold() in kept]:
            print(f"keeping the existing image for {name}")
        names = [n for n in names if n.casefold() not in kept]
    title_font = Font(os.path.join(FONTS, "BebasNeue-Regular.ttf"))

    os.makedirs(args.out, exist_ok=True)
    paths = []
    for name in names:
        if name not in collections:
            sys.exit(f"no collection {name!r} in auto-collections.json")
        svg = poster_svg(name, {**(cfg.get("defaults") or {}), **(posters.get(name) or {})}, template, title_font)
        path = os.path.join(args.out, f"{name}.jpg")
        render(svg, path)
        if args.svg:
            with open(path[:-4] + ".svg", "w") as f:
                f.write(svg)
        paths.append(path)
        if not args.watch:
            print(path)
    if args.preview:
        write_preview_page(args.out, paths)
    return paths


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("names", nargs="*", help="collections to render (default: those in posters.yaml)")
    p.add_argument("--all", action="store_true", help="render every collection in auto-collections.json")
    p.add_argument("--preview", action="store_true",
                   help="render posters.yaml's posters and preview list into preview/, with an index.html")
    p.add_argument("--watch", action="store_true",
                   help="render again whenever template.svg, posters.yaml, an icon, a flag or art changes")
    p.add_argument("--out", help="output folder (default: ../collection-images, or preview/ with --preview)")
    p.add_argument("--svg", action="store_true", help="also write the filled-in SVG next to each poster")
    p.add_argument("--settings", action="append", help="another posters.yaml-style file to add posters from")
    p.add_argument("--keep", metavar="DIR", help="skip collections that already have an image in DIR")
    args = p.parse_args(argv)
    if args.out is None:
        args.out = os.path.join(HERE, "preview" if args.preview else os.path.join("..", "collection-images"))

    if not args.watch:
        render_all(args)
        return
    print(f"watching template.svg, posters.yaml, icons/, flags/ and art/; rendering into {args.out} (Ctrl+C stops)", flush=True)
    seen = None
    while True:
        now = watched_mtimes()
        if now != seen:
            seen = now
            try:
                paths = render_all(args)
                print(f"{time.strftime('%H:%M:%S')} rendered {len(paths)} posters", flush=True)
            except (SystemExit, Exception) as e:  # keep watching through a half-saved edit
                print(f"{time.strftime('%H:%M:%S')} render failed: {e}", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    main()
