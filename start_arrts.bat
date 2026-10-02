@echo off
echo ============================================
echo  ARRTS - Advanced Rail Routing and Ticketing
echo ============================================
echo.

REM Check if data exists
if not exist "data\out\stops.csv" (
    echo [STEP 1] Downloading railway timetable data from NTES...
    echo This may take 5-10 minutes for the first run.
    echo.
    set PYTHONIOENCODING=utf-8
    python generate_data.py
    if errorlevel 1 (
        echo.
        echo WARNING: Some data may not have been downloaded.
        echo The app will start but search results may be limited.
    )
) else (
    echo [INFO] Timetable data found. Skipping download.
    echo To refresh data: python generate_data.py
)

echo.
echo [STEP 2] Starting ARRTS server...
echo Open your browser at: http://localhost:8000
echo.
set PYTHONIOENCODING=utf-8
python app.py
