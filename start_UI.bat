@echo off
title YOLO Garbage Detection (Desktop)

echo.
echo ========================================
echo   YOLO Garbage Detection - Desktop
echo ========================================
echo.

cd /d "%~dp0"

echo Starting desktop application...
python garbage_detection_ui_v2.py

echo.
echo Application closed.
pause