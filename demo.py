"""Demonstrate all ten RPC operations and expected error handling."""

import json
from threading import Thread
from time import time

from rpc import RPCClient, RPCServer
from variant25 import ModelError


def main():
    with RPCServer(("127.0.0.1", 0)) as server:
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        client = RPCClient(port=server.server_address[1])

        def call(name, **params):
            result = client.call(name, **params)
            print(name, json.dumps(result, ensure_ascii=False))
            return result

        try:
            person = call("create_client", locale="ru_RU")[0]
            call("list_all_client")
            call("update_client", uid=person["uid"], locale="en_US")
            instruction = call(
                "create_instruction",
                client=person["uid"],
                content="print('hello')",
                tags="demo",
                launched=1,
                created=int(time()),
            )[0]
            call("list_all_instruction")
            call("update_instruction", uid=instruction["uid"], tags="checked")
            result = call(
                "create_result",
                instruction=instruction["uid"],
                output="hello",
                status="success",
                duration=12,
            )[0]
            call("list_all_result")
            call("update_result", uid=result["uid"], cache_hit=1)
            call("recent_results")
            try:
                call("create_result", instruction=999, status="failure")
            except ModelError as error:
                print("Expected error:", error)
        finally:
            server.shutdown()
            worker.join(timeout=2)


if __name__ == "__main__":
    main()
