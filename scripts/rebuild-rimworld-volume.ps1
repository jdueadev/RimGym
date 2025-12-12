# Rebuild RimWorld Docker Volume (Windows PowerShell)
#
# Use when your rimworld-data volume has stale content (e.g., legacy Mods/RimworldMLBridge).
# This will REMOVE the Docker volume and re-populate it from a local RimWorld Linux install.

param(
    [Parameter(Mandatory = $true)]
    [string]$RimWorldPath,

    [Parameter(Mandatory = $false)]
    [string]$VolumeName = "rimworld-data",

    [Parameter(Mandatory = $false)]
    [switch]$Force
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker CLI not found. Install Docker Desktop (Windows) and try again."
    exit 1
}

if (-not $Force) {
    Write-Host "This will DELETE the Docker volume '$VolumeName' and all saved game data inside it." -ForegroundColor Yellow
    Write-Host "Re-run with -Force to proceed." -ForegroundColor Yellow
    exit 2
}

Write-Host "Stopping any compose stacks (best-effort)..." -ForegroundColor Cyan
try { docker compose down | Out-Null } catch { }
try { docker-compose down | Out-Null } catch { }

Write-Host "Removing volume: $VolumeName" -ForegroundColor Cyan
try {
    docker volume rm -f $VolumeName | Out-Null
}
catch {
    # ignore if volume doesn't exist
}

Write-Host "Recreating volume from: $RimWorldPath" -ForegroundColor Cyan
& (Join-Path $PSScriptRoot "setup-rimworld-volume.ps1") -RimWorldPath $RimWorldPath -VolumeName $VolumeName
