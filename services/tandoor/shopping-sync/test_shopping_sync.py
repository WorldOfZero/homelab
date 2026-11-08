import itertools
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import shopping_sync as ss


class FakeTandoor:
    def __init__(self):
        self.e = {}  # id -> {"text", "done", "old"}; "old" entries are not in the list endpoint
        self.ids = itertools.count(100)
        self.writes = 0
        self.fail = False

    def items(self):
        if self.fail:
            raise ss.ApiError("down")
        return {i: {"text": v["text"], "done": v["done"]} for i, v in self.e.items() if not v.get("old")}

    def get(self, i):
        v = self.e.get(i)
        return None if v is None else {"text": v["text"], "done": v["done"]}

    def add(self, text):
        self.writes += 1
        i = next(self.ids)
        self.e[i] = {"text": text, "done": False}
        return i

    def set_done(self, i, done):
        self.writes += 1
        if i in self.e:
            self.e[i]["done"] = done

    def delete(self, i):
        self.writes += 1
        self.e.pop(i, None)


class FakeHA:
    def __init__(self):
        self.i = {}
        self.uids = (f"u{n}" for n in itertools.count())
        self.writes = 0

    def items(self):
        return {u: dict(v) for u, v in self.i.items()}

    def add(self, text):
        self.writes += 1
        self.i[next(self.uids)] = {"text": text, "done": False}

    def set_done(self, u, done):
        self.writes += 1
        self.i[u]["done"] = done

    def rename(self, u, text):
        self.writes += 1
        self.i[u]["text"] = text

    def delete(self, u):
        self.writes += 1
        self.i.pop(u, None)


def texts(side):
    return sorted((v["text"], v["done"]) for v in side.items().values())


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.t, self.h, self.pairs = FakeTandoor(), FakeHA(), []

    def cycle(self, **kw):
        self.pairs = ss.sync(self.t, self.h, self.pairs, **kw)

    def assert_same(self):
        self.assertEqual(texts(self.t), texts(self.h))

    def assert_stable(self):
        """A second cycle with no outside change writes nothing (no loop)."""
        tw, hw = self.t.writes, self.h.writes
        self.cycle()
        self.assertEqual((self.t.writes, self.h.writes), (tw, hw))

    def test_new_items_copy_both_ways(self):
        self.t.add("Milk (2 l)")
        self.h.add("Eggs")
        self.cycle()
        self.assert_same()
        self.assertEqual(len(self.pairs), 2)
        self.assert_stable()

    def test_first_run_pairs_same_text_with_no_copy(self):
        self.t.add("Milk")
        self.h.add("  milk ")
        self.cycle()
        self.assertEqual(len(self.t.e), 1)
        self.assertEqual(len(self.h.i), 1)
        self.assertEqual(len(self.pairs), 1)
        self.assert_stable()

    def test_checked_items_on_first_run_are_not_copied(self):
        i = self.t.add("Old thing")
        self.t.set_done(i, True)
        self.cycle()
        self.assertEqual(self.h.i, {})

    def test_check_off_both_ways(self):
        self.t.add("Milk")
        self.h.add("Eggs")
        self.cycle()
        milk_t = next(i for i, v in self.t.e.items() if v["text"] == "Milk")
        eggs_h = next(u for u, v in self.h.i.items() if v["text"] == "Eggs")
        self.t.set_done(milk_t, True)
        self.h.set_done(eggs_h, True)
        self.cycle()
        self.assert_same()
        self.assertEqual(texts(self.h), [("Eggs", True), ("Milk", True)])
        self.assert_stable()
        self.h.set_done(eggs_h, False)  # un-check
        self.cycle()
        self.assert_same()

    def test_delete_both_ways(self):
        self.t.add("Milk")
        self.t.add("Eggs")
        self.cycle()
        milk_t = next(i for i, v in self.t.e.items() if v["text"] == "Milk")
        eggs_h = next(u for u, v in self.h.i.items() if v["text"] == "Eggs")
        self.t.delete(milk_t)
        self.h.delete(eggs_h)
        self.cycle()
        self.assertEqual(self.t.e, {})
        self.assertEqual(self.h.i, {})
        self.assertEqual(self.pairs, [])
        self.assert_stable()

    def test_old_checked_entry_out_of_the_list_is_not_deleted(self):
        i = self.t.add("Milk")
        self.cycle()
        self.t.set_done(i, True)
        self.cycle()
        self.t.e[i]["old"] = True  # Tandoor's list leaves it out now
        self.cycle()
        self.assertIn(i, self.t.e)
        self.assertEqual(texts(self.h), [("Milk", True)])
        self.assertEqual(len(self.pairs), 1)

    def test_unchecked_entry_missing_from_the_list_is_looked_up(self):
        i = self.t.add("Milk")
        self.cycle()
        self.t.e[i]["old"] = True  # not in the list, but it exists: keep it
        self.cycle()
        self.assertEqual(texts(self.h), [("Milk", False)])

    def test_clearing_completed_in_ha_keeps_tandoor_history(self):
        i = self.t.add("Milk")
        self.cycle()
        self.t.set_done(i, True)
        self.cycle()
        self.h.i.clear()  # todo.remove_completed_items
        self.cycle()
        self.assertIn(i, self.t.e)
        self.assertEqual(self.pairs, [])
        self.assert_stable()

    def test_rename_both_ways(self):
        i = self.t.add("Milk")
        self.h.add("Eggs")
        self.cycle()
        self.t.e[i]["text"] = "Milk (2 l)"
        eggs_h = next(u for u, v in self.h.i.items() if v["text"] == "Eggs")
        self.h.rename(eggs_h, "Brown eggs")
        self.cycle()
        self.assert_same()
        self.assertEqual(texts(self.t), [("Brown eggs", False), ("Milk (2 l)", False)])
        self.assert_stable()

    def test_a_failed_read_changes_nothing(self):
        self.t.add("Milk")
        self.cycle()
        before = (json.dumps(self.pairs), texts(self.h))
        self.t.fail = True
        with self.assertRaises(ss.ApiError):
            self.cycle()
        self.assertEqual((json.dumps(self.pairs), texts(self.h)), before)

    def test_dry_run_writes_nothing(self):
        self.t.add("Milk")
        self.h.add("Eggs")
        tw, hw = self.t.writes, self.h.writes
        self.cycle(dry_run=True)
        self.assertEqual((self.t.writes, self.h.writes), (tw, hw))


class EntryTextTest(unittest.TestCase):
    def test_forms(self):
        self.assertEqual(ss.entry_text({"food": {"name": "Milk"}, "amount": "0"}), "Milk")
        self.assertEqual(ss.entry_text({"food": {"name": "Milk"}, "amount": 2.5, "unit": {"name": "l"}}), "Milk (2.5 l)")
        self.assertEqual(ss.entry_text({"food": {"name": "Eggs"}, "amount": 12, "unit": None}), "Eggs (12)")


class HttpClientTest(unittest.TestCase):
    """The real Tandoor and HomeAssistant classes against small fake HTTP servers."""

    def setUp(self):
        calls = self.calls = []
        entries = {1: {"id": 1, "food": {"name": "Milk"}, "amount": 0, "unit": None, "checked": False}}
        todo = [{"uid": "a", "summary": "Eggs", "status": "needs_action"}]

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def reply(self, code, body=None):
                raw = b"" if body is None else json.dumps(body).encode()
                self.send_response(code)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def body(self):
                n = int(self.headers.get("Content-Length") or 0)
                return json.loads(self.rfile.read(n)) if n else None

            def handle_any(self):
                b = self.body()
                calls.append((self.command, self.path, b, self.headers.get("Authorization"), self.headers.get("Host")))
                p = self.path
                if p.startswith("/api/shopping-list-entry/?"):
                    if "page=2" in p:
                        return self.reply(200, {"next": None, "results": [
                            {"id": 2, "food": {"name": "Flour"}, "amount": 1, "unit": {"name": "kg"}, "checked": True}]})
                    return self.reply(200, {"next": "https://tandoor.example/api/shopping-list-entry/?page=2&page_size=200",
                                            "results": list(entries.values())})
                if p == "/api/shopping-list-entry/9/":
                    return self.reply(404, {"detail": "not found"})
                if p == "/api/shopping-list-entry/" and self.command == "POST":
                    return self.reply(201, {"id": 7, **b})
                if p.startswith("/api/shopping-list-entry/"):
                    return self.reply(200 if self.command != "DELETE" else 204, {} if self.command != "DELETE" else None)
                if p == "/api/services/todo/get_items?return_response":
                    return self.reply(200, {"changed_states": [], "service_response": {"todo.shopping_list": {"items": todo}}})
                if p.startswith("/api/services/todo/"):
                    return self.reply(200, [])
                return self.reply(401, {"message": "no"})

            do_GET = do_POST = do_PATCH = do_DELETE = handle_any

        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.srv.server_port}"

    def tearDown(self):
        self.srv.shutdown()

    def test_tandoor(self):
        t = ss.Tandoor(self.base, "tok", host="tandoor.example")
        self.assertEqual(t.items(), {1: {"text": "Milk", "done": False}, 2: {"text": "Flour (1 kg)", "done": True}})
        self.assertIsNone(t.get(9))
        self.assertEqual(t.add("Eggs"), 7)
        t.set_done(1, True)
        t.delete(1)
        self.assertEqual(self.calls[0][3:], ("Bearer tok", "tandoor.example"))
        self.assertEqual(self.calls[1][1], "/api/shopping-list-entry/?page=2&page_size=200")
        self.assertEqual(self.calls[3][:3], ("POST", "/api/shopping-list-entry/", {"food": {"name": "Eggs"}, "amount": 0, "unit": None}))
        self.assertEqual(self.calls[4][:3], ("PATCH", "/api/shopping-list-entry/1/", {"checked": True}))
        self.assertEqual(self.calls[5][:2], ("DELETE", "/api/shopping-list-entry/1/"))

    def test_home_assistant(self):
        h = ss.HomeAssistant(self.base, "hat", "todo.shopping_list")
        self.assertEqual(h.items(), {"a": {"text": "Eggs", "done": False}})
        h.add("Milk")
        h.set_done("a", True)
        h.rename("a", "Brown eggs")
        h.delete("a")
        bodies = [c[2] for c in self.calls[1:]]
        self.assertEqual(bodies, [
            {"entity_id": "todo.shopping_list", "item": "Milk"},
            {"entity_id": "todo.shopping_list", "item": "a", "status": "completed"},
            {"entity_id": "todo.shopping_list", "item": "a", "rename": "Brown eggs"},
            {"entity_id": "todo.shopping_list", "item": "a"},
        ])
        self.assertEqual([c[1] for c in self.calls[1:]], ["/api/services/todo/add_item", "/api/services/todo/update_item",
                                                          "/api/services/todo/update_item", "/api/services/todo/remove_item"])

    def test_errors(self):
        with self.assertRaises(ss.ApiError):
            ss.Tandoor(self.base + "/nope", "x")._call("/x")
        with self.assertRaises(ss.ApiError):
            ss.HomeAssistant("http://127.0.0.1:1", "x", "todo.x").items()


if __name__ == "__main__":
    unittest.main()
