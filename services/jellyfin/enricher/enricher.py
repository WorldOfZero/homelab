"""Additively enrich Jellyfin items with metadata (tags, genres) derived from external sources.

Currently one source: IMDb keywords, looked up per item by IMDb id. Rules in config.yaml map
keywords to tags/genres; matching values are appended to the item and nothing is ever removed.
"""

import argparse
import datetime as dt
import json
import logging
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

import yaml

log = logging.getLogger("enricher")

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
WRITABLE_FIELDS = ("Tags", "Genres")


def normalize(text):
    return re.sub(r"\s+", " ", text.replace("-", " ")).strip().casefold()


def http_json(url, method="GET", headers=None, body=None, timeout=30):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return json.loads(raw) if raw else None


class Jellyfin:
    def __init__(self, url, api_key):
        self.url = url.rstrip("/")
        self.headers = {"Authorization": f'MediaBrowser Token="{api_key}"', "Accept": "application/json"}
        self._user_id = None

    def _call(self, path, method="GET", params=None, body=None):
        url = f"{self.url}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        return http_json(url, method=method, headers=self.headers, body=body)

    def user_id(self):
        # GET /Items/{id} needs a user context; use the first administrator.
        if self._user_id is None:
            users = self._call("/Users")
            admins = [u for u in users if u.get("Policy", {}).get("IsAdministrator")]
            self._user_id = (admins or users)[0]["Id"]
        return self._user_id

    def items(self, item_types, page_size=500):
        start = 0
        while True:
            page = self._call("/Items", params={
                "Recursive": "true",
                "IncludeItemTypes": ",".join(item_types),
                "Fields": "ProviderIds,Tags,Genres",
                "StartIndex": start,
                "Limit": page_size,
            })
            yield from page["Items"]
            start += len(page["Items"])
            if not page["Items"] or start >= page.get("TotalRecordCount", 0):
                return

    def get_item(self, item_id):
        return self._call(f"/Items/{item_id}", params={"userId": self.user_id()})

    def update_item(self, item_id, dto):
        # POST /Items/{id} replaces the item's metadata with the DTO, so always send the full
        # DTO fetched just before, with only the additive fields changed.
        self._call(f"/Items/{item_id}", method="POST", body=dto)


class KeywordSource:
    """IMDb keywords per title as {normalized keyword: (relevant votes, total votes)}, cached on disk."""

    def __init__(self, cache_path, sources, kometa_url, imdb_url, cache_days, request_delay):
        self.cache_path = cache_path
        self.sources = sources
        self.kometa_url = kometa_url.rstrip("/")
        self.imdb_url = imdb_url.rstrip("/")
        self.cache_seconds = cache_days * 86400
        self.request_delay = request_delay
        self.lookups = 0
        try:
            with open(cache_path) as f:
                self.cache = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.cache = {}

    def save(self):
        tmp = self.cache_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.cache, f)
        os.replace(tmp, self.cache_path)

    def cached(self, imdb_id):
        entry = self.cache.get(imdb_id)
        if entry and time.time() - entry["fetched"] < self.cache_seconds:
            return {k: tuple(v) for k, v in entry["keywords"].items()}
        return None

    def get(self, imdb_id):
        hit = self.cached(imdb_id)
        if hit is not None:
            return hit
        keywords = None
        for source in self.sources:
            try:
                keywords = getattr(self, f"_from_{source}")(imdb_id)
                break
            except Exception as e:  # try the next source
                log.warning("keyword source %s failed for %s: %s", source, imdb_id, e)
        self.lookups += 1
        time.sleep(self.request_delay)
        if keywords is None:
            return {}  # every source failed: don't cache, retry next run
        self.cache[imdb_id] = {"fetched": int(time.time()), "keywords": keywords}
        return {k: tuple(v) for k, v in keywords.items()}

    def _from_kometa(self, imdb_id):
        # Kometa's public IMDb keyword service, the same one Kometa's imdb_keyword filter uses.
        try:
            data = http_json(f"{self.kometa_url}/keywords/{imdb_id}", headers={"User-Agent": USER_AGENT})
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {}
            raise
        out = {}
        for name, votes in ((data or {}).get("keywords") or {}).items():
            out[normalize(name)] = list(votes)[:2] if isinstance(votes, list) else [0, 0]
        return out

    def _from_imdb(self, imdb_id):
        # Fallback: the title's keyword page embeds its data as JSON in __NEXT_DATA__.
        req = urllib.request.Request(f"{self.imdb_url}/title/{imdb_id}/keywords/",
                                     headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", "replace")
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
        if not m:
            raise ValueError("no __NEXT_DATA__ on keyword page")
        out = {}
        for node in walk(json.loads(m.group(1))):
            kw = node.get("keyword")
            if not isinstance(kw, dict):
                continue
            text = kw.get("text")
            text = text.get("text") if isinstance(text, dict) else text
            if not isinstance(text, str):
                continue
            score = node.get("interestScore") or {}
            out[normalize(text)] = [score.get("usersInterested", 0), score.get("usersVoted", 0)]
        return out


def walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)


class Rule:
    def __init__(self, spec, defaults):
        self.name = spec.get("name") or ", ".join(spec.get("add", {}).get("tags", []))
        match = spec["match"]
        bad = [k for k in match["imdb_keywords"] if not isinstance(k, str)]
        if bad:
            raise ValueError(f"rule {self.name!r}: quote non-text keywords {bad} in YAML")
        self.keywords = {normalize(k) for k in match["imdb_keywords"]}
        self.min_relevant = match.get("min_relevant", defaults.get("min_relevant", 0))
        self.min_votes = match.get("min_votes", defaults.get("min_votes", 0))
        self.min_percentage = match.get("min_percentage", defaults.get("min_percentage", 0))
        self.item_types = set(spec.get("item_types", []))
        self.add = {f: list(spec.get("add", {}).get(f.lower(), [])) for f in WRITABLE_FIELDS}
        if not any(self.add.values()):
            raise ValueError(f"rule {self.name!r} adds nothing")

    def matches(self, item_type, keywords):
        if self.item_types and item_type not in self.item_types:
            return False
        for kw in self.keywords & keywords.keys():
            relevant, total = keywords[kw]
            if relevant >= self.min_relevant and total >= self.min_votes and (
                    total == 0 or relevant / total >= self.min_percentage):
                return True
        return False


def missing_values(current, wanted):
    have = {v.casefold() for v in current or []}
    out = []
    for v in wanted:
        if v.casefold() not in have:
            have.add(v.casefold())
            out.append(v)
    return out


def run(cfg, jellyfin, source, dry_run):
    rules = [Rule(r, cfg.get("defaults", {})) for r in cfg["rules"]]
    max_lookups = cfg.get("max_lookups_per_run", 2000)
    stats = {"items": 0, "no_imdb": 0, "changed": 0, "skipped_lookups": 0}
    for item in jellyfin.items(cfg.get("item_types", ["Movie", "Series"])):
        stats["items"] += 1
        imdb_id = (item.get("ProviderIds") or {}).get("Imdb")
        if not imdb_id:
            stats["no_imdb"] += 1
            continue
        if source.cached(imdb_id) is None and source.lookups >= max_lookups:
            stats["skipped_lookups"] += 1
            continue
        before = source.lookups
        keywords = source.get(imdb_id)
        if source.lookups != before and source.lookups % 50 == 0:
            source.save()  # checkpoint so a crash mid-run doesn't lose the lookups
        additions = {f: [] for f in WRITABLE_FIELDS}
        for rule in rules:
            if rule.matches(item.get("Type"), keywords):
                for f in WRITABLE_FIELDS:
                    additions[f] += rule.add[f]
        additions = {f: missing_values(item.get(f), v) for f, v in additions.items()}
        additions = {f: v for f, v in additions.items() if v}
        if not additions:
            continue
        stats["changed"] += 1
        log.info("%s %s (%s): add %s", "would update" if dry_run else "updating",
                 item.get("Name"), imdb_id, additions)
        if dry_run:
            continue
        dto = jellyfin.get_item(item["Id"])
        changed = False
        for f, values in additions.items():
            new = missing_values(dto.get(f), values)  # recheck against the fresh DTO
            if new:
                dto[f] = list(dto.get(f) or []) + new
                changed = True
        if changed:
            jellyfin.update_item(item["Id"], dto)
    source.save()
    log.info("done: %s, %d keyword lookups%s", stats, source.lookups, " (dry run)" if dry_run else "")
    return stats


def seconds_until(run_at, tz):
    now = dt.datetime.now(tz)
    hour, minute = map(int, run_at.split(":"))
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += dt.timedelta(days=1)
    return (target - now).total_seconds()


def env_flag(name, default):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", default=os.environ.get("ENRICHER_CONFIG", "/app/config.yaml"))
    p.add_argument("--once", action="store_true", help="run once and exit instead of scheduling")
    p.add_argument("--dry-run", action="store_true", default=None, help="log changes without writing")
    args = p.parse_args(argv)
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"),
                        format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)

    with open(args.config) as f:
        cfg = yaml.safe_load(f)
    dry_run = args.dry_run if args.dry_run is not None else env_flag("DRY_RUN", True)
    data_dir = os.environ.get("DATA_DIR", "/data")
    os.makedirs(data_dir, exist_ok=True)

    jellyfin = Jellyfin(os.environ.get("JELLYFIN_URL", "http://127.0.0.1:8096"), os.environ["JELLYFIN_APIKEY"])
    kw_cfg = cfg.get("imdb_keywords", {})

    def once():
        source = KeywordSource(
            os.path.join(data_dir, "imdb_keywords.json"),
            sources=kw_cfg.get("sources", ["kometa", "imdb"]),
            kometa_url=os.environ.get("KOMETA_SERVICE_URL", "https://utilities.kometa.wiki/imdb-service"),
            imdb_url=os.environ.get("IMDB_URL", "https://www.imdb.com"),
            cache_days=kw_cfg.get("cache_days", 30),
            request_delay=float(kw_cfg.get("request_delay_seconds", 1.0)),
        )
        return run(cfg, jellyfin, source, dry_run)

    if args.once or not os.environ.get("RUN_AT"):
        once()
        return
    tz = ZoneInfo(os.environ.get("TZ", "UTC"))
    pending = env_flag("RUN_ON_START", True)
    while True:
        if pending:
            try:
                once()
            except Exception:
                log.exception("run failed; will retry at next scheduled time")
        wait = seconds_until(os.environ["RUN_AT"], tz)
        log.info("next run in %.1f hours", wait / 3600)
        time.sleep(wait)
        pending = True


if __name__ == "__main__":
    main()
