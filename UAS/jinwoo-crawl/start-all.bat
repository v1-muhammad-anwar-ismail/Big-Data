@echo off
title JinwooCrawl System Launcher
cd /d "%~dp0"
echo =====================================================================
echo  JinwooCrawl - Big Data Intelligence Platform
echo  Backend:  http://localhost:5002  -^> scrape.jinwoostream.lol
echo  Frontend: http://localhost:5001  -^> crawl.jinwoostream.lol
echo =====================================================================

start "JinwooCrawl Backend" cmd /c "start-backend.bat"
timeout /t 3 /nobreak >nul
start "JinwooCrawl Frontend" cmd /c "start-frontend.bat"

echo.
echo Layanan JinwooCrawl berhasil diluncurkan!
echo Silakan buka browser di: http://localhost:5001
echo Dokumentasi API Backend: http://localhost:5002/docs
echo.
pause
