import copy
import json
import os
import re
import socket
import tempfile
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

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
        self.tasks = [{"Id": "t-scan", "Name": "Scan Media Library", "State": "Idle"},
                      {"Id": "t-ac", "Name": "Auto Collections Update", "State": "Idle",
                       "LastExecutionResult": {"EndTimeUtc": "2026-10-26T03:01:00Z"}}]
        self.started_tasks = []
        self.task_polls = 2    # a started task reports Running this many times before it finishes
        self.on_task_done = None
        self.uploads = []      # image uploads: the enricher must never make one
        self.refreshed = []    # item ids refreshed
        self.refresh_errors = set()  # item ids whose refresh answers 500
        self.collections_dir = None  # local stand-in for Jellyfin's /config/data/collections
        self.not_ready = 0     # answer /health with 503 this many more times

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
            if u.path == "/jf/health":
                if fake.not_ready:
                    fake.not_ready -= 1
                    return self._send(503, b"Unhealthy", "text/plain")
                return self._send(200, b"Healthy", "text/plain")
            if u.path == "/jf/Users":
                return self._send(200, [{"Id": "u-user", "Policy": {"IsAdministrator": False}},
                                        {"Id": "u-admin", "Policy": {"IsAdministrator": True}}])
            if u.path == "/jf/Plugins":
                return self._send(200, fake.plugins)
            if u.path.startswith("/jf/Plugins/"):
                pid = u.path.split("/")[3]
                if any(p["Id"] == pid and p.get("Status", "Active") != "Active" for p in fake.plugins):
                    return self._send(404, None)  # Jellyfin has no instance of a plugin that is not loaded
                return self._send(200, copy.deepcopy(fake.plugin_configs[pid]))
            if u.path == "/jf/ScheduledTasks":
                return self._send(200, fake.tasks)
            if u.path.startswith("/jf/ScheduledTasks/"):
                task = next(t for t in fake.tasks if t["Id"] == u.path.rsplit("/", 1)[1])
                if task["State"] == "Running":
                    task["polls"] -= 1
                    if task["polls"] <= 0:
                        task["State"] = "Idle"
                        task["LastExecutionResult"] = {"EndTimeUtc": f"end-{len(fake.started_tasks)}"}
                        if fake.on_task_done:
                            fake.on_task_done()
                return self._send(200, {k: v for k, v in task.items() if k != "polls"})
            if u.path == "/jf/Items":
                if q.get("userId") != "u-admin":  # Jellyfin 12 returns mostly collections without a user
                    return self._send(200, {"Items": [], "TotalRecordCount": 0})
                types = q["IncludeItemTypes"].split(",")
                allitems = [i for i in fake.items.values() if i["Type"] in types]
                start, limit = int(q["StartIndex"]), int(q["Limit"])
                return self._send(200, {"Items": copy.deepcopy(allitems[start:start + limit]),
                                        "TotalRecordCount": len(allitems)})
            if u.path.startswith("/jf/Items/") and u.path.endswith("/Images"):
                return self._send(200, copy.deepcopy(fake.items[u.path.split("/")[3]].get("ImageInfos", [])))
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
            raw = self.rfile.read(length)
            if "/Images/" in u.path:
                fake.uploads.append(u.path)
                return self._send(500, b"Read-only file system", "text/plain")
            if u.path.endswith("/Refresh"):
                item_id = u.path.split("/")[3]
                if item_id in fake.refresh_errors:
                    return self._send(500, b"Error processing request.", "text/plain")
                fake.refreshed.append(item_id)
                # Like Jellyfin's ItemImageProvider.MergeImages: a poster file in the item's folder
                # becomes its primary image, and nothing is deleted.
                item = fake.items[item_id]
                folder = os.path.join(fake.collections_dir, item["Path"].split("/config/data/collections/", 1)[1])
                posters = sorted(f for f in os.listdir(folder) if f.startswith("poster."))
                if posters:
                    item["ImageInfos"] = [{"ImageType": "Primary", "Path": f"{item['Path']}/{posters[0]}"}]
                return self._send(204)
            body = json.loads(raw) if length else None
            if u.path.startswith("/jf/ScheduledTasks/Running/"):
                task_id = u.path.rsplit("/", 1)[1]
                fake.started_tasks.append(task_id)
                task = next(t for t in fake.tasks if t["Id"] == task_id)
                task["State"], task["polls"] = "Running", fake.task_polls
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

    def ac(self, name, expression, sort_by=2):
        return {"CollectionName": name, "Expression": expression, "CaseSensitive": False, "SortBy": sort_by, "SortOrder": 0}

    def write_ac(self, collections, pairs=()):
        """Write a plugin-format JSON file; returns the auto_collections settings pointing at it."""
        path = os.path.join(self.tmp.name, "ac.json")
        with open(path, "w") as f:
            json.dump({"TitleMatchPairs": list(pairs), "ExpressionCollections": collections}, f)
        return {"file": path, "plugin_name": "auto collections", "task_name": "Auto Collection"}

    def jf(self):
        return enricher.Jellyfin(f"{self.base}/jf", "key")

    def test_sync_replaces_managed_keys_and_keeps_other_settings(self):
        self.fake.plugin_configs["p-ac"]["ExpressionCollections"] = [self.ac("Old", 'TAG "old"')]
        want = [self.ac("Heist Collection", 'TAG "heist"'), self.ac("1950s", 'YEAR ">1949"', sort_by=0)]
        settings = self.write_ac(want)
        self.assertTrue(enricher.sync_auto_collections(settings, self.jf(), dry_run=False))
        cfg = self.fake.plugin_configs["p-ac"]
        self.assertEqual(cfg["SomeOtherSetting"], 7)
        self.assertEqual(cfg["ExpressionCollections"], want)
        # second sync is a no-op
        self.assertFalse(enricher.sync_auto_collections(settings, self.jf(), dry_run=False))

    def test_sync_dry_run_leaves_plugin_untouched(self):
        settings = self.write_ac([self.ac("Heist Collection", 'TAG "heist"')])
        before = copy.deepcopy(self.fake.plugin_configs["p-ac"])
        self.assertTrue(enricher.sync_auto_collections(settings, self.jf(), dry_run=True))
        self.assertEqual(self.fake.plugin_configs["p-ac"], before)

    def test_sync_errors_when_plugin_missing_or_duplicate_names(self):
        self.fake.plugins = [{"Id": "p-other", "Name": "TMDb"}]
        settings = self.write_ac([self.ac("A", 'TAG "a"')])
        with self.assertRaises(LookupError):
            enricher.sync_auto_collections(settings, self.jf(), dry_run=False)
        dup = self.write_ac([self.ac("A", "x"), self.ac("A", "y")])
        with self.assertRaises(ValueError):
            enricher.load_auto_collections(dup["file"])

    def test_sync_uses_the_active_plugin_and_names_the_status_when_none_is(self):
        settings = self.write_ac([self.ac("A", 'TAG "a"')])
        self.fake.plugins = [{"Id": "p-old", "Name": "Auto Collections", "Version": "0.0.7.0", "Status": "NotSupported"},
                             {"Id": "p-ac", "Name": "Auto Collections", "Version": "0.0.9.0", "Status": "Active"}]
        enricher.sync_auto_collections(settings, self.jf(), dry_run=False)
        self.assertEqual(self.fake.plugin_configs["p-ac"]["ExpressionCollections"][0]["CollectionName"], "A")
        self.fake.plugins = [{"Id": "p-old", "Name": "Auto Collections", "Version": "0.0.7.0", "Status": "NotSupported"}]
        with self.assertRaisesRegex(LookupError, "0.0.7.0 is NotSupported"):
            enricher.sync_auto_collections(settings, self.jf(), dry_run=False)

    def write_image(self, name, data=b"\xff\xd8poster"):
        directory = os.path.join(self.tmp.name, "images")
        os.makedirs(directory, exist_ok=True)
        with open(os.path.join(directory, name), "wb") as f:
            f.write(data)
        return directory

    def boxset(self, item_id, name, image=None):
        """A collection with its folder, as the plugin creates it; `image` is its current primary
        image path, e.g. a movie's poster that the plugin borrowed."""
        self.fake.collections_dir = os.path.join(self.tmp.name, "collections")
        os.makedirs(os.path.join(self.fake.collections_dir, f"{name} [boxset]"), exist_ok=True)
        infos = [{"ImageType": "Primary", "Path": image}] if image else []
        self.fake.add(item_id, name, item_type="BoxSet", Path=f"/config/data/collections/{name} [boxset]",
                      ImageInfos=infos)

    def poster(self, name, filename="poster.jpg"):
        path = os.path.join(self.fake.collections_dir, f"{name} [boxset]", filename)
        with open(path, "rb") as f:
            return f.read()

    def apply_images(self, dry_run=False):
        return enricher.apply_collection_images(os.path.join(self.tmp.name, "images"), self.jf(),
                                                os.path.join(self.tmp.name, "collections"), dry_run)

    def test_collection_images_are_written_to_the_folder_and_never_uploaded(self):
        # The plugin pointed the collection at a movie's poster; replacing it must not touch that file.
        self.boxset("c1", "Aviation Collection", image="/media/Movies/Top Gun (1986)/poster.jpg")
        self.boxset("c2", "Heist Collection")
        self.write_image("aviation collection.JPG")  # names and extensions match in any case
        self.write_image("README.md", b"not an image")
        stats = self.apply_images()
        self.assertEqual(stats, {"written": 1, "refreshed": 1, "unchanged": 0, "no_collection": 0, "failed": 0})
        self.assertEqual(self.poster("Aviation Collection"), b"\xff\xd8poster")
        self.assertEqual(self.fake.items["c1"]["ImageInfos"][0]["Path"],
                         "/config/data/collections/Aviation Collection [boxset]/poster.jpg")
        self.assertEqual(self.fake.uploads, [])
        # Second run: file and image already match, so nothing is written or refreshed.
        self.assertEqual(self.apply_images()["unchanged"], 1)
        self.assertEqual(self.fake.refreshed, ["c1"])
        # A changed design is written and refreshed again.
        self.write_image("aviation collection.JPG", b"\xff\xd8new poster")
        self.assertEqual(self.apply_images()["written"], 1)
        self.assertEqual(self.poster("Aviation Collection"), b"\xff\xd8new poster")
        # Something else pointed the collection elsewhere: refresh again, without rewriting the file.
        self.fake.items["c1"]["ImageInfos"] = [{"ImageType": "Primary", "Path": "/media/Movies/X/poster.jpg"}]
        stats = self.apply_images()
        self.assertEqual((stats["written"], stats["refreshed"]), (0, 1))
        self.assertEqual(self.fake.uploads, [])

    def test_collection_images_dry_run_missing_collection_and_format_change(self):
        self.boxset("c1", "Aviation Collection")
        self.write_image("Aviation Collection.jpg")
        self.write_image("Polyamory Collection.webp")
        stats = self.apply_images(dry_run=True)
        self.assertEqual(stats, {"written": 0, "refreshed": 1, "unchanged": 0, "no_collection": 1, "failed": 0})
        self.assertEqual(os.listdir(os.path.join(self.fake.collections_dir, "Aviation Collection [boxset]")), [])
        self.assertEqual(self.fake.refreshed, [])
        self.apply_images()
        os.remove(os.path.join(self.tmp.name, "images", "Aviation Collection.jpg"))
        self.write_image("Aviation Collection.png", b"png")
        self.apply_images()  # the old poster.jpg is removed so it cannot compete with poster.png
        self.assertEqual(sorted(os.listdir(os.path.join(self.fake.collections_dir, "Aviation Collection [boxset]"))),
                         ["poster.png"])

    def test_one_failing_collection_does_not_stop_the_rest(self):
        for i, name in enumerate(["1980's Movies", "1990's Movies", "2000's Movies"]):
            self.boxset(f"c{i}", name)
            self.write_image(f"{name}.jpg")
        self.fake.refresh_errors = {"c1"}
        with self.assertLogs(level="ERROR") as logs:
            stats = self.apply_images()
        self.assertEqual(stats["failed"], 1)
        self.assertEqual(sorted(self.fake.refreshed), ["c0", "c2"])
        self.assertIn("1990's Movies (c1) failed: HTTP Error 500", "\n".join(logs.output))
        self.fake.refresh_errors = set()  # the failed one is retried next run; the others are unchanged
        stats = self.apply_images()
        self.assertEqual((stats["refreshed"], stats["unchanged"], stats["failed"]), (1, 2, 0))

    def test_collection_outside_the_collections_folder_is_refused(self):
        self.boxset("c1", "Aviation Collection")
        self.fake.items["c1"]["Path"] = "/media/Movies/Top Gun (1986)"
        self.boxset("c2", "Heist Collection")
        self.fake.items["c2"]["Path"] = "/config/data/collections/../../../media/Movies"
        self.write_image("Aviation Collection.jpg")
        self.write_image("Heist Collection.jpg")
        with self.assertLogs(level="ERROR"):
            self.assertEqual(self.apply_images()["failed"], 2)
        self.assertEqual((self.fake.refreshed, self.fake.uploads), ([], []))

    def test_two_images_for_one_collection_is_an_error(self):
        self.write_image("Aviation Collection.png")
        self.write_image("aviation collection.jpg")
        with self.assertRaisesRegex(ValueError, "two images"):
            self.apply_images()

    def run_main(self, dry_run, images=None):
        self.write_ac([self.ac("Heist Collection", 'TAG "heist"')])
        cfg_path = os.path.join(self.tmp.name, "config.yaml")
        ac = {"file": "ac.json", "task_name": "Auto Collection"}
        if images:
            ac["images"] = images
        with open(cfg_path, "w") as f:
            yaml.safe_dump(dict(self.cfg, auto_collections=ac,
                                imdb_keywords={"sources": ["kometa"], "request_delay_seconds": 0}), f)
        env = {"JELLYFIN_APIKEY": "key", "JELLYFIN_URL": f"{self.base}/jf", "KOMETA_SERVICE_URL": f"{self.base}/kometa",
               "DATA_DIR": self.tmp.name, "DRY_RUN": "false",  # --dry-run still overrides
               "COLLECTIONS_DIR": os.path.join(self.tmp.name, "collections")}
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

    def test_main_still_tags_when_the_plugin_is_not_active(self):
        self.fake.plugins = [{"Id": "p-ac", "Name": "Auto Collections", "Version": "0.0.7.0", "Status": "NotSupported"}]
        self.fake.add("1", "Heat", "tt0113277")
        self.fake.kometa["tt0113277"] = {"keywords": {"heist": [1, 1]}}
        with self.assertLogs(level="ERROR") as logs:
            self.run_main(dry_run=False)
        self.assertIn("0.0.7.0 is NotSupported", "\n".join(logs.output))
        self.assertEqual(self.fake.items["1"]["Tags"], ["heist"])
        self.assertEqual(self.fake.started_tasks, [])

    def test_main_dry_run_starts_nothing(self):
        self.fake.add("1", "Heat", "tt0113277")
        self.fake.kometa["tt0113277"] = {"keywords": {"heist": [1, 1]}}
        self.run_main(dry_run=True)
        self.assertEqual(self.fake.started_tasks, [])
        self.assertEqual(self.fake.plugin_configs["p-ac"]["ExpressionCollections"], [])

    def test_main_sets_images_on_collections_the_task_creates(self):
        self.fake.add("1", "Heat", "tt0113277")
        self.fake.kometa["tt0113277"] = {"keywords": {"heist": [1, 1]}}
        self.fake.on_task_done = lambda: self.boxset("c1", "Heist Collection")
        self.write_image("Heist Collection.jpg")
        with mock.patch("enricher.time.sleep") as sleep:
            self.run_main(dry_run=False, images="images")
        self.assertEqual(self.fake.started_tasks, ["t-ac"])
        self.assertGreaterEqual(sleep.call_count, 2)  # polled the task until it finished
        self.assertEqual(self.fake.refreshed, ["c1"])

    def test_main_sets_images_without_a_task_and_survives_a_missing_folder(self):
        self.boxset("c1", "Heist Collection")
        self.fake.plugin_configs["p-ac"]["ExpressionCollections"] = [self.ac("Heist Collection", 'TAG "heist"')]
        self.write_image("Heist Collection.jpg")
        self.run_main(dry_run=False, images="images")  # nothing to sync or tag, so no task is started
        self.assertEqual(self.fake.started_tasks, [])
        self.assertEqual(self.fake.refreshed, ["c1"])
        with self.assertLogs(level="ERROR") as logs:
            self.run_main(dry_run=False, images="no-such-folder")
        self.assertIn("collection images: skipped", "\n".join(logs.output))

    def test_main_waits_for_jellyfin_to_be_ready(self):
        self.fake.add("1", "Heat", "tt0113277")
        self.fake.kometa["tt0113277"] = {"keywords": {"heist": [1, 1]}}
        self.fake.not_ready = 3
        with mock.patch("enricher.time.sleep") as sleep:
            self.run_main(dry_run=False)
        self.assertEqual(self.fake.not_ready, 0)
        self.assertGreaterEqual(sleep.call_count, 3)
        self.assertEqual(self.fake.items["1"]["Tags"], ["heist"])

    def test_wait_gives_up_when_jellyfin_never_answers(self):
        with socket.socket() as s:  # a port nothing listens on: connection refused
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        jf = enricher.Jellyfin(f"http://127.0.0.1:{port}", "key")
        with self.assertRaises(TimeoutError):
            jf.wait_until_ready(timeout=0.2, interval=0.05)

    def test_shipped_auto_collections_json_is_importable_and_covers_every_enricher_tag(self):
        with open(os.path.join(HERE, "auto-collections.json")) as f:
            raw = json.load(f)
        self.assertEqual(set(raw), {"TitleMatchPairs", "ExpressionCollections"})  # plugin export shape
        for c in raw["ExpressionCollections"]:
            self.assertEqual(set(c), {"CollectionName", "Expression", "CaseSensitive", "SortBy", "SortOrder"}, c)
        desired = enricher.load_auto_collections(os.path.join(HERE, "auto-collections.json"))
        self.assertGreaterEqual(len(desired["ExpressionCollections"]), 135)
        expr_tags = set()
        for c in desired["ExpressionCollections"]:
            expr_tags |= {t.casefold() for t in re.findall(r'TAG "([^"]+)"', c["Expression"])}
        with open(os.path.join(HERE, "config.yaml")) as f:
            cfg = yaml.safe_load(f)
        rule_tags = {t.casefold() for r in cfg["rules"] for t in r["add"].get("tags", [])}
        self.assertEqual(rule_tags - expr_tags, set(), "enricher adds tags no collection uses")

    def test_shipped_collection_images_name_shipped_collections(self):
        with open(os.path.join(HERE, "config.yaml")) as f:
            folder = os.path.join(HERE, yaml.safe_load(f)["auto_collections"]["images"])
        names = {c["CollectionName"].casefold() for c in
                 enricher.load_auto_collections(os.path.join(HERE, "auto-collections.json"))["ExpressionCollections"]}
        images = enricher.load_collection_images(folder)  # also fails on two images for one collection
        self.assertEqual(sorted(set(images) - names), [], "images for collections not in auto-collections.json")

    def test_shipped_config_is_valid(self):
        with open(os.path.join(HERE, "config.yaml")) as f:
            cfg = yaml.safe_load(f)
        rules = [enricher.Rule(r, cfg.get("defaults", {})) for r in cfg["rules"]]
        self.assertGreater(len(rules), 40)
        self.assertTrue(rules[0].matches("Movie", {"bank robbery": (0, 0)}))

    def test_shipped_config_on_real_keywords(self):
        # Excerpts of real Kometa keyword data (2026-10-26) for titles the first run mis-tagged.
        with open(os.path.join(HERE, "config.yaml")) as f:
            cfg = yaml.safe_load(f)
        rules = [enricher.Rule(r, cfg.get("defaults", {})) for r in cfg["rules"]]

        def tags(keywords):
            return {t for r in rules if r.matches("Movie", keywords) for t in r.add["Tags"]}

        lost_in_space = {"spaceship": (3, 3), "robot": (4, 5), "alien": (1, 1), "spy": (0, 0),
                         "assassin": (0, 0), "doctor": (0, 0), "time travel": (0, 0)}
        self.assertEqual(tags(lost_in_space), {"space", "alien", "time travel"})
        nosferatu = {"vampire": (8, 11), "christmas": (0, 1), "grindhouse": (0, 0),
                     "folk horror": (0, 0), "doctor": (0, 0)}
        self.assertEqual(tags(nosferatu), {"vampire"})
        # Unvoted keywords still count: most keywords, and every keyword on old films, have no votes.
        shriek_in_the_night = {"serial killer": (0, 0), "revenge": (0, 0), "lawyer": (0, 0)}
        self.assertEqual(tags(shriek_in_the_night), {"serial killer", "revenge"})
        self.assertEqual(tags({"body horror": (0, 0), "independent film": (1, 2)}),
                         {"body horror", "independent film"})
        self.assertEqual(tags({"gay": (9, 9), "based on novel": (1, 1)}), {"gay", "lgbt", "based on book"})
        self.assertEqual(tags({"trans woman": (0, 0)}), {"trans", "lgbt"})
        vicky_cristina_barcelona = {"polyamorous relationship": (3, 3), "polyamory": (3, 4), "bisexual": (1, 3)}
        self.assertEqual(tags(vicky_cristina_barcelona), {"polyamory"})  # bisexual voted down
        self.assertEqual(tags({"menage a trois": (0, 0), "open marriage": (2, 2)}), set())
        species = {"lesbian": (3, 6), "body horror": (0, 0), "hitman": (2, 2)}  # 2026-10-27
        self.assertEqual(tags(species), {"body horror", "assassin"})  # an even split is not enough for lesbian
        self.assertIn("lesbian", tags({"lesbian": (4, 6)}))
        # Aviation (excerpts, 2026-10-27): planes as the main topic, not a plane in one scene.
        self.assertIn("aviation", tags({"air traffic controller": (3, 3), "airplane": (1, 1)}))  # Pushing Tin
        self.assertIn("aviation", tags({"airplane": (3, 3), "flight attendant": (0, 0)}))  # Snakes on a Plane
        self.assertIn("aviation", tags({"airplane crash": (5, 5), "pilot": (4, 4)}))  # Flight
        self.assertNotIn("aviation", tags({"pilot": (0, 0), "planet": (0, 0)}))  # Lost in Space
        self.assertNotIn("aviation", tags({"airplane hijacking": (1, 3), "airplane": (0, 1)}))
        self.assertNotIn("aviation", tags({"airplane crash": (2, 2), "airplane": (1, 1)}))
        # Tentacles (excerpts, 2026-10-27): Deep Rising, The Thing; not an octopus in passing.
        self.assertIn("tentacles", tags({"tentacle": (2, 2), "squid": (0, 0), "kraken": (0, 0)}))
        self.assertIn("tentacles", tags({"tentacles": (0, 0), "tentacle": (0, 0)}))
        self.assertNotIn("tentacles", tags({"octopus": (1, 1), "squid": (0, 0)}))
        self.assertIn("dinosaur", tags({"tyrannosaurus rex": (2, 2), "triceratops": (1, 1)}))  # King Kong (2005)


if __name__ == "__main__":
    unittest.main()
