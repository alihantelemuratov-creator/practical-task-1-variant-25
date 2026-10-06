import unittest
from threading import Thread

from hypothesis import given, settings, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from rpc import RPCClient, RPCServer
from variant25 import DataModel, ModelError


class ModelTests(unittest.TestCase):
    def test_join_and_six_minute_boundary(self):
        model = DataModel(clock=lambda: 1000)
        client = model.create("client", locale="ru")
        recent = model.create("instruction", client=client["uid"], content="new", created=641)
        old = model.create("instruction", client=client["uid"], content="old", created=640)
        model.create("result", instruction=recent["uid"], status="ok")
        model.create("result", instruction=old["uid"], status="old")
        self.assertEqual(model.recent_results(), [{"locale": "ru", "content": "new", "status": "ok"}])

    def test_rejects_missing_references(self):
        model = DataModel()
        with self.assertRaises(ModelError):
            model.create("instruction", client=999)
        with self.assertRaises(ModelError):
            model.create("result", instruction=999)

    @given(locale=st.text(max_size=30), content=st.text(max_size=30), status=st.text(max_size=30))
    @settings(max_examples=35)
    def test_round_trip_strings(self, locale, content, status):
        model = DataModel(clock=lambda: 1000)
        c = model.create("client", locale=locale)
        i = model.create("instruction", client=c["uid"], content=content)
        r = model.create("result", instruction=i["uid"], status=status)
        self.assertEqual(model.list_all("client"), [c])
        self.assertEqual(model.list_all("instruction"), [i])
        self.assertEqual(model.list_all("result"), [r])
        self.assertEqual(model.recent_results(), [{"locale": locale, "content": content, "status": status}])


class RPCIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.server = RPCServer(("127.0.0.1", 0), DataModel(clock=lambda: 1000))
        self.worker = Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.client = RPCClient(port=self.server.server_address[1])

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(timeout=2)

    @given(
        locale=st.text(alphabet="abcXYZ012<>&'\"Рус", max_size=15),
        content=st.text(alphabet="abcXYZ012<>&'\"Рус", max_size=15),
        status=st.text(alphabet="abcXYZ012<>&'\"Рус", max_size=15),
    )
    @settings(max_examples=15, deadline=None)
    def test_all_ten_methods_generated(self, locale, content, status):
        self.server.model = DataModel(clock=lambda: 1000)
        c = self.client.call("create_client", locale=locale)[0]
        self.assertEqual(len(self.client.call("list_all_client")), 1)
        self.client.call("update_client", uid=c["uid"], locale="en")
        i = self.client.call("create_instruction", client=c["uid"], content=content, created=999)[0]
        self.assertEqual(len(self.client.call("list_all_instruction")), 1)
        self.client.call("update_instruction", uid=i["uid"], tags="demo")
        r = self.client.call("create_result", instruction=i["uid"], status=status)[0]
        self.assertEqual(len(self.client.call("list_all_result")), 1)
        self.client.call("update_result", uid=r["uid"], cache_hit=1)
        self.assertEqual(self.client.call("recent_results", now=1000), [
            {"locale": "en", "content": content, "status": status}
        ])

    @given(uid=st.integers(min_value=1, max_value=10_000))
    @settings(max_examples=5, deadline=None)
    def test_error_response_generated(self, uid):
        with self.assertRaises(ModelError):
            self.client.call("create_result", instruction=uid)


class ModelStateMachine(RuleBasedStateMachine):
    """Hypothesis explores sequences of creates and edits to the data model."""

    def __init__(self):
        super().__init__()
        self.model = DataModel(clock=lambda: 1000)
        self.client_ids = []

    @rule(locale=st.text(max_size=15))
    def create_client(self, locale):
        row = self.model.create("client", locale=locale)
        self.client_ids.append(row["uid"])

    @rule(locale=st.text(max_size=15))
    def update_first_client(self, locale):
        if self.client_ids:
            uid = self.client_ids[0]
            row = self.model.update("client", uid, locale=locale)
            assert row["locale"] == locale

    @invariant()
    def ids_are_unique(self):
        rows = self.model.list_all("client")
        assert len({row["uid"] for row in rows}) == len(rows)
        assert len(rows) == len(self.client_ids)


TestStateMachine = ModelStateMachine.TestCase
TestStateMachine.settings = settings(max_examples=25, stateful_step_count=20)


if __name__ == "__main__":
    unittest.main()
