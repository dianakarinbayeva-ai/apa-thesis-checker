@echo off
cd /d "%~dp0"
if exist "APA Thesis Checker.exe" (
  "APA Thesis Checker.exe"
) else (
  python launcher.py
)
pause
