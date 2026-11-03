"""Model-Based Testing всех 10 TCP RPC методов через Hypothesis."""

from threading import Thread

from hypothesis import settings, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule

from src.rpc import RPCClient, RPCServer
from src.variant25 import DataModel, ModelError


NOW = 1000
TEXT = st.text(alphabet="abcXYZ123 Жé中 <>&'", max_size=10)


class RpcStateMachine(RuleBasedStateMachine):
    """Сравнивать сервер с независимой моделью на словарях."""

    def __init__(self):
        super().__init__()
        self.server = RPCServer(("127.0.0.1", 0), DataModel(clock=lambda: NOW))
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.rpc = RPCClient(port=self.server.server_address[1])
        self.clients = {}
        self.instructions = {}
        self.results = {}

    def teardown(self):
        """Остановить сервер между сгенерированными сценариями."""
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    @initialize(locale=TEXT, content=TEXT, status=TEXT)
    def initial_chain(self, locale, content, status):
        """Вызвать все десять методов в каждом начальном сценарии."""
        client = self.rpc.create_client(locale=locale, created=NOW)
        self.clients[client["uid"]] = client.copy()
        assert self.rpc.get_all_clients() == [client]
        client = self.rpc.update_client(client["uid"], locale="ru")
        self.clients[client["uid"]] = client.copy()

        instruction = self.rpc.create_instruction(
            client=client["uid"], created=NOW,
            content=content, tags="initial", launched=0,
        )
        self.instructions[instruction["uid"]] = instruction.copy()
        assert self.rpc.get_all_instructions() == [instruction]
        instruction = self.rpc.update_instruction(
            instruction["uid"], tags="changed"
        )
        self.instructions[instruction["uid"]] = instruction.copy()

        result = self.rpc.create_result(
            instruction=instruction["uid"], created=NOW,
            output="", status=status, error="",
            cache_hit=0, duration=5,
        )
        self.results[result["uid"]] = result.copy()
        assert self.rpc.get_all_results() == [result]
        result = self.rpc.update_result(result["uid"], cache_hit=1)
        self.results[result["uid"]] = result.copy()
        assert self.rpc.select_recent_results(now=NOW) == [
            {"locale": "ru", "content": content, "status": status}
        ]

    @rule(locale=TEXT)
    def add_client(self, locale):
        """Создать нового клиента через TCP."""
        row = self.rpc.create_client(locale=locale, created=NOW)
        self.clients[row["uid"]] = row.copy()

    @rule(uid=st.integers(1, 7), locale=TEXT)
    def edit_client(self, uid, locale):
        """Сравнить успешное или ошибочное редактирование."""
        if uid not in self.clients:
            self._missing(
                lambda: self.rpc.update_client(uid, locale=locale)
            )
            return
        row = self.rpc.update_client(uid, locale=locale)
        self.clients[uid] = row.copy()

    @rule(client_id=st.integers(1, 7), content=TEXT,
          created=st.sampled_from([NOW - 361, NOW - 360, NOW - 359, NOW]))
    def add_instruction(self, client_id, content, created):
        """Проверить внешние ключи и границу шести минут."""
        action = lambda: self.rpc.create_instruction(
            client=client_id, created=created,
            content=content, tags="", launched=0,
        )
        if client_id not in self.clients:
            self._missing(action)
            return
        row = action()
        self.instructions[row["uid"]] = row.copy()

    @rule(uid=st.integers(1, 7), content=TEXT)
    def edit_instruction(self, uid, content):
        """Редактировать существующие или отсутствующие инструкции."""
        action = lambda: self.rpc.update_instruction(
            uid, content=content
        )
        if uid not in self.instructions:
            self._missing(action)
            return
        row = action()
        self.instructions[uid] = row.copy()

    @rule(instruction_id=st.integers(1, 7), status=TEXT)
    def add_result(self, instruction_id, status):
        """Проверить добавление результата по внешнему ключу."""
        action = lambda: self.rpc.create_result(
            instruction=instruction_id, created=NOW,
            output="", status=status, error="",
            cache_hit=0, duration=1,
        )
        if instruction_id not in self.instructions:
            self._missing(action)
            return
        row = action()
        self.results[row["uid"]] = row.copy()

    @rule(uid=st.integers(1, 7), status=TEXT)
    def edit_result(self, uid, status):
        """Проверить редактирование результата по идентификатору."""
        action = lambda: self.rpc.update_result(uid, status=status)
        if uid not in self.results:
            self._missing(action)
            return
        row = action()
        self.results[uid] = row.copy()

    def _missing(self, action):
        """Проверить диагностируемую RPC-ошибку."""
        try:
            action()
        except ModelError:
            return
        raise AssertionError("Ожидалась ошибка отсутствующей записи")

    def expected_recent(self):
        """Независимо выполнить фильтр, соединение и проекцию."""
        answer = []
        seen = set()
        for result in self.results.values():
            inst = self.instructions.get(result["instruction"])
            if inst is None or inst["created"] <= NOW - 360:
                continue
            client = self.clients.get(inst["client"])
            if client is None:
                continue
            values = (client["locale"], inst["content"], result["status"])
            if values not in seen:
                answer.append(dict(zip(("locale", "content", "status"), values)))
                seen.add(values)
        return answer

    @invariant()
    def all_tables_match_reference(self):
        """Сравнить все три таблицы и результат реляционной операции."""
        assert self.rpc.get_all_clients() == list(self.clients.values())
        assert self.rpc.get_all_instructions() == list(
            self.instructions.values()
        )
        assert self.rpc.get_all_results() == list(self.results.values())
        assert self.rpc.select_recent_results(now=NOW) == (
            self.expected_recent()
        )


TestRpcStateMachine = RpcStateMachine.TestCase
TestRpcStateMachine.settings = settings(
    max_examples=20, stateful_step_count=12, deadline=None
)
