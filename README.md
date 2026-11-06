# Практическая работа №1 — вариант №25

Дисциплина: «Прикладная разработка серверных частей веб-приложений на языке Питон».
Сборник заданий ИКБО-71-24 (2026/2027), страницы 78–80, ER-диаграмма 25 и таблица протокола 25.

## Что реализовано

Прототип работает на Python и хранит записи Client, Instruction и Result **в списках в оперативной памяти**. Сохранения таблиц на диск нет. Отдельно по заданию сохраняется файл журнала запросов journal.log.

### Этап 1: данные и REPL

Таблицы и атрибуты:

| Сущность | Атрибуты |
| --- | --- |
| Client | uid, created, locale |
| Instruction | uid, created, content, client, tags, launched |
| Result | uid, created, output, status, error, instruction, cache_hit, duration |

Слой данных: src/variant25.py. Для каждой сущности реализованы создание, получение всех записей и редактирование; всего девять методов, плюс select_recent_results (десятая операция). Предусмотрены проверки типов, связей, некорректных аргументов и ошибок.

Выборка выполняет соединения по C.uid = I.client и I.uid = R.instruction, фильтр I.created > now - 6 минут и проекцию C.locale, I.content, R.status.

Запуск REPL:

    python -m src.model_repl

Запуск через Windows:

    .\run.bat repl

### Этап 2: TCP RPC и XML

Сервер: src/server.py и src/rpc.py; клиент: src/client.py.
Формат запроса (порядок байт **little-endian**):

| Смещение | Размер | Содержимое |
| --- | --- | --- |
| 0 | 4 байта | Размер XML-тела запроса |
| 4 | 1 байт | Код операции |
| 5 | переменно | XML-тело запроса |

Формат ответа:

| Смещение | Размер | Содержимое |
| --- | --- | --- |
| 0 | 1 байт | Версия протокола |
| 1 | 1 байт | Код операции |
| 2 | 4 байта | Размер XML-тела ответа |
| 6 | переменно | XML-тело ответа |

В журнале journal.log фиксируются все обработанные RPC-запросы, в том числе некорректные. Файл исключён из Git.

Для запуска откройте два терминала:

    python -m src.server
    python -m src.demo

Клиент для отдельного вызова:

    python -m src.client create_client locale=ru_RU
    python -m src.client get_all_clients

Демонстрация всех 10 функций:

    .\run.bat demo

Простой локальный HTTP-интерфейс (дополнительно):

    python -m src.web

После этого открыть http://127.0.0.1:8080; TCP-сервер должен быть запущен отдельно.

### Этап 3: Model-Based Testing

Тесты сгенерированы Hypothesis с помощью RuleBasedStateMachine. В файле tests/test_mbt_rpc.py эталонное состояние хранится отдельно в словарях и сопоставляется с состоянием TCP-сервера после последовательностей операций. В каждом начальном сценарии вызываются все 10 RPC-методов; также проверяются ошибки и временная граница 6 минут.

Установить зависимости:

    python -m pip install -r requirements.txt

Запустить все тесты:

    python -m pytest -q

Запустить только MBT:

    .\run.bat mbt

Сформировать отчёт покрытия ветвей только по тестам, сгенерированным Hypothesis:

    .\run.bat coverage

На Linux:

    sh run.sh coverage

GitHub Actions: https://github.com/alihantelemuratov-creator/practical-task-1-variant-25/actions

Проверено в GitHub Actions 03.11.2026: 7 тестов пройдены, модельный тест Hypothesis пройден, общее покрытие ветвей двух проверяемых модулей — 86%.

Просмотреть процент покрытия: вывод команды coverage report. Дополнительно создаётся htmlcov/index.html. Приводить число покрытия в отчёте следует только после фактического запуска в своей среде.

## Структура

- src/ — модель данных, REPL, TCP-сервер и RPC-клиент
- tests/ — модульные и модельные проверки
- run.bat / run.sh — сценарии запуска
- requirements.txt — зависимости
- .gitignore — исключение временных файлов
- TEST_REPORT.md — как получить проверяемый отчёт

## Git

История включает отдельные коммиты подготовки модели, TCP RPC и модельных тестов. Не загружайте в репозиторий ZIP, journal.log, .coverage, .venv и __pycache__.

## Проверка соответствия варианту №25 перед защитой

Сверка со страницами **78–80** исходного задания:

| Этап | Что требуется | Где реализовано | Проверка |
| --- | --- | --- | --- |
| 1 | Три таблицы в виде списков и 9 операций создания/получения/редактирования | `src/variant25.py` | `run.bat repl` |
| 1 | Десятая операция: соединение Client, Instruction, Result с фильтром за 6 минут | `DataModel.select_recent_results` | Команда `recent` в REPL |
| 2 | TCP RPC для всех 10 функций, XML, little-endian и журнал `journal.log` | `src/rpc.py`, `src/client.py` | `run.bat demo` |
| 3 | MBT с `RuleBasedStateMachine` и покрытием ветвей через `coverage` | `tests/test_mbt_rpc.py` | `run.bat mbt`, затем `run.bat coverage` |

Последовательность демонстрации в **Windows PowerShell** (из корня проекта):

```powershell
python -m pip install -r requirements.txt
.\run.bat repl
.\run.bat demo
.\run.bat mbt
.\run.bat coverage
```

В REPL можно показать создание клиента (`create client locale=ru_RU`), получение
(`list client`) и редактирование (`update client 1 locale=en_US`).
Чтобы выйти из REPL, введите `exit` перед выполнением следующей команды.

Команда `demo` самостоятельно запускает локальный TCP-сервер, вызывает
все 10 RPC-операций и демонстрирует обработку ошибки; файл `journal.log`
создаётся локально и не добавляется в репозиторий.

В истории Git доступны отдельные содержательные коммиты этапов:
[модель данных](https://github.com/alihantelemuratov-creator/practical-task-1-variant-25/commit/c95220bc399a5b93aa90944ff13f420643b793b5),
[TCP RPC](https://github.com/alihantelemuratov-creator/practical-task-1-variant-25/commit/3073322bf77397a019722adb60043a354d63f222),
[MBT](https://github.com/alihantelemuratov-creator/practical-task-1-variant-25/commit/bbf357816a520c4463b71aa544088c415dbd9e3d).

Последние результаты тестирования приведены в `TEST_REPORT.md`;
при защите следует заново выполнить команды на своей машине.
