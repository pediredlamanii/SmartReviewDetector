@echo off
echo Starting SmartReviewDetector...

IF EXIST .\venv\Scripts\python.exe (
    .\venv\Scripts\python.exe app.py
) ELSE IF EXIST .\venv\bin\python.exe (
    .\venv\bin\python.exe app.py
) ELSE (
    echo Python executable not found in virtual environment. Please run install.bat first.
)

pause
