"""Small local web client for the TCP RPC server."""

from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs
import argparse
import json

from rpc import NAME_TO_CODE, RPCClient


class WebHandler(BaseHTTPRequestHandler):
    rpc_host = "127.0.0.1"
    rpc_port = 8765

    def do_GET(self):
        self._render()

    def do_POST(self):
        if self.path != "/call":
            self.send_error(404)
            return
        size = int(self.headers.get("Content-Length", "0"))
        if size > 100_000:
            self.send_error(413)
            return
        data = parse_qs(self.rfile.read(size).decode("utf-8"), keep_blank_values=True)
        method = data.get("method", [""])[0]
        parameters = data.get("parameters", [""])[0]
        try:
            params = {}
            for line in parameters.splitlines():
                if not line.strip():
                    continue
                key, value = line.split("=", 1)
                params[key.strip()] = value.strip()
            result = RPCClient(self.rpc_host, self.rpc_port).call(method, **params)
            message = json.dumps(result, ensure_ascii=False, indent=2)
        except (OSError, ValueError) as error:
            message = f"Error: {error}"
        self._render(method, parameters, message)

    def _render(self, method="", parameters="", message=""):
        options = "".join(
            f'<option value="{escape(name)}" {"selected" if name == method else ""}>{escape(name)}</option>'
            for name in sorted(NAME_TO_CODE)
        )
        page = f"""<!doctype html><html lang="ru"><meta charset="utf-8">
<title>Вариант 25 — TCP RPC</title><style>
body{{font:16px system-ui;max-width:760px;margin:3rem auto;padding:0 1rem;color:#172337}}
h1{{font-size:1.7rem}}form{{display:grid;gap:1rem}}select,textarea,button{{font:inherit;padding:.7rem}}
textarea{{min-height:9rem}}button{{background:#1c5ea8;color:#fff;border:0;cursor:pointer}}
pre{{background:#f1f5f9;padding:1rem;white-space:pre-wrap;overflow-wrap:anywhere}}
</style><h1>Вариант 25 · TCP RPC</h1>
<p>Вызов методов модели данных через TCP-сервер. Параметры укажите по одному в строке.</p>
<form method="post" action="/call"><label>Метод<select name="method">{options}</select></label>
<label>Параметры<textarea name="parameters" placeholder="locale=ru_RU">{escape(parameters)}</textarea></label>
<button type="submit">Выполнить</button></form>
<h2>Ответ</h2><pre>{escape(message)}</pre></html>""".encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.end_headers()
        self.wfile.write(page)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--rpc-host", default="127.0.0.1")
    parser.add_argument("--rpc-port", type=int, default=8765)
    args = parser.parse_args()
    WebHandler.rpc_host, WebHandler.rpc_port = args.rpc_host, args.rpc_port
    with ThreadingHTTPServer((args.host, args.port), WebHandler) as server:
        print(f"Web client at http://{args.host}:{args.port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
