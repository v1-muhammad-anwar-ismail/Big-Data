@echo off
title JinwooCrawl Backend (Port 5002)
cd /d "%~dp0backend"
echo [JinwooCrawl] Memulai FastAPI Backend di port 5002...
python -m uvicorn app.main:app --host 0.0.0.0 --port 5002 --reload
pause
