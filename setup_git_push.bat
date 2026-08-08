@echo off
echo ======================================================================
echo    iCharts Master Dashboard - GitHub Deployment Setup
echo ======================================================================
echo.
echo 1. Initializing Git repository...
git init
git add .
git commit -m "Deploy iCharts Master Excel & Strategy Dashboard"
git branch -M main

echo.
echo ======================================================================
echo Next Steps to Push to Your GitHub Account:
echo 1. Go to https://github.com/new and create a repo named: icharts-excel-dashboard
echo 2. Copy and paste the following 2 lines into this command prompt:
echo.
echo    git remote add origin https://github.com/YOUR_USERNAME/icharts-excel-dashboard.git
echo    git push -u origin main
echo.
echo ======================================================================
pause
