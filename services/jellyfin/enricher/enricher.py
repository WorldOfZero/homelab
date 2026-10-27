"""Additively enrich Jellyfin items with metadata (tags, genres) derived from external sources.

Currently one source: IMDb keywords, looked up per item by IMDb id. Rules in config.yaml map
keywords to tags/genres; matching values are appended to the item and nothing is ever removed.
"""

import argparse
import base64
import datetime as dt
import hashlib
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
    if data is None and method != "GET":
        data = b""  # send Content-Length: 0 rather than no length on a body-less POST
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    if body is not None:
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
        # Item queries need a user context; use the first administrator. Without one, Jellyfin 12's
        # GET /Items ignores IncludeItemTypes and returns mostly collections, not the library.
        if self._user_id is None:
            users = self._call("/Users")
            admins = [u for u in users if u.get("Policy", {}).get("IsAdministrator")]
            self._user_id = (admins or users)[0]["Id"]
        return self._user_id

    def items(self, item_types, page_size=500):
        start = 0
        while True:
            page = self._call("/Items", params={
                "userId": self.user_id(),
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

    def set_primary_image(self, item_id, data, content_type):
        # Jellyfin decodes the request body as base64, not as raw image bytes.
        req = urllib.request.Request(f"{self.url}/Items/{item_id}/Images/Primary", data=base64.b64encode(data),
                                     method="POST", headers={**self.headers, "Content-Type": content_type})
        with urllib.request.urlopen(req, timeout=60):
            pass

    def update_item(self, item_id, dto):
        # POST /Items/{id} replaces the item's metadata with the DTO, so always send the full
        # DTO fetched just before, with only the additive fields changed.
        self._call(f"/Items/{item_id}", method="POST", body=dto)

    def wait_until_ready(self, timeout, interval=10):
        """Wait until GET /health answers 200: Jellyfin refuses connections while it starts and
        answers 503 during startup and database migrations."""
        deadline = time.monotonic() + timeout
        logged = False
        while True:
            try:
                req = urllib.request.Request(f"{self.url}/health", headers=self.headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status == 200:
                        if logged:
                            log.info("jellyfin is up")
                        return
            except OSError as e:  # URLError, HTTPError and connection errors
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"jellyfin not ready after {timeout:.0f}s: {e}") from e
                if not logged:
                    log.info("waiting for jellyfin: %s", e)
                    logged = True
            time.sleep(interval)

    def plugin_id(self, name):
        plugins = self._call("/Plugins")
        matches = [p for p in plugins if p["Name"].casefold() == name.casefold()]
        if not matches:
            raise LookupError(f"plugin {name!r} not installed; have: {sorted(p['Name'] for p in plugins)}")
        # Jellyfin answers 404 for the configuration of a plugin that is not loaded (an old version
        # that this server does not support, or one waiting for a restart), so use the active one.
        for p in matches:
            if p.get("Status", "Active") == "Active":
                return p["Id"]
        raise LookupError(f"plugin {name!r} is not active: "
                          + ", ".join(f"{p.get('Version')} is {p.get('Status')}" for p in matches))

    def plugin_config(self, plugin_id):
        return self._call(f"/Plugins/{plugin_id}/Configuration")

    def set_plugin_config(self, plugin_id, config):
        self._call(f"/Plugins/{plugin_id}/Configuration", method="POST", body=config)

    def start_task(self, name):
        """Start the first scheduled task whose name contains `name` (case-insensitive); returns it."""
        tasks = self._call("/ScheduledTasks")
        for task in tasks:
            if name.casefold() in task["Name"].casefold():
                self._call(f"/ScheduledTasks/Running/{task['Id']}", method="POST")
                return task
        raise LookupError(f"no scheduled task matching {name!r}; have: {sorted(t['Name'] for t in tasks)}")

    def wait_for_task(self, task, timeout, interval=10):
        """Wait until a task returned by start_task has finished: idle, with a newer last result
        than when it was started. Returns False on timeout."""
        before = (task.get("LastExecutionResult") or {}).get("EndTimeUtc")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            time.sleep(interval)
            now = self._call(f"/ScheduledTasks/{task['Id']}")
            if now.get("State") == "Idle" and (now.get("LastExecutionResult") or {}).get("EndTimeUtc") != before:
                return True
        return False


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


MANAGED_PLUGIN_KEYS = ("ExpressionCollections", "TitleMatchPairs")


def load_auto_collections(path):
    """Read the plugin's own export/import JSON into the desired values for the managed keys."""
    with open(path) as f:
        spec = json.load(f)
    desired = {k: list(spec.get(k, [])) for k in MANAGED_PLUGIN_KEYS}
    names = [c["CollectionName"] for c in desired["ExpressionCollections"]]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        raise ValueError(f"duplicate CollectionName in {path}: {dupes}")
    return desired


def sync_auto_collections(settings, jellyfin, dry_run):
    """Make the Auto Collections plugin's collection definitions match the repo.

    Authoritative for the managed keys (a collection removed from the file is removed from the
    plugin); every other key in the plugin's configuration is left as Jellyfin has it.
    Returns True if the plugin configuration changed (or would have, in a dry run).
    """
    path = settings["file"]
    desired = load_auto_collections(path)
    plugin_id = jellyfin.plugin_id(settings.get("plugin_name", "Auto Collections"))
    current = jellyfin.plugin_config(plugin_id)
    if all(current.get(k) == desired[k] for k in MANAGED_PLUGIN_KEYS):
        log.info("auto collections: plugin config already matches %s", os.path.basename(path))
        return False
    have = {c.get("CollectionName"): c for c in current.get("ExpressionCollections") or []}
    want = {c["CollectionName"]: c for c in desired["ExpressionCollections"]}
    log.info("auto collections: %s plugin config: +%s -%s ~%s%s",
             "would update" if dry_run else "updating",
             sorted(want.keys() - have.keys()), sorted(have.keys() - want.keys()),
             sorted(n for n in want.keys() & have.keys() if want[n] != have[n]),
             " (TitleMatchPairs changed)" if current.get("TitleMatchPairs") != desired["TitleMatchPairs"] else "")
    if not dry_run:
        jellyfin.set_plugin_config(plugin_id, {**current, **desired})
    return True


def refresh_auto_collections(settings, jellyfin):
    """Start the plugin's scheduled task; returns the task, or None if there is no such task."""
    try:
        task = jellyfin.start_task(settings.get("task_name", "Auto Collection"))
    except LookupError as e:
        log.warning("auto collections: %s (collections update on the plugin's own schedule)", e)
        return None
    log.info("auto collections: started task %r", task["Name"])
    return task


IMAGE_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


def load_collection_images(directory):
    """{casefolded collection name: file path} for the images in `directory`, each named after its
    collection, e.g. "Aviation Collection.jpg". Other files (a README) are ignored."""
    out = {}
    for name in sorted(os.listdir(directory)):
        stem, ext = os.path.splitext(name)
        if ext.lower() not in IMAGE_TYPES:
            continue
        if stem.casefold() in out:
            raise ValueError(f"two images for collection {stem!r} in {directory}")
        out[stem.casefold()] = os.path.join(directory, name)
    return out


def apply_collection_images(directory, jellyfin, state_path, dry_run):
    """Set each collection's primary image from its file in `directory`.

    Uploads only when the file changed, or when the collection's image is no longer the one
    uploaded: the plugin recreated the collection, or a metadata refresh replaced the image.
    The state file records the file hash and Jellyfin's image tag per collection id.
    """
    images = load_collection_images(directory)
    try:
        with open(state_path) as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}
    collections = {}
    for c in jellyfin.items(["BoxSet"]):
        collections.setdefault(c["Name"].casefold(), []).append(c)
    stats = {"uploaded": 0, "unchanged": 0, "no_collection": 0, "failed": 0}
    new_state = {}
    for key, path in images.items():
        name = os.path.basename(path)
        if key not in collections:
            # The plugin creates a collection only once something matches its expression.
            log.info("collection image %s: no collection by that name yet", name)
            stats["no_collection"] += 1
            continue
        with open(path, "rb") as f:
            data = f.read()
        digest = hashlib.sha256(data).hexdigest()
        for c in collections[key]:
            tag = (c.get("ImageTags") or {}).get("Primary")
            if state.get(c["Id"]) == {"sha256": digest, "tag": tag}:
                new_state[c["Id"]] = state[c["Id"]]
                stats["unchanged"] += 1
                continue
            log.info("collection image %s: %s %s", name, "would set on" if dry_run else "setting on", c["Name"])
            if dry_run:
                stats["uploaded"] += 1
                continue
            try:
                jellyfin.set_primary_image(c["Id"], data, IMAGE_TYPES[os.path.splitext(path)[1].lower()])
                tag = (jellyfin.get_item(c["Id"]).get("ImageTags") or {}).get("Primary")
            except OSError as e:  # HTTPError and connection errors
                # One collection failing must not stop the rest; with no state it is retried next run.
                detail = e.read().decode("utf-8", "replace")[:300] if isinstance(e, urllib.error.HTTPError) else ""
                log.error("collection image %s: setting on %s (%s) failed: %s %s",
                          name, c["Name"], c["Id"], e, detail.strip())
                stats["failed"] += 1
                continue
            stats["uploaded"] += 1
            new_state[c["Id"]] = {"sha256": digest, "tag": tag}
    if not dry_run:
        tmp = state_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(new_state, f)
        os.replace(tmp, state_path)
    log.info("collection images: %s%s", stats, " (dry run)" if dry_run else "")
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
        # On a redeploy this starts alongside Jellyfin, which needs a while (longer when it migrates).
        jellyfin.wait_until_ready(float(os.environ.get("JELLYFIN_WAIT_MINUTES", 20)) * 60)
        source = KeywordSource(
            os.path.join(data_dir, "imdb_keywords.json"),
            sources=kw_cfg.get("sources", ["kometa", "imdb"]),
            kometa_url=os.environ.get("KOMETA_SERVICE_URL", "https://utilities.kometa.wiki/imdb-service"),
            imdb_url=os.environ.get("IMDB_URL", "https://www.imdb.com"),
            cache_days=kw_cfg.get("cache_days", 30),
            request_delay=float(kw_cfg.get("request_delay_seconds", 1.0)),
        )
        ac = dict(cfg.get("auto_collections") or {})
        for key in ("file", "images"):
            if ac.get(key):
                ac[key] = os.path.join(os.path.dirname(os.path.abspath(args.config)), ac[key])
        # Sync collection definitions first so new TAG rules exist before tags are added.
        config_changed = False
        if ac:
            try:
                config_changed = sync_auto_collections(ac, jellyfin, dry_run)
            except (LookupError, urllib.error.HTTPError) as e:
                # Tagging does not need the plugin, so still run it.
                log.error("auto collections: sync skipped: %s", e)
                ac = {}
        stats = run(cfg, jellyfin, source, dry_run)
        task = None
        if ac and not dry_run and (config_changed or stats["changed"]):
            task = refresh_auto_collections(ac, jellyfin)
        if ac.get("images"):
            # Wait for the task so collections it creates this run get their image now, not tomorrow.
            wait = float(ac.get("task_wait_minutes", 30)) * 60
            if task and not jellyfin.wait_for_task(task, wait):
                log.warning("collection images: %r still running after %.0f minutes; setting images anyway",
                            task["Name"], wait / 60)
            try:
                apply_collection_images(ac["images"], jellyfin, os.path.join(data_dir, "collection_images.json"),
                                        dry_run)
            except (OSError, ValueError) as e:  # HTTPError is an OSError; tagging already finished
                log.error("collection images: skipped: %s", e)
        return stats

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
