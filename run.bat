@echo off
cd /d "%~dp0"
if /I "%~1"=="repl" goto repl
if "%~1"=="" goto repl
if /I "%~1"=="server" goto server
if /I "%~1"=="demo" goto demo
if /I "%~1"=="web" goto web
if /I "%~1"=="mbt" goto mbt
if /I "%~1"=="coverage" goto coverage
if /I "%~1"=="test" goto test
echo Usage: run.bat [repl^|server^|demo^|web^|mbt^|coverage^|test]
exit /b 2
:repl
python -m src.model_repl
exit /b %errorlevel%
:server
python -m src.server
exit /b %errorlevel%
:demo
python -m src.demo
exit /b %errorlevel%
:web
python -m src.web
exit /b %errorlevel%
:mbt
python -m pytest -q tests/test_mbt_rpc.py
exit /b %errorlevel%
:coverage
python -m coverage erase
python -m coverage run --branch -m pytest -q tests/test_mbt_rpc.py
if errorlevel 1 exit /b %errorlevel%
python -m coverage report -m --include="src/*"
python -m coverage html --include="src/*"
exit /b %errorlevel%
:test
python -m pytest -q
exit /b %errorlevel%
