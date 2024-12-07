@echo off
cd /d ""  REM Change this to your repository path

echo Fetching latest changes from the remote repository...
git fetch

echo Pulling the latest changes from the remote repository...
git pull

echo Done!