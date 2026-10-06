# Практическое задание № 1 — вариант 25

Прототип на Python хранит таблицы `Client`, `Instruction`, `Result` в списках в памяти. Данные не записываются на диск. Реализованы создание, получение всех записей и редактирование для каждой таблицы, а также выборка `locale`, `content`, `status` после соединения таблиц для инструкций, созданных за последние 6 минут. Итого 10 методов RPC.

## Запуск

Требуется Python 3.10+.

```powershell
python server.py
```

В другом терминале:

```powershell
python client.py create_client locale=ru_RU
python client.py list_all_client
python client.py create_instruction client=1 content=hello tags=demo
python client.py create_result instruction=1 status=success output=hello
python client.py recent_results
```

`python demo.py` запускает сервер в фоне, вызывает все 10 методов, показывает одну ожидаемую ошибку и завершает работу. В рабочем режиме сервер пишет обращения и ошибки в `journal.log`.

Для этапа 1 можно отдельно запустить REPL модели: `python model_repl.py`. Для веб-интерфейса сначала запустите RPC-сервер, затем `python web.py` и откройте `http://127.0.0.1:8080`.

## Формат протокола

Все числа передаются в сетевом порядке байтов (big endian). Соединение обслуживает один вызов RPC.

| Сообщение | Версия | Код операции | Размер XML | Тело XML |
| --- | --- | --- | --- | --- |
| Запрос | 4 байта | 1 байт | 4 байта | переменная длина |
| Ответ | 1 байт | 1 байт | 4 байта | переменная длина |

Версия протокола — `1`. Коды операций: `1–3` для `Client`, `4–6` для `Instruction`, `7–9` для `Result` (создание, список, редактирование); `10` — выборка. Параметры передаются в XML как `<request><param name="field">value</param></request>`. Ответ содержит `<response ok="true"><data><item>...</item></data></response>` либо `<response ok="false"><error>...</error></response>`.

Поскольку условие не задаёт порядок байтов и единицу времени, в реализации выбраны big endian и Unix-секунды для полей `created`. Создание и редактирование проверяют внешние ключи `Instruction.client` и `Result.instruction`.

## Проверка

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m coverage run --branch --source=variant25,rpc -m unittest discover -s tests
python -m coverage report -m
```

Тесты используют `RuleBasedStateMachine` из Hypothesis. В итоговом отчёте coverage приведены ветви. Исходное условие — страницы 78–80 открытого сборника (печатные страницы 78–80; в PDF это также страницы 78–80).
