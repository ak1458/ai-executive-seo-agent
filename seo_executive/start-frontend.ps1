# SEO Executive Frontend Server

Write-Host "Starting SEO Executive Frontend..." -ForegroundColor Green
Write-Host "Frontend will be available at http://localhost:3000" -ForegroundColor Cyan

cd frontend

# Use Python's simple HTTP server
py -m http.server 3000
