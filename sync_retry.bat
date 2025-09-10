@echo off
setlocal enabledelayedexpansion

echo Starting GitHub sync with retry mechanism...

set MAX_ATTEMPTS=20
set INITIAL_WAIT=5
set current_wait=%INITIAL_WAIT%

for /L %%i in (1,1,%MAX_ATTEMPTS%) do (
    echo.
    echo === Attempt %%i of %MAX_ATTEMPTS% ===
    echo Waiting !current_wait! seconds before attempt...
    timeout /t !current_wait! /nobreak >nul
    
    echo Trying to push to GitHub...
    git push -u origin main
    
    if !errorlevel! == 0 (
        echo.
        echo *** SUCCESS! Repository synced successfully ***
        goto :success
    )
    
    echo Push failed, trying fetch first...
    git fetch origin main
    
    if !errorlevel! == 0 (
        echo Fetch successful, trying merge...
        git merge origin/main --allow-unrelated-histories --no-edit
        
        if !errorlevel! == 0 (
            echo Merge successful, trying push again...
            git push -u origin main
            
            if !errorlevel! == 0 (
                echo.
                echo *** SUCCESS! Repository synced after merge ***
                goto :success
            )
        )
    )
    
    echo Attempt %%i failed. Exponential backoff...
    set /a current_wait=!current_wait! * 2
    if !current_wait! gtr 120 set current_wait=120
)

echo.
echo All %MAX_ATTEMPTS% attempts failed. Please check:
echo 1. Network connectivity
echo 2. GitHub repository access
echo 3. DNS settings
goto :end

:success
echo.
echo Repository is now synchronized with GitHub!
git status
git log --oneline -3

:end
pause