# Verify and Fix RimWorld Docker Volume
param(
    [Parameter(Mandatory = $false)]
    [string]$RimWorldPath = "C:\RimworldLinux"
)

Write-Host "🔍 Checking rimworld-data volume..." -ForegroundColor Cyan
Write-Host ""

# Check if volume exists
$volumeExists = docker volume inspect rimworld-data 2>$null
if (-not $volumeExists) {
    Write-Host "❌ Volume 'rimworld-data' does not exist" -ForegroundColor Red
    Write-Host "Creating volume..." -ForegroundColor Yellow
    docker volume create rimworld-data
}

# Check volume contents
Write-Host "Checking volume contents..." -ForegroundColor Yellow
$volumeContents = docker run --rm -v rimworld-data:/data alpine sh -c "ls -la /data 2>/dev/null | wc -l"

if ($volumeContents -le 3) {
    Write-Host "❌ Volume is empty (only has . and ..)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Running setup script to populate volume..." -ForegroundColor Yellow
    & "$PSScriptRoot\setup-rimworld-volume.ps1" -RimWorldPath $RimWorldPath
}
else {
    Write-Host "✅ Volume has content" -ForegroundColor Green
    Write-Host ""
    Write-Host "Volume contents:" -ForegroundColor Cyan
    docker run --rm -v rimworld-data:/data alpine ls -la /data
    
    # Check for RimWorldLinux executable specifically
    $hasExecutable = docker run --rm -v rimworld-data:/data alpine test -f /data/RimWorldLinux
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ RimWorldLinux executable found!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Ready to run tests:" -ForegroundColor Cyan
        Write-Host "  docker-compose up test" -ForegroundColor White
    }
    else {
        Write-Host ""
        Write-Host "❌ RimWorldLinux executable not found!" -ForegroundColor Red
        Write-Host "Re-running setup script..." -ForegroundColor Yellow
        & "$PSScriptRoot\setup-rimworld-volume.ps1" -RimWorldPath $RimWorldPath
    }
}
