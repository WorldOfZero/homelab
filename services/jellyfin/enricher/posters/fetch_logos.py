"""Download the logos listed in logos/sources.yaml into logos/.

The logos are their owners' trademarks, and several are non-free files from English Wikipedia,
so they are not kept in git. The enricher's image build runs this, and make_posters.py runs it
for any logo it is missing.

  python fetch_logos.py              # the logos not downloaded yet
  python fetch_logos.py --force dc   # download a logo again
"""

import argparse
import hashlib
import io
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
LOGOS = os.path.join(HERE, "logos")
# Wikimedia asks automated clients for a descriptive User-Agent with a way to get in touch.
USER_AGENT = "homelab-jellyfin-posters/1.0 (https://github.com/WorldOfZero/homelab) python-urllib"


def load_sources():
    with open(os.path.join(LOGOS, "sources.yaml")) as f:
        return {str(k): v for k, v in yaml.safe_load(f).items()}


def wikimedia_url(entry):
    """upload.wikimedia.org stores a file under the first one and two hex digits of the MD5 of
    its name, with spaces as underscores."""
    name = entry["file"].replace(" ", "_")
    digest = hashlib.md5(name.encode()).hexdigest()
    site = "en" if entry.get("wiki") == "en" else "commons"
    return f"https://upload.wikimedia.org/wikipedia/{site}/{digest[0]}/{digest[:2]}/{urllib.parse.quote(name)}"


def target_path(name, entry):
    ext = ".png" if entry.get("fix") == "white_to_alpha" else os.path.splitext(entry["file"])[1].lower()
    return os.path.join(LOGOS, name + ext)


def check_svg(data, name):
    # Downloaded files are untrusted: refuse scripts and anything loaded from elsewhere.
    text = data.decode("utf-8", "replace")
    if re.search(r"<script|javascript:|href\s*=\s*[\"']\s*(https?:|//)", text, re.I):
        raise ValueError(f"{name}: SVG has a script or a remote reference")
    return text


def strip_units(text):
    """Drop pt/mm/px units from the root <svg> element's width and height."""
    root = re.search(r"<svg\b[^>]*>", text, re.S)
    fixed = re.sub(r'(\s(?:width|height)=")([\d.]+)(?:pt|mm|px)"', r'\1\2"', root.group(0))
    return text[:root.start()] + fixed + text[root.end():]


def white_to_alpha(data, is_svg):
    """A PNG of the image with white made transparent: alpha falls as a pixel gets lighter."""
    from PIL import Image

    if is_svg:
        import resvg_py
        data = bytes(resvg_py.svg_to_bytes(svg_string=data.decode("utf-8"), width=1600))
    from PIL import ImageChops, ImageOps
    image = Image.open(io.BytesIO(data)).convert("RGBA")
    r, g, b, a = image.split()
    darkness = ImageOps.invert(ImageChops.darker(r, ImageChops.darker(g, b)))  # 255 - min(r, g, b)
    image.putalpha(ImageChops.multiply(a, darkness))
    out = io.BytesIO()
    image.save(out, "PNG", optimize=True)
    return out.getvalue()


def download(url, attempts=6):
    """GET `url`, waiting and retrying when Wikimedia answers 429 (too many requests)."""
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == attempts - 1:
                raise
            wait = int(e.headers.get("Retry-After") or 0) or 5 * 2 ** attempt
            print(f"rate limited by upload.wikimedia.org, waiting {wait}s", file=sys.stderr)
            time.sleep(wait)


def fetch(name, entry):
    data = download(wikimedia_url(entry))
    is_svg = entry["file"].lower().endswith(".svg")
    if is_svg:
        text = check_svg(data, name)
        if entry.get("fix") == "strip_units":
            data = strip_units(text).encode("utf-8")
    if entry.get("fix") == "white_to_alpha":
        data = white_to_alpha(data, is_svg)
    path = target_path(name, entry)
    with open(path + ".tmp", "wb") as f:
        f.write(data)
    os.replace(path + ".tmp", path)
    return path


def ensure(names=None, force=False):
    """Download the named logos (default: all) that are missing, or all of them with `force`."""
    sources = load_sources()
    unknown = sorted(set(names or []) - set(sources))
    if unknown:
        raise KeyError(f"no logos/sources.yaml entry for {unknown}")
    fetched = []
    for name in names or sources:
        entry = sources[name]
        if force or not os.path.exists(target_path(name, entry)):
            fetched.append(fetch(name, entry))
            time.sleep(1)  # be gentle with upload.wikimedia.org
    return fetched


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("names", nargs="*", help="logos to fetch (default: all in logos/sources.yaml)")
    p.add_argument("--force", action="store_true", help="download again even if the file exists")
    args = p.parse_args(argv)
    for path in ensure(args.names, args.force):
        print(path)


if __name__ == "__main__":
    sys.exit(main())
