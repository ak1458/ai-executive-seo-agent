# SEO Executive Startup Script for Windows

Write-Host "Starting SEO Executive..." -ForegroundColor Green

# Check if Redis is running
try {
    $redisPing = redis-cli ping 2>$null
    if ($redisPing -ne "PONG") {
        Write-Host "Starting Redis..." -ForegroundColor Yellow
        Start-Process redis-server --daemonize yes -WindowStyle Hidden
        Start-Sleep 2
    } else {
        Write-Host "Redis is already running" -ForegroundColor Green
    }
} catch {
    Write-Host "Redis not found. Please install Redis or start it manually." -ForegroundColor Red
    Write-Host "Continuing without Redis (Celery tasks will not work)..." -ForegroundColor Yellow
}

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Yellow
cd backend
.\venv\Scripts\python.exe -c "from app.models.database import init_db; init_db()"

# Start Celery worker (optional, in background)
Write-Host "Starting Celery worker..." -ForegroundColor Yellow
Start-Process .\venv\Scripts\python.exe -ArgumentList "-m", "celery", "-A", "app.worker", "worker", "--loglevel=info" -WindowStyle Hidden

# Start FastAPI backend
Write-Host "Starting FastAPI backend on http://localhost:8000" -ForegroundColor Green
Write-Host "API docs available at http://localhost:8000/docs" -ForegroundColor Cyan

# Start the server
.\venv\Scripts\uvicorn.exe app.main:app --host 0.0.0.0 --port 8000 --reload
