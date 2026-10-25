@echo off
echo Setting up the virtual environment...
python -m venv venv

echo.
echo Installing Flask...
IF EXIST .\venv\Scripts\pip.exe (
    .\venv\Scripts\pip.exe install flask requests beautifulsoup4 duckduckgo-search
) ELSE IF EXIST .\venv\bin\pip.exe (
    .\venv\bin\pip.exe install flask requests beautifulsoup4 duckduckgo-search
) ELSE (
    echo Error: pip not found.
)

echo.
echo Installation complete! You can now run start.bat to open the app.
pause























