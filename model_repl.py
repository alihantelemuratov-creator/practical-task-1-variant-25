"""Interactive REPL for the in-memory data layer (stage 1)."""

import json
import shlex

from variant25 import DataModel, ModelError


HELP = """Commands:
  create client|instruction|result field=value ...
  list client|instruction|result
  update client|instruction|result UID field=value ...
  recent [now=UNIX_SECONDS]
  help
  exit
"""


def _parameters(parts):
    values = {}
    for pair in parts:
        if "=" not in pair:
            raise ModelError(f"Expected field=value: {pair}")
        name, raw = pair.split("=", 1)
        values[name] = int(raw) if name in {
            "created", "client", "launched", "instruction", "cache_hit", "duration", "now"
        } else raw
    return values


def main():
    model = DataModel()
    print(HELP)
    while True:
        try:
            parts = shlex.split(input("variant25> "))
            if not parts:
                continue
            command = parts[0]
            if command in {"exit", "quit"}:
                break
            if command == "help":
                print(HELP)
                continue
            if command == "create" and len(parts) >= 2:
                answer = model.create(parts[1], **_parameters(parts[2:]))
            elif command == "list" and len(parts) == 2:
                answer = model.list_all(parts[1])
            elif command == "update" and len(parts) >= 3:
                answer = model.update(parts[1], int(parts[2]), **_parameters(parts[3:]))
            elif command == "recent":
                answer = model.recent_results(**_parameters(parts[1:]))
            else:
                raise ModelError("Unknown command; type help")
            print(json.dumps(answer, ensure_ascii=False, indent=2))
        except (ModelError, ValueError) as error:
            print("Error:", error)
        except (EOFError, KeyboardInterrupt):
            print()
            break


if __name__ == "__main__":
    main()
