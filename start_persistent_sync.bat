@echo off
title YAMLWeave Persistent Sync

echo Starting YAMLWeave persistent sync service...
echo This window will continue running until sync succeeds
echo Press Ctrl+C to stop

cd /d "%~dp0"

rem 检查是否已在运行
if exist sync.pid (
    echo Checking if sync is already running...
    for /f %%i in (sync.pid) do (
        tasklist /fi "PID eq %%i" 2>nul | find "%%i" >nul
        if errorlevel 1 (
            echo Removing stale PID file
            del sync.pid
        ) else (
            echo Sync already running with PID %%i
            pause
            exit /b 1
        )
    )
)

rem 启动持久化同步
bash persistent_sync.sh

echo.
echo Sync completed! Press any key to exit.
pause