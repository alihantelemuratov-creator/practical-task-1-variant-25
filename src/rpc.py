"""TCP RPC protocol specified for practical assignment 1, variant 25."""

from __future__ import annotations

import logging
import socket
import socketserver
import struct
import xml.etree.ElementTree as ET
from typing import Any

from src.variant25 import DataModel, ModelError, STRING_FIELDS


VERSION = 1
MAX_BODY = 1_000_000
OPERATIONS = {
    1: ("create", "client"),
    2: ("list_all", "client"),
    3: ("update", "client"),
    4: ("create", "instruction"),
    5: ("list_all", "instruction"),
    6: ("update", "instruction"),
    7: ("create", "result"),
    8: ("list_all", "result"),
    9: ("update", "result"),
    10: ("recent_results", None),
}
NAME_TO_CODE = {
    f"{method}_{entity}" if entity else method: code
    for code, (method, entity) in OPERATIONS.items()
}
NAME_TO_CODE.update({
    "get_all_clients": 2,
    "get_all_instructions": 5,
    "get_all_results": 8,
    "select_recent_results": 10,
})


def read_exact(stream, count: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < count:
        part = stream.recv(count - len(chunks))
        if not part:
            raise ConnectionError("Connection closed during frame")
        chunks.extend(part)
    return bytes(chunks)


def _xml_request(params: dict[str, Any]) -> bytes:
    root = ET.Element("request")
    for name, value in params.items():
        ET.SubElement(root, "param", name=name).text = str(value)
    return ET.tostring(root, encoding="utf-8")


def _parse_request(body: bytes, entity: str | None) -> dict:
    root = ET.fromstring(body)
    if root.tag != "request":
        raise ModelError("Expected XML request")
    values = {}
    for param in root:
        if param.tag != "param" or "name" not in param.attrib:
            raise ModelError("Invalid parameter")
        name = param.attrib["name"]
        if name in values:
            raise ModelError(f"Duplicate parameter: {name}")
        raw = param.text or ""
        if entity and name not in STRING_FIELDS[entity]:
            try:
                values[name] = int(raw)
            except ValueError as exc:
                raise ModelError(f"{name} must be an integer") from exc
        elif name == "now":
            try:
                values[name] = int(raw)
            except ValueError as exc:
                raise ModelError("now must be an integer") from exc
        else:
            values[name] = raw
    return values


def _xml_response(data=None, error: str | None = None) -> bytes:
    root = ET.Element("response", ok="false" if error else "true")
    if error:
        ET.SubElement(root, "error").text = error
    else:
        payload = ET.SubElement(root, "data")
        records = data if isinstance(data, list) else [data]
        for record in records:
            item = ET.SubElement(payload, "item")
            for name, value in record.items():
                ET.SubElement(item, "field", name=name).text = str(value)
    return ET.tostring(root, encoding="utf-8")


def _parse_response(body: bytes) -> dict | list[dict]:
    root = ET.fromstring(body)
    if root.tag != "response":
        raise ValueError("Invalid response XML")
    if root.get("ok") != "true":
        raise ModelError(root.findtext("error") or "RPC error")
    records = []
    for item in root.findall("./data/item"):
        record = {}
        for field in item.findall("field"):
            name = field.attrib["name"]
            value = field.text or ""
            record[name] = int(value) if name in {
                "uid", "created", "client", "launched", "instruction", "cache_hit", "duration"
            } else value
        records.append(record)
    return records


class RPCHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            header = read_exact(self.request, 5)
            size, code = struct.unpack("<IB", header)
            if size > MAX_BODY:
                raise ModelError("Request body too large")
            body = read_exact(self.request, size)
            self.server.logger.info(
                "RPC request code=%s size=%s body=%r", code, size, body
            )
            if code not in OPERATIONS:
                raise ModelError("Unknown operation code")
            method, entity = OPERATIONS[code]
            params = _parse_request(body, entity)
            if method == "recent_results":
                if set(params) - {"now"}:
                    raise ModelError("Unknown query parameter")
                result = self.server.model.recent_results(**params)
            elif method == "list_all":
                if params:
                    raise ModelError("List operation takes no parameters")
                result = self.server.model.list_all(entity)
            elif method == "update":
                if "uid" not in params:
                    raise ModelError("uid is required")
                uid = params.pop("uid")
                result = self.server.model.update(entity, uid, **params)
            else:
                result = self.server.model.create(entity, **params)
            response = _xml_response(result)
            self.server.logger.info("RPC response code=%s ok", code)
        except (ConnectionError, OSError, ET.ParseError, ModelError, TypeError) as exc:
            code = locals().get("code", 0)
            response = _xml_response(error=str(exc))
            self.server.logger.warning("RPC code=%s error=%s", code, exc)
        self.request.sendall(struct.pack("<BBI", VERSION, code, len(response)) + response)


class RPCServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address, model: DataModel | None = None):
        self.model = model if model is not None else DataModel()
        self.logger = logging.getLogger(f"variant25.rpc.{id(self)}")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self._journal = logging.FileHandler("journal.log", encoding="utf-8")
        self._journal.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        self.logger.addHandler(self._journal)
        super().__init__(address, RPCHandler)

    def server_close(self):
        """Закрыть журнал после остановки TCP-сервера."""
        super().server_close()
        self.logger.removeHandler(self._journal)
        self._journal.close()


class RPCClient:
    def __init__(self, host="127.0.0.1", port=8765, timeout=5):
        self.host, self.port, self.timeout = host, port, timeout

    def call(self, method: str, **params) -> list[dict]:
        if method not in NAME_TO_CODE:
            raise ValueError(f"Unknown RPC method: {method}")
        code = NAME_TO_CODE[method]
        body = _xml_request(params)
        with socket.create_connection((self.host, self.port), self.timeout) as connection:
            connection.sendall(struct.pack("<IB", len(body), code) + body)
            version, returned_code, size = struct.unpack(
                "<BBI", read_exact(connection, 6)
            )
            if version != VERSION or returned_code != code or size > MAX_BODY:
                raise ValueError("Invalid response header")
            return _parse_response(read_exact(connection, size))

    def create_client(self, **values):
        """Создать Client удалённо."""
        return self.call("create_client", **values)[0]

    def get_all_clients(self):
        """Получить клиентов удалённо."""
        return self.call("get_all_clients")

    def update_client(self, uid, **changes):
        """Изменить клиента удалённо."""
        return self.call("update_client", uid=uid, **changes)[0]

    def create_instruction(self, **values):
        """Создать Instruction удалённо."""
        return self.call("create_instruction", **values)[0]

    def get_all_instructions(self):
        """Получить инструкции удалённо."""
        return self.call("get_all_instructions")

    def update_instruction(self, uid, **changes):
        """Изменить инструкцию удалённо."""
        return self.call("update_instruction", uid=uid, **changes)[0]

    def create_result(self, **values):
        """Создать Result удалённо."""
        return self.call("create_result", **values)[0]

    def get_all_results(self):
        """Получить результаты удалённо."""
        return self.call("get_all_results")

    def update_result(self, uid, **changes):
        """Изменить результат удалённо."""
        return self.call("update_result", uid=uid, **changes)[0]

    def select_recent_results(self, now=None):
        """Получить выборку за последние 6 минут."""
        if now is None:
            return self.call("select_recent_results")
        return self.call("select_recent_results", now=now)
