"""Keep the Tandoor shopping list and a Home Assistant to-do list the same, in both directions.

Each cycle reads both lists, compares them with the pairs it saved at the end of the last cycle,
and copies the changes: new items, check-offs, un-checks, renames, and deletions. The saved pairs
are what stop loops: an item this script made is already paired, so the next cycle does not see it
as new. See README.md.
"""

import argparse
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

log = logging.getLogger("shopping-sync")


class ApiError(Exception):
    pass


def http_json(url, method="GET", headers=None, body=None, timeout=30):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=dict(headers or {}))
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise ApiError(f"{method} {url}: HTTP {e.code} {e.read()[:300]!r}") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ApiError(f"{method} {url}: {e}") from e
    return json.loads(raw) if raw else {}


def entry_text(entry):
    """The text of a Tandoor entry, in the same form as Tandoor's own Home Assistant connector:
    "Milk (2 l)", or "Milk" with no amount."""
    text = ((entry.get("food") or {}).get("name") or "").strip()
    amount = float(entry.get("amount") or 0)
    if amount:
        unit = (entry.get("unit") or {}).get("name")
        number = f"{amount:.2f}".rstrip("0").rstrip(".")
        text += f" ({number} {unit})" if unit else f" ({number})"
    return text


def key(text):
    return " ".join(text.split()).casefold()


class Tandoor:
    def __init__(self, url, token, host=None):
        self.url = url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        if host:
            # Django checks the Host header against ALLOWED_HOSTS. On 127.0.0.1 the header
            # would be 127.0.0.1, so send Tandoor's tailnet name.
            self.headers["Host"] = host

    def _call(self, path, method="GET", body=None):
        return http_json(self.url + path, method=method, headers=self.headers, body=body)

    def items(self):
        """{id: {"text", "done"}}. The list endpoint returns unchecked entries and checked
        entries of the last few days (the user's "recent days" setting), not older ones."""
        out = {}
        path = "/api/shopping-list-entry/?page_size=200"
        while path:
            page = self._call(path)
            if page is None:
                raise ApiError("Tandoor: no shopping list endpoint")
            results = page.get("results", page) if isinstance(page, dict) else page
            for e in results:
                out[e["id"]] = {"text": entry_text(e), "done": bool(e.get("checked"))}
            nxt = page.get("next") if isinstance(page, dict) else None
            path = urllib.parse.urlsplit(nxt)._replace(scheme="", netloc="").geturl() if nxt else None
        return out

    def get(self, entry_id):
        e = self._call(f"/api/shopping-list-entry/{entry_id}/")
        return None if e is None else {"text": entry_text(e), "done": bool(e.get("checked"))}

    def add(self, text):
        e = self._call("/api/shopping-list-entry/", "POST", {"food": {"name": text}, "amount": 0, "unit": None})
        return e["id"]

    def set_done(self, entry_id, done):
        self._call(f"/api/shopping-list-entry/{entry_id}/", "PATCH", {"checked": done})

    def delete(self, entry_id):
        self._call(f"/api/shopping-list-entry/{entry_id}/", "DELETE")


class HomeAssistant:
    def __init__(self, url, token, entity_id):
        self.url = url.rstrip("/")
        self.entity_id = entity_id
        self.headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    def _service(self, service, data, response=False):
        path = f"/api/services/todo/{service}" + ("?return_response" if response else "")
        return http_json(self.url + path, "POST", self.headers, {"entity_id": self.entity_id, **data})

    def items(self):
        """{uid: {"text", "done"}}."""
        r = self._service("get_items", {}, response=True)
        if r is None:
            raise ApiError(f"Home Assistant: no to-do list {self.entity_id}")
        items = r["service_response"][self.entity_id]["items"]
        return {i["uid"]: {"text": i["summary"], "done": i["status"] == "completed"} for i in items}

    def add(self, text):
        self._service("add_item", {"item": text})

    def set_done(self, uid, done):
        self._service("update_item", {"item": uid, "status": "completed" if done else "needs_action"})

    def rename(self, uid, text):
        self._service("update_item", {"item": uid, "rename": text})

    def delete(self, uid):
        self._service("remove_item", {"item": uid})


def sync(tandoor, ha, pairs, dry_run=False):
    """One cycle. `pairs` is the saved state: a list of {"t": Tandoor id, "h": HA uid, "text",
    "done"}, as both sides were at the end of the last cycle. Returns the new pairs.

    Both lists are read before anything is written; if a read fails, the cycle stops with no
    change, so a dead API never looks like an empty list.
    """
    T = tandoor.items()
    H = ha.items()
    def do(what, label, fn, *args):
        log.info("%s%s %r", "dry run: " if dry_run else "", what, label)
        return None if dry_run else fn(*args)

    kept, added_to_ha = [], []
    for p in pairs:
        t, h = T.get(p["t"]), H.get(p["h"])
        if t is None and not (p["done"] and h is not None and h["done"]):
            # Not in the list: deleted, or checked long enough ago that the list leaves it out.
            # Only the entry itself tells. (A pair done on both sides is left alone: it is old.)
            t = tandoor.get(p["t"])
        elif t is None:
            t = {"text": p["text"], "done": True}
        if t is None and h is None:
            continue
        if t is None:
            do("Tandoor deleted; remove from Home Assistant:", p["text"], ha.delete, p["h"])
            continue
        if h is None:
            if not (p["done"] and t["done"]):
                do("Home Assistant removed; delete in Tandoor:", p["text"], tandoor.delete, p["t"])
            continue  # A done item cleared in Home Assistant stays in Tandoor's history.
        q = dict(p)
        if t["done"] != p["done"] and h["done"] == p["done"]:
            do("Tandoor checked/unchecked; copy to Home Assistant:", p["text"], ha.set_done, p["h"], t["done"])
        elif h["done"] != p["done"] and t["done"] == p["done"]:
            do("Home Assistant checked/unchecked; copy to Tandoor:", p["text"], tandoor.set_done, p["t"], h["done"])
            t = dict(t, done=h["done"])
        q["done"] = t["done"]
        # Compared as keys: spaces and case do not count (the first run pairs by key too).
        if key(t["text"]) != key(p["text"]):
            do("Tandoor changed the text; rename in Home Assistant:", t["text"], ha.rename, p["h"], t["text"])
            q["text"] = t["text"]
        elif key(h["text"]) != key(p["text"]):
            # A Tandoor entry is a food, an amount and a unit. Renaming the food would rename it
            # in every recipe, so the entry is replaced with one for the new text.
            new_id = do("Home Assistant renamed; replace the Tandoor entry:", h["text"], tandoor.add, h["text"])
            do("  and delete the old entry:", p["text"], tandoor.delete, p["t"])
            if h["done"] and new_id is not None:
                tandoor.set_done(new_id, True)
            q.update(t=new_id if new_id is not None else p["t"], text=h["text"])
        kept.append(q)

    paired_t = {p["t"] for p in kept} | {p["t"] for p in pairs}
    paired_h = {p["h"] for p in kept} | {p["h"] for p in pairs}
    new_t = {i: v for i, v in T.items() if i not in paired_t and not v["done"]}
    new_h = {u: v for u, v in H.items() if u not in paired_h and not v["done"]}

    # The same text on both sides with no pair (the first run, or items added on both sides
    # in the same minute): pair them, do not copy.
    by_text = {}
    for u, v in new_h.items():
        by_text.setdefault(key(v["text"]), []).append(u)
    for i in list(new_t):
        us = by_text.get(key(new_t[i]["text"]))
        if us:
            u = us.pop(0)
            kept.append({"t": i, "h": u, "text": new_t[i]["text"], "done": False})
            del new_t[i], new_h[u]

    for i, v in new_t.items():
        do("New in Tandoor; add to Home Assistant:", v["text"], ha.add, v["text"])
        added_to_ha.append((i, v["text"]))
    for u, v in new_h.items():
        new_id = do("New in Home Assistant; add to Tandoor:", v["text"], tandoor.add, v["text"])
        if new_id is not None:
            kept.append({"t": new_id, "h": u, "text": v["text"], "done": False})

    if added_to_ha and not dry_run:
        # add_item returns no uid: read the list again and take the new items by their text.
        known = {p["h"] for p in kept}
        fresh = {}
        for u, v in ha.items().items():
            if u not in known and u not in H:
                fresh.setdefault(key(v["text"]), []).append(u)
        for i, text in added_to_ha:
            us = fresh.get(key(text))
            if us:
                kept.append({"t": i, "h": us.pop(0), "text": text, "done": False})
            else:
                log.warning("could not find the new Home Assistant item %r; it pairs by text next cycle", text)
    return kept


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save(path, pairs):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(pairs, f, indent=1)
    os.replace(tmp, path)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--once", action="store_true", help="run one cycle and exit")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    env = os.environ
    missing = [k for k in ("TANDOOR_URL", "TANDOOR_TOKEN", "HA_URL", "HA_TOKEN") if not env.get(k)]
    if missing:
        log.error("missing environment variables: %s", ", ".join(missing))
        return 2
    tandoor = Tandoor(env["TANDOOR_URL"], env["TANDOOR_TOKEN"], env.get("TANDOOR_HOST"))
    ha = HomeAssistant(env["HA_URL"], env["HA_TOKEN"], env.get("HA_TODO_ENTITY", "todo.shopping_list"))
    state = env.get("STATE_FILE", "/data/pairs.json")
    interval = int(env.get("SYNC_INTERVAL", "60"))
    dry_run = env.get("DRY_RUN", "true").lower() != "false"
    if dry_run:
        log.info("DRY_RUN: logging the changes only; set DRY_RUN=false to write")
    while True:
        try:
            pairs = sync(tandoor, ha, load(state), dry_run=dry_run)
            if not dry_run:
                save(state, pairs)
        except ApiError as e:
            log.error("cycle skipped, nothing changed: %s", e)
        if args.once:
            return 0
        time.sleep(interval)


if __name__ == "__main__":
    sys.exit(main())
