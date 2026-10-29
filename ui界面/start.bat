@echo off
echo ========================================
echo   YOLO Garbage Detection System
echo ========================================
echo.

echo [1/3] Starting Flask backend (GPU mode)...
echo        Loading model, please wait...
cd /d %~dp0\backend
start /min "YOLO Backend" cmd /k "python app.py"

echo.
echo [2/3] Waiting for backend to start...
timeout /t 8 /nobreak >nul

echo [3/3] Starting frontend dev server...
cd /d %~dp0\frontend
start "YOLO Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo   Startup Complete!
echo ========================================
echo.
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:5000
echo.
echo   Backend window is minimized.
echo   Press any key to open browser...
pause >nul
start http://localhost:3000
