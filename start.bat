@echo off
setlocal EnableDelayedExpansion

title DevAnalytics - Start Script
color 0A

echo.
echo  ============================================================
echo   DevAnalytics Platform - Local Development Startup
echo  ============================================================
echo.

:: ── Check prerequisites ───────────────────────────────────────────────────────

echo [1/5] Checking prerequisites...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found. Please install Python 3.10+ and add it to PATH.
    pause & exit /b 1
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Node.js not found. Please install Node.js 18+ and add it to PATH.
    pause & exit /b 1
)

where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo  [WARN]  Docker not found. Infrastructure services (Postgres, Redis, RabbitMQ)
    echo          must be running manually if you skip Docker.
)

echo  [OK] Prerequisites checked.
echo.

:: ── Copy .env if missing ──────────────────────────────────────────────────────

echo [2/5] Checking environment files...

if not exist "backend\.env" (
    if exist "backend\.env.example" (
        copy "backend\.env.example" "backend\.env" >nul
        echo  [INFO] Created backend\.env from .env.example
        echo  [WARN] Please edit backend\.env and fill in your DATABASE_URL and secrets.
    ) else (
        echo  [WARN] backend\.env not found and no .env.example to copy from.
    )
) else (
    echo  [OK] backend\.env exists.
)

if not exist "frontend\.env" (
    if exist "frontend\.env.example" (
        copy "frontend\.env.example" "frontend\.env" >nul
        echo  [INFO] Created frontend\.env from .env.example
    )
) else (
    echo  [OK] frontend\.env exists.
)
echo.

:: ── Start infrastructure via Docker Compose ───────────────────────────────────

echo [3/5] Starting infrastructure (Postgres, Redis, RabbitMQ)...

where docker-compose >nul 2>&1
if %errorlevel% equ 0 (
    docker-compose up -d postgres redis rabbitmq
    if %errorlevel% neq 0 (
        echo  [WARN] docker-compose failed. Make sure Docker Desktop is running.
    ) else (
        echo  [OK] Infrastructure containers started.
        echo  [INFO] Waiting 5 seconds for services to be ready...
        timeout /t 5 /nobreak >nul
    )
) else (
    where docker >nul 2>&1
    if %errorlevel% equ 0 (
        docker compose up -d postgres redis rabbitmq
        if %errorlevel% neq 0 (
            echo  [WARN] docker compose failed. Make sure Docker Desktop is running.
        ) else (
            echo  [OK] Infrastructure containers started.
            timeout /t 5 /nobreak >nul
        )
    ) else (
        echo  [SKIP] Docker not available. Skipping infrastructure startup.
        echo         Make sure Postgres, Redis, and RabbitMQ are running manually.
    )
)
echo.

:: ── Backend setup and start ───────────────────────────────────────────────────

echo [4/5] Starting backend (FastAPI)...

:: Activate virtual environment if it exists
if exist "backend\venv\Scripts\activate.bat" (
    echo  [INFO] Activating virtual environment...
    call backend\venv\Scripts\activate.bat
) else (
    echo  [INFO] No venv found. Creating one...
    python -m venv backend\venv
    call backend\venv\Scripts\activate.bat
    echo  [INFO] Installing backend dependencies...
    pip install -r backend\requirements.txt --quiet
)

:: Run Alembic migrations
echo  [INFO] Running database migrations...
cd backend
alembic upgrade head
if %errorlevel% neq 0 (
    echo  [WARN] Alembic migration failed. Check your DATABASE_URL in backend\.env
) else (
    echo  [OK] Migrations applied.
)
cd ..

:: Start FastAPI in a new window
echo  [INFO] Launching FastAPI server on http://localhost:8000
start "DevAnalytics Backend" cmd /k "cd backend && call venv\Scripts\activate.bat && uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload"

echo  [OK] Backend window opened.
echo.

:: ── Frontend setup and start ──────────────────────────────────────────────────

echo [5/5] Starting frontend (Vite + React)...

if not exist "frontend\node_modules" (
    echo  [INFO] Installing frontend dependencies (first run)...
    cd frontend
    npm install
    cd ..
) else (
    echo  [OK] node_modules already present.
)

:: Start Vite dev server in a new window
echo  [INFO] Launching Vite dev server on http://localhost:5173
start "DevAnalytics Frontend" cmd /k "cd frontend && npm run dev"

echo  [OK] Frontend window opened.
echo.

:: ── Summary ───────────────────────────────────────────────────────────────────

echo  ============================================================
echo   All services started!
echo  ============================================================
echo.
echo   Frontend  :  http://localhost:5173
echo   Backend   :  http://localhost:8000
echo   API Docs  :  http://localhost:8000/docs
echo   RabbitMQ  :  http://localhost:15672  (guest / guest)
echo.
echo   Two new terminal windows have been opened:
echo     - "DevAnalytics Backend"  (FastAPI + uvicorn)
echo     - "DevAnalytics Frontend" (Vite dev server)
echo.
echo   Press any key to close this launcher window.
echo  ============================================================
echo.
pause
endlocal
