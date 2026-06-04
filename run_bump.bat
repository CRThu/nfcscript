@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: 自动增加版本号
echo [INFO] Bumping version...
uvx bump-my-version bump patch

pause