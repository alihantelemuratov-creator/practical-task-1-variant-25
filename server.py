"""Start the variant 25 RPC server."""

import argparse
import logging

from rpc import RPCServer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    logging.basicConfig(
        filename="journal.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    with RPCServer((args.host, args.port)) as server:
        print(f"RPC server listening on {args.host}:{args.port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
