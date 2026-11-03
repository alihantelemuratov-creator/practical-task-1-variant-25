# Отчёт о тестировании — вариант №25

Проверено **3 ноября 2026 года** с помощью GitHub Actions:
https://github.com/alihantelemuratov-creator/practical-task-1-variant-25/actions/runs/41630445596

## Результаты

- Общий набор тестов: **7 passed**.
- Model-Based Testing RPC через Hypothesis RuleBasedStateMachine: **1 passed**.
- Покрытие ветвей (coverage --branch) измерялось **только по тестам Hypothesis** из tests/test_mbt_rpc.py.
- Измерялись сервер RPC (src/rpc.py) и модель данных (src/variant25.py), так как именно они обеспечивают 10 требуемых RPC-операций.

| Модуль | Операторы | Пропущено | Ветви | Частичные ветви | Покрытие |
| --- | ---: | ---: | ---: | ---: | ---: |
| src/rpc.py | 164 | 17 | 54 | 13 | 86% |
| src/variant25.py | 142 | 17 | 38 | 9 | 86% |
| **Итого** | **306** | **34** | **92** | **22** | **86%** |

## Как проверить заново

Установить зависимости и запустить проверки:

    python -m pip install -r requirements.txt
    python -m pytest -q
    python -m coverage erase
    python -m coverage run --branch -m pytest -q tests/test_mbt_rpc.py
    python -m coverage report -m --include="src/*"
    python -m coverage html --include="src/*"

Конфигурация .coveragerc ограничивает измерение модулями src.rpc и src.variant25. В сгенерированном отчёте отображаются ветви и непокрытые строки.

Дополнительные скриншоты для преподавателя: вывод TCP-демонстрации, журнал journal.log, результаты тестирования и история Git-коммитов.
