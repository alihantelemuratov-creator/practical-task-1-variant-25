"""Command-line client; supports all ten RPC methods."""

import argparse
import json

from rpc import NAME_TO_CODE, RPCClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("method", choices=sorted(NAME_TO_CODE))
    parser.add_argument("parameters", nargs="*", help="field=value")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    params = {}
    for pair in args.parameters:
        if "=" not in pair:
            parser.error(f"Expected field=value: {pair}")
        key, value = pair.split("=", 1)
        params[key] = value
    answer = RPCClient(args.host, args.port).call(args.method, **params)
    print(json.dumps(answer, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
