"""In-memory data model for practical assignment 1, variant 25."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from threading import RLock
from time import time
from typing import Any


@dataclass
class Client:
    uid: int
    created: int
    locale: str


@dataclass
class Instruction:
    uid: int
    created: int
    content: str
    client: int
    tags: str
    launched: int


@dataclass
class Result:
    uid: int
    created: int
    output: str
    status: str
    error: str
    instruction: int
    cache_hit: int
    duration: int


TABLES = {"client": Client, "instruction": Instruction, "result": Result}
STRING_FIELDS = {
    "client": {"locale"},
    "instruction": {"content", "tags"},
    "result": {"output", "status", "error"},
}


class ModelError(ValueError):
    pass


class DataModel:
    """Stores table rows in lists, as required by the assignment."""

    def __init__(self, clock=None):
        self.clients: list[list] = []
        self.instructions: list[list] = []
        self.results: list[list] = []
        self._next_id = {name: 1 for name in TABLES}
        self._clock = clock or time
        self._lock = RLock()

    def _rows(self, entity: str) -> list:
        if entity not in TABLES:
            raise ModelError(f"Unknown entity: {entity}")
        return getattr(self, f"{entity}s")

    def _validate(
        self, entity: str, values: dict[str, Any], creating: bool
    ) -> dict:
        cls = TABLES[entity]
        allowed = set(cls.__dataclass_fields__) - {"uid"}
        unknown = set(values) - allowed
        if unknown:
            raise ModelError(f"Unknown fields: {', '.join(sorted(unknown))}")
        result = {}
        for key, value in values.items():
            if key in STRING_FIELDS[entity]:
                if not isinstance(value, str):
                    raise ModelError(f"{key} must be a string")
            elif isinstance(value, bool) or not isinstance(value, int):
                raise ModelError(f"{key} must be an integer")
            result[key] = value
        if creating:
            defaults = {
                "client": {"locale": ""},
                "instruction": {"content": "", "tags": "", "launched": 0},
                "result": {
                    "output": "", "status": "", "error": "",
                    "cache_hit": 0, "duration": 0,
                },
            }
            result = {**defaults[entity], **result}
            result.setdefault("created", int(self._clock()))
            required = {"instruction": "client", "result": "instruction"}
            if entity in required and required[entity] not in result:
                raise ModelError(f"{required[entity]} is required")
        return result

    def _check_references(self, entity: str, values: dict) -> None:
        if entity == "instruction" and "client" in values:
            if not any(row[0] == values["client"] for row in self.clients):
                raise ModelError("Client does not exist")
        if entity == "result" and "instruction" in values:
            if not any(
                row[0] == values["instruction"]
                for row in self.instructions
            ):
                raise ModelError("Instruction does not exist")

    def create(self, entity: str, **values) -> dict:
        with self._lock:
            rows = self._rows(entity)
            values = self._validate(entity, values, True)
            self._check_references(entity, values)
            uid = self._next_id[entity]
            record = TABLES[entity](uid=uid, **values)
            rows.append(list(asdict(record).values()))
            self._next_id[entity] += 1
            return asdict(record)

    def list_all(self, entity: str) -> list[dict]:
        with self._lock:
            fields = TABLES[entity].__dataclass_fields__
            return [dict(zip(fields, row)) for row in self._rows(entity)]

    def update(self, entity: str, uid: int, **values) -> dict:
        with self._lock:
            rows = self._rows(entity)
            if isinstance(uid, bool) or not isinstance(uid, int):
                raise ModelError("uid must be an integer")
            values = self._validate(entity, values, False)
            self._check_references(entity, values)
            for index, row in enumerate(rows):
                if row[0] == uid:
                    fields = list(TABLES[entity].__dataclass_fields__)
                    updated = dict(zip(fields, row))
                    updated.update(values)
                    rows[index] = [updated[field] for field in fields]
                    return updated
            raise ModelError(f"{entity} {uid} does not exist")

    def recent_results(self, now: int | None = None) -> list[dict]:
        """π(locale, content, status) σ(created > now − 6 min)(C ⋈ I ⋈ R)."""
        with self._lock:
            now = int(self._clock()) if now is None else now
            clients = {row[0]: row for row in self.clients}
            instructions = {row[0]: row for row in self.instructions}
            answer = []
            seen = set()
            for result in self.results:
                instruction = instructions.get(result[5])
                if instruction is None or instruction[1] <= now - 360:
                    continue
                client = clients.get(instruction[3])
                if client is not None:
                    values = (client[2], instruction[2], result[3])
                    if values not in seen:
                        seen.add(values)
                        names = ("locale", "content", "status")
                        answer.append(dict(zip(names, values)))
            return answer

    def create_client(self, **values):
        """Создать запись Client."""
        return self.create("client", **values)

    def get_all_clients(self):
        """Получить все записи Client."""
        return self.list_all("client")

    def update_client(self, uid, **values):
        """Редактировать Client."""
        return self.update("client", uid, **values)

    def create_instruction(self, **values):
        """Создать запись Instruction."""
        return self.create("instruction", **values)

    def get_all_instructions(self):
        """Получить все записи Instruction."""
        return self.list_all("instruction")

    def update_instruction(self, uid, **values):
        """Редактировать Instruction."""
        return self.update("instruction", uid, **values)

    def create_result(self, **values):
        """Создать запись Result."""
        return self.create("result", **values)

    def get_all_results(self):
        """Получить все записи Result."""
        return self.list_all("result")

    def update_result(self, uid, **values):
        """Редактировать Result."""
        return self.update("result", uid, **values)

    def select_recent_results(self, now=None):
        """Выборка связанных результатов за шесть минут."""
        return self.recent_results(now)
