@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python setup_engine.py
) else (
  py -3 setup_engine.py
)
if errorlevel 1 echo Instalacja nieukonczona. Sprawdz komunikaty powyzej.
pause
