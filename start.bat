@echo off
REM ==========================================
REM  🎬 CARTOON CHANNEL - WINDOWS LAUNCHER
REM ==========================================
REM Double-click this file to run the pipeline!
REM Run as Administrator for scheduler setup.

echo.
echo  ==========================================
echo   🎬 FUNNY FRIENDS CARTOON CHANNEL
echo  ==========================================
echo.
echo  Choose an option:
echo.
echo  [1] FIRST TIME SETUP (run once)
echo  [2] RUN THIS WEEK NOW
echo  [3] RUN SPECIFIC WEEK
echo  [4] SETUP WINDOWS SCHEDULER (auto forever)
echo  [5] TEST PIPELINE (quick verify)
echo  [6] YOUTUBE AUTHORIZATION
echo  [0] EXIT
echo.

set /p choice="Enter choice (0-6): "

if "%choice%"=="1" (
    echo.
    echo 🚀 Running first-time setup...
    python run_pipeline.py --setup
    pause
)

if "%choice%"=="2" (
    echo.
    echo 🎬 Running current week...
    python run_pipeline.py
    pause
)

if "%choice%"=="3" (
    set /p week="Enter week number (1-52): "
    echo.
    echo 🎬 Running week %week%...
    python run_pipeline.py --week %week%
    pause
)

if "%choice%"=="4" (
    echo.
    echo ⚙️ Setting up Windows Task Scheduler...
    echo (Requires Administrator - right-click this file → Run as Administrator)
    powershell -ExecutionPolicy Bypass -File setup_windows_scheduler.ps1
    pause
)

if "%choice%"=="5" (
    echo.
    echo 🧪 Testing pipeline...
    python test_pipeline.py
    pause
)

if "%choice%"=="6" (
    echo.
    echo 🔐 Authorizing YouTube API...
    python upload.py --auth
    pause
)

if "%choice%"=="0" (
    exit
)

echo.
echo Invalid choice. Press any key to exit.
pause