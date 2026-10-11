import copy
import json
import os
import re
import tempfile
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import yaml

import enricher

HERE = os.path.dirname(os.path.abspath(__file__))


class Fake:
    """In-process stand-in for Jellyfin, the Kometa keyword service and IMDb keyword pages."""

    def __init__(self):
        self.items = {}
        self.kometa = {}       # imdb id -> {"keywords": {...}} ; missing -> 404
        self.kometa_down = False
        self.imdb_pages = {}   # imdb id -> keyword list for __NEXT_DATA__
        self.posts = []
        self.requests = []
        self.plugins = [{"Id": "p-other", "Name": "TMDb"}, {"Id": "p-ac", "Name": "Auto Collections"}]
        self.plugin_configs = {"p-ac": {"TitleMatchPairs": [], "ExpressionCollections": [], "SomeOtherSetting": 7}}
        self.tasks = [{"Id": "t-scan", "Name": "Scan Media Library"}, {"Id": "t-ac", "Name": "Auto Collections Update"}]
        self.started_tasks = []

    def add(self, item_id, name, imdb=None, item_type="Movie", tags=None, **extra):
        self.items[item_id] = {"Id": item_id, "Name": name, "Type": item_type,
                               "ProviderIds": {"Imdb": imdb} if imdb else {},
                               "Tags": tags or [], "Genres": [], "Overview": f"about {name}", **extra}


def make_handler(fake):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body=None, ctype="application/json"):
            data = body if isinstance(body, bytes) else (json.dumps(body).encode() if body is not None else b"")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            q = dict(urllib.parse.parse_qsl(u.query))
            fake.requests.append(u.path)
            if u.path.startswith("/jf/"):
                assert self.headers["Authorization"] == 'MediaBrowser Token="key"'
            if u.path == "/jf/Users":
                return self._send(200, [{"Id": "u-user", "Policy": {"IsAdministrator": False}},
                                        {"Id": "u-admin", "Policy": {"IsAdministrator": True}}])
            if u.path == "/jf/Plugins":
                return self._send(200, fake.plugins)
            if u.path.startswith("/jf/Plugins/"):
                return self._send(200, copy.deepcopy(fake.plugin_configs[u.path.split("/")[3]]))
            if u.path == "/jf/ScheduledTasks":
                return self._send(200, fake.tasks)
            if u.path == "/jf/Items":
                types = q["IncludeItemTypes"].split(",")
                allitems = [i for i in fake.items.values() if i["Type"] in types]
                start, limit = int(q["StartIndex"]), int(q["Limit"])
                return self._send(200, {"Items": copy.deepcopy(allitems[start:start + limit]),
                                        "TotalRecordCount": len(allitems)})
            if u.path.startswith("/jf/Items/"):
                assert q.get("userId") == "u-admin"
                return self._send(200, copy.deepcopy(fake.items[u.path.rsplit("/", 1)[1]]))
            if u.path.startswith("/kometa/keywords/"):
                if fake.kometa_down:
                    return self._send(500, {"error": "down"})
                imdb = u.path.rsplit("/", 1)[1]
                return self._send(200, fake.kometa[imdb]) if imdb in fake.kometa else self._send(404, {})
            if u.path.startswith("/imdb/title/"):
                imdb = u.path.split("/")[3]
                nodes = [{"node": {"keyword": {"text": {"text": k}}, "interestScore": {"usersInterested": r, "usersVoted": t}}}
                         for k, r, t in fake.imdb_pages.get(imdb, [])]
                nd = json.dumps({"props": {"pageProps": {"contentData": {"data": {"title": {"keywords": {"edges": nodes}}}}}}})
                html = f'<html><script id="__NEXT_DATA__" type="application/json">{nd}</script></html>'
                return self._send(200, html.encode(), "text/html")
            self._send(404, {})

        def do_POST(self):
            u = urllib.parse.urlparse(self.path)
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length)) if length else None
            if u.path.startswith("/jf/ScheduledTasks/Running/"):
                fake.started_tasks.append(u.path.rsplit("/", 1)[1])
                return self._send(204)
            if u.path.startswith("/jf/Plugins/"):
                fake.plugin_configs[u.path.split("/")[3]] = body
                return self._send(204)
            fake.posts.append((u.path, body))
            fake.items[u.path.rsplit("/", 1)[1]] = body
            self._send(204)

    return H


class EnricherTest(unittest.TestCase):
    def setUp(self):
        self.fake = Fake()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.fake))
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = {"item_types": ["Movie", "Series"], "rules": [
            {"match": {"imdb_keywords": ["heist", "bank-robbery"]}, "add": {"tags": ["heist"]}},
            {"match": {"imdb_keywords": ["vampire"], "min_votes": 3}, "add": {"tags": ["vampire"], "genres": ["Horror"]}},
        ]}

    def tearDown(self):
        self.server.shutdown()
        self.tmp.cleanup()

    def run_once(self, dry_run=False, sources=("kometa", "imdb"), cfg=None):
        jf = enricher.Jellyfin(f"{self.base}/jf", "key")
        src = enricher.KeywordSource(os.path.join(self.tmp.name, "cache.json"), list(sources),
                                     f"{self.base}/kometa", f"{self.base}/imdb", cache_days=30, request_delay=0)
        return enricher.run(cfg or self.cfg, jf, src, dry_run)

    def test_adds_tags_additively_and_preserves_other_fields(self):
        self.fake.add("1", "Ocean's Eleven", "tt0240772", tags=["Favourite"])
        self.fake.kometa["tt0240772"] = {"keywords": {"Bank Robbery": [10, 12], "casino": [5, 5]}}
        self.run_once()
        self.assertEqual(len(self.fake.posts), 1)
        path, body = self.fake.posts[0]
        self.assertEqual(path, "/jf/Items/1")
        self.assertEqual(body["Tags"], ["Favourite", "heist"])
        self.assertEqual(body["Overview"], "about Ocean's Eleven")  # full DTO sent back untouched

    def test_existing_tag_any_case_means_no_write(self):
        self.fake.add("1", "Heat", "tt0113277", tags=["Heist"])
        self.fake.kometa["tt0113277"] = {"keywords": {"heist": [1, 1]}}
        stats = self.run_once()
        self.assertEqual(self.fake.posts, [])
        self.assertEqual(stats["changed"], 0)

    def test_dry_run_writes_nothing(self):
        self.fake.add("1", "Heat", "tt0113277")
        self.fake.kometa["tt0113277"] = {"keywords": {"heist": [1, 1]}}
        stats = self.run_once(dry_run=True)
        self.assertEqual(self.fake.posts, [])
        self.assertEqual(stats["changed"], 1)

    def test_vote_threshold_and_genres(self):
        self.fake.add("1", "Low votes", "tt1")
        self.fake.add("2", "Enough votes", "tt2")
        self.fake.kometa["tt1"] = {"keywords": {"vampire": [1, 2]}}
        self.fake.kometa["tt2"] = {"keywords": {"vampire": [3, 4]}}
        self.run_once()
        self.assertEqual([p for p, _ in self.fake.posts], ["/jf/Items/2"])
        self.assertEqual(self.fake.items["2"]["Tags"], ["vampire"])
        self.assertEqual(self.fake.items["2"]["Genres"], ["Horror"])

    def test_falls_back_to_imdb_page_when_service_down(self):
        self.fake.kometa_down = True
        self.fake.add("1", "Inside Man", "tt0454848")
        self.fake.imdb_pages["tt0454848"] = [("bank heist", 0, 0), ("heist", 7, 9)]
        self.run_once()
        self.assertEqual(self.fake.items["1"]["Tags"], ["heist"])

    def test_cache_avoids_second_lookup_and_failures_are_not_cached(self):
        self.fake.add("1", "Heat", "tt0113277")
        self.fake.add("2", "Unknown", "tt9")
        self.fake.kometa["tt0113277"] = {"keywords": {"heist": [1, 1]}}
        self.run_once(sources=("kometa",))
        self.fake.kometa_down = True  # tt9 was a 404 (cached as empty); tt0113277 is cached
        self.fake.requests.clear()
        self.run_once(sources=("kometa",))
        self.assertFalse([r for r in self.fake.requests if r.startswith("/kometa/")])

    def test_skips_items_without_imdb_and_pages_through_library(self):
        for i in range(1203):
            self.fake.add(str(i), f"m{i}", None)
        self.fake.add("x", "Heat", "tt0113277", item_type="Series")
        self.fake.kometa["tt0113277"] = {"keywords": {"heist": [1, 1]}}
        stats = self.run_once()
        self.assertEqual(stats["items"], 1204)
        self.assertEqual(stats["no_imdb"], 1203)
        self.assertEqual(self.fake.items["x"]["Tags"], ["heist"])

    def test_lookup_budget(self):
        for i in range(5):
            self.fake.add(str(i), f"m{i}", f"tt{i}")
        cfg = dict(self.cfg, max_lookups_per_run=2)
        stats = self.run_once(cfg=cfg)
        self.assertEqual(stats["skipped_lookups"], 3)

    def write_ac(self, collections, pairs=()):
        path = os.path.join(self.tmp.name, "ac.yaml")
        with open(path, "w") as f:
            yaml.safe_dump({"plugin": {"name": "auto collections", "task_name": "Auto Collection"},
                            "expression_defaults": {"CaseSensitive": False, "SortBy": 2, "SortOrder": 0},
                            "TitleMatchPairs": list(pairs), "ExpressionCollections": collections}, f)
        return path

    def jf(self):
        return enricher.Jellyfin(f"{self.base}/jf", "key")

    def test_sync_replaces_managed_keys_and_keeps_other_settings(self):
        self.fake.plugin_configs["p-ac"]["ExpressionCollections"] = [
            {"CollectionName": "Old", "Expression": 'TAG "old"', "CaseSensitive": False, "SortBy": 2, "SortOrder": 0}]
        path = self.write_ac([{"CollectionName": "Heist Collection", "Expression": 'TAG "heist"'},
                              {"CollectionName": "1950s", "Expression": 'YEAR ">1949"', "SortBy": 0}])
        self.assertTrue(enricher.sync_auto_collections(path, self.jf(), dry_run=False))
        cfg = self.fake.plugin_configs["p-ac"]
        self.assertEqual(cfg["SomeOtherSetting"], 7)
        self.assertEqual(cfg["ExpressionCollections"], [
            {"CollectionName": "Heist Collection", "Expression": 'TAG "heist"', "CaseSensitive": False, "SortBy": 2, "SortOrder": 0},
            {"CollectionName": "1950s", "Expression": 'YEAR ">1949"', "CaseSensitive": False, "SortBy": 0, "SortOrder": 0}])
        # second sync is a no-op
        self.assertFalse(enricher.sync_auto_collections(path, self.jf(), dry_run=False))

    def test_sync_dry_run_leaves_plugin_untouched(self):
        path = self.write_ac([{"CollectionName": "Heist Collection", "Expression": 'TAG "heist"'}])
        before = copy.deepcopy(self.fake.plugin_configs["p-ac"])
        self.assertTrue(enricher.sync_auto_collections(path, self.jf(), dry_run=True))
        self.assertEqual(self.fake.plugin_configs["p-ac"], before)

    def test_sync_errors_when_plugin_missing_or_duplicate_names(self):
        self.fake.plugins = [{"Id": "p-other", "Name": "TMDb"}]
        path = self.write_ac([{"CollectionName": "A", "Expression": 'TAG "a"'}])
        with self.assertRaises(LookupError):
            enricher.sync_auto_collections(path, self.jf(), dry_run=False)
        dup = self.write_ac([{"CollectionName": "A", "Expression": "x"}, {"CollectionName": "A", "Expression": "y"}])
        with self.assertRaises(ValueError):
            enricher.load_auto_collections(dup)

    def run_main(self, dry_run):
        self.write_ac([{"CollectionName": "Heist Collection", "Expression": 'TAG "heist"'}])
        cfg_path = os.path.join(self.tmp.name, "config.yaml")
        with open(cfg_path, "w") as f:
            yaml.safe_dump(dict(self.cfg, auto_collections="ac.yaml",
                                imdb_keywords={"sources": ["kometa"], "request_delay_seconds": 0}), f)
        env = {"JELLYFIN_APIKEY": "key", "JELLYFIN_URL": f"{self.base}/jf", "KOMETA_SERVICE_URL": f"{self.base}/kometa",
               "DATA_DIR": self.tmp.name, "DRY_RUN": "false"}  # --dry-run still overrides
        old = {k: os.environ.get(k) for k in [*env, "RUN_AT"]}
        os.environ.update(env)
        os.environ.pop("RUN_AT", None)
        try:
            enricher.main(["--config", cfg_path, "--once"] + (["--dry-run"] if dry_run else []))
        finally:
            for k, v in old.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)

    def test_main_syncs_tags_then_starts_plugin_task(self):
        self.fake.add("1", "Heat", "tt0113277")
        self.fake.kometa["tt0113277"] = {"keywords": {"heist": [1, 1]}}
        self.run_main(dry_run=False)
        self.assertEqual(self.fake.items["1"]["Tags"], ["heist"])
        self.assertEqual(self.fake.plugin_configs["p-ac"]["ExpressionCollections"][0]["CollectionName"], "Heist Collection")
        self.assertEqual(self.fake.started_tasks, ["t-ac"])

    def test_main_dry_run_starts_nothing(self):
        self.fake.add("1", "Heat", "tt0113277")
        self.fake.kometa["tt0113277"] = {"keywords": {"heist": [1, 1]}}
        self.run_main(dry_run=True)
        self.assertEqual(self.fake.started_tasks, [])
        self.assertEqual(self.fake.plugin_configs["p-ac"]["ExpressionCollections"], [])

    def test_shipped_auto_collections_cover_every_enricher_tag(self):
        _, desired = enricher.load_auto_collections(os.path.join(HERE, "auto-collections.yaml"))
        self.assertGreaterEqual(len(desired["ExpressionCollections"]), 55)
        expr_tags = set()
        for c in desired["ExpressionCollections"]:
            expr_tags |= {t.casefold() for t in re.findall(r'TAG "([^"]+)"', c["Expression"])}
        with open(os.path.join(HERE, "config.yaml")) as f:
            cfg = yaml.safe_load(f)
        rule_tags = {t.casefold() for r in cfg["rules"] for t in r["add"].get("tags", [])}
        self.assertEqual(rule_tags - expr_tags, set(), "enricher adds tags no collection uses")

    def test_shipped_config_is_valid(self):
        with open(os.path.join(HERE, "config.yaml")) as f:
            cfg = yaml.safe_load(f)
        rules = [enricher.Rule(r, cfg.get("defaults", {})) for r in cfg["rules"]]
        self.assertGreater(len(rules), 40)
        self.assertTrue(rules[0].matches("Movie", {"bank robbery": (0, 0)}))


if __name__ == "__main__":
    unittest.main()
