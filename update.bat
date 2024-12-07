@echo off
echo Current directory: %~dp0
cd /d "%~dp0"  || (echo Failed to change directory! & pause & exit /b)

echo Fetching latest changes from the remote repository...
git fetch || (echo Failed to fetch from Git! & pause & exit /b)

echo Pulling the latest changes from the remote repository...
git pull || (echo Failed to pull from Git! & pause & exit /b)

echo Done!
pause
