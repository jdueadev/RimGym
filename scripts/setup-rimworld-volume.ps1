# Setup RimWorld Docker Volume (Windows PowerShell)

param(
    [Parameter(Mandatory = $true)]
    [string]$RimWorldPath,
    
    [Parameter(Mandatory = $false)]
    [string]$VolumeName = "rimworld-data"
)

# Validate RimWorld path
if (-not (Test-Path $RimWorldPath)) {
    Write-Error "RimWorld directory not found: $RimWorldPath"
    exit 1
}

# Check directory contents to help debug
Write-Host "Checking RimWorld directory contents..." -ForegroundColor Yellow
$files = Get-ChildItem -Path $RimWorldPath -Name | Select-Object -First 10
Write-Host "Found files: $($files -join ', ')" -ForegroundColor Gray
Write-Host ""

# Look for RimWorldLinux executable (might be in subdirectory from DepotDownloader)
$rimworldExe = $null
$possiblePaths = @(
    (Join-Path $RimWorldPath "RimWorldLinux"),
    (Join-Path $RimWorldPath "linux/RimWorldLinux"),
    (Get-ChildItem -Path $RimWorldPath -Recurse -Filter "RimWorldLinux" -File -ErrorAction SilentlyContinue | Select-Object -First 1).FullName
)

foreach ($path in $possiblePaths) {
    if ($path -and (Test-Path $path)) {
        $rimworldExe = $path
        Write-Host "✓ Found RimWorldLinux at: $rimworldExe" -ForegroundColor Green
        # Adjust RimWorldPath to the actual directory containing the executable
        $RimWorldPath = Split-Path $rimworldExe -Parent
        break
    }
}

if (-not $rimworldExe) {
    Write-Error "RimWorldLinux executable not found in: $RimWorldPath"
    Write-Error "Expected to find 'RimWorldLinux' file (Linux executable)"
    Write-Error ""
    Write-Error "If you used DepotDownloader, check the directory structure."
    Write-Error "You may need to point to a subdirectory containing the actual game files."
    exit 1
}

Write-Host "Setting up RimWorld Docker volume..." -ForegroundColor Cyan
Write-Host "Source: $RimWorldPath" -ForegroundColor White
Write-Host "Volume: $VolumeName" -ForegroundColor White
Write-Host ""

# Create volume if it doesn't exist
$volumeExists = docker volume inspect $VolumeName 2>$null
if (-not $volumeExists) {
    Write-Host "Creating Docker volume: $VolumeName" -ForegroundColor Yellow
    docker volume create $VolumeName
}

# Convert Windows path to Docker-compatible format
$dockerPath = $RimWorldPath -replace '\\', '/' -replace '^([A-Z]):', '//$1'

# Copy RimWorld to volume
Write-Host "Copying RimWorld files to Docker volume (this may take a minute)..." -ForegroundColor Yellow

docker run --rm `
    -v "${dockerPath}:/source:ro" `
    -v "${VolumeName}:/dest" `
    alpine sh -c "cp -r /source/. /dest/ && find /dest -name 'RimWorldLinux' -type f -exec chmod +x {} \;"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ RimWorld Docker volume setup complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Verify with:" -ForegroundColor Cyan
    Write-Host "  docker run --rm -v ${VolumeName}:/opt/rimworld alpine ls -la /opt/rimworld" -ForegroundColor White
    Write-Host ""
    Write-Host "Use in tests:" -ForegroundColor Cyan
    Write-Host "  docker-compose up test" -ForegroundColor White
    Write-Host "  or" -ForegroundColor White
    Write-Host "  docker run --rm -v ${VolumeName}:/opt/rimworld rimworld-ml-bridge test" -ForegroundColor White
}
else {
    Write-Error "Failed to setup Docker volume"
    exit 1
}
