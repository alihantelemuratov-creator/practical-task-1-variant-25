# Отчёт о проверке практической работы №1, вариант №25

Этот файл описывает **воспроизводимую проверку**. Ранее приведённый процент покрытия относился к старой версии кода и после исправления структуры и протокола не считается актуальным.

## Проверка на компьютере

    python -m pip install -r requirements.txt
    python -m pytest -q
    python -m coverage erase
    python -m coverage run --branch -m pytest -q tests/test_mbt_rpc.py
    python -m coverage report -m --include="src/*"
    python -m coverage html --include="src/*"

Отчёт о покрытии формируется **только тестом tests/test_mbt_rpc.py**, использующим Hypothesis RuleBasedStateMachine. Сохраните фактический вывод команды coverage report в отчёт для преподавателя; не подставляйте предполагаемые проценты.

Дополнительно сделайте скриншоты демонстрации TCP RPC и журнала journal.log. Убедитесь, что в GitHub есть три отдельных коммита для этапов работы.
