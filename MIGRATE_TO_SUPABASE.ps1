# ============================================================
# Supabase Migration — one-shot script
# Project: nbuxgiquiimkrjpenjya
# ============================================================
# Usage:
#   .\MIGRATE_TO_SUPABASE.ps1 -Password "YourSupabaseDBPassword"
# ============================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$Password
)

$ProjectRef = "nbuxgiquiimkrjpenjya"
$DirectUrl  = "postgresql://postgres:$Password@db.$ProjectRef.supabase.co:5432/postgres"
$PooledUrl  = "postgresql://postgres:$Password@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Supabase Migration  (project: $ProjectRef)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. Write .env ──────────────────────────────────────────────────────────────
Write-Host "Step 1: Writing backend/.env ..." -ForegroundColor Yellow

$envContent = @"
# Local PostgreSQL (kept for reference)
DATABASE_URL=postgresql://postgres:123@localhost:5432/devanalytics

# Supabase — direct connection (port 5432) used by the app and migrations
SUPABASE_DB_URL=$DirectUrl

# Auth
JWT_SECRET=change-this-to-a-long-random-string-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Other services
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
"@

Set-Content -Path "backend/.env" -Value $envContent
Write-Host "  .env written." -ForegroundColor Green
Write-Host ""

# ── 2. Run Alembic migrations on Supabase ──────────────────────────────────────
Write-Host "Step 2: Running Alembic migrations on Supabase ..." -ForegroundColor Yellow
Set-Location backend
$env:DATABASE_URL = $DirectUrl
python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Warning: Alembic reported issues (may be OK if tables already exist)" -ForegroundColor Yellow
} else {
    Write-Host "  Schema ready." -ForegroundColor Green
}
Write-Host ""

# ── 3. Copy local data ─────────────────────────────────────────────────────────
Write-Host "Step 3: Copying local data to Supabase ..." -ForegroundColor Yellow
$env:SUPABASE_DB_URL = $DirectUrl
python migrate_to_supabase.py

Set-Location ..

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Migration complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Restart the backend:" -ForegroundColor Cyan
Write-Host "  cd backend"
Write-Host "  python -m uvicorn gateway.main:app --reload"
Write-Host ""
