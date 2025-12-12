#!/usr/bin/env pwsh
# Package RimTCP (RimWorld mod) for release or Steam Workshop upload

param(
    [Parameter(Mandatory = $true)]
    [string]$Version,
    
    [Parameter(Mandatory = $false)]
    [string]$OutputDir = "release",
    
    [Parameter(Mandatory = $false)]
    [switch]$SkipBuild,
    
    [Parameter(Mandatory = $false)]
    [switch]$CreateZip
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RimTCP Package Builder" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Version: $Version" -ForegroundColor Yellow
Write-Host "Output:  $OutputDir" -ForegroundColor Yellow
Write-Host ""

# Validate version format
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Error "Invalid version format. Use semantic versioning (e.g., 1.0.0)"
    exit 1
}

# Build if not skipped
if (-not $SkipBuild) {
    Write-Host "[1/7] Building C# project..." -ForegroundColor Green
    
    # Restore NuGet packages
    Write-Host "  → Restoring NuGet packages..."
    nuget restore src\RimTCP\RimTCP\RimTCP.sln | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "NuGet restore failed"
        exit 1
    }
    
    # Build solution
    Write-Host "  → Building solution (Release configuration)..."
    msbuild src\RimTCP\RimTCP\RimTCP.sln /p:Configuration=Release /p:Platform="Any CPU" /verbosity:minimal
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed"
        exit 1
    }
    
    Write-Host "  ✓ Build successful" -ForegroundColor Green
}
else {
    Write-Host "[1/7] Skipping build (using existing assemblies)..." -ForegroundColor Yellow
}

# Verify no native DLLs
Write-Host "[2/7] Verifying assemblies..." -ForegroundColor Green
$nativeDlls = Get-ChildItem -Path "src\RimTCP\1.6\Assemblies" -Filter "*csharp_ext*.dll" -ErrorAction SilentlyContinue
if ($nativeDlls) {
    Write-Error "ERROR: Native DLLs found in output! $($nativeDlls.Name -join ', ')"
    Write-Error "These will crash RimWorld. Run build cleanup."
    exit 1
}
Write-Host "  ✓ No native DLLs found" -ForegroundColor Green

# Create package directory structure
$packageName = "RimTCP-v$Version"
$packagePath = Join-Path $OutputDir $packageName

Write-Host "[3/7] Creating package structure..." -ForegroundColor Green
if (Test-Path $packagePath) {
    Write-Host "  → Removing existing package..."
    Remove-Item -Path $packagePath -Recurse -Force
}
New-Item -ItemType Directory -Path $packagePath -Force | Out-Null

# Copy mod files
Write-Host "[4/7] Copying mod files..." -ForegroundColor Green

Write-Host "  → About/ folder..."
Copy-Item -Path "src\RimTCP\About" -Destination "$packagePath\About" -Recurse -Force

Write-Host "  → 1.6/Assemblies/ folder..."
Copy-Item -Path "src\RimTCP\1.6" -Destination "$packagePath\1.6" -Recurse -Force

Write-Host "  → Protos/ folder..."
Copy-Item -Path "src\shared\Protos" -Destination "$packagePath\Protos" -Recurse -Force

# Copy documentation
Write-Host "  → Documentation..."
Copy-Item -Path "README.md" -Destination "$packagePath\" -Force
if (Test-Path "docs\docker\QUICKSTART.md") { Copy-Item -Path "docs\docker\QUICKSTART.md" -Destination "$packagePath\" -Force }
Copy-Item -Path "CONTRIBUTING.md" -Destination "$packagePath\" -Force

# Copy guides
if (Test-Path "docs\guides") {
    New-Item -ItemType Directory -Path "$packagePath\docs\guides" -Force | Out-Null
    Copy-Item -Path "docs\guides\*" -Destination "$packagePath\docs\guides\" -Recurse -Force
}

# Generate CHANGELOG
Write-Host "[5/7] Generating CHANGELOG..." -ForegroundColor Green
$changelogContent = @"
# Changelog - v$Version

Release date: $(Get-Date -Format 'yyyy-MM-dd')

## Features

- High-performance TCP + Protocol Buffers communication
- Dual-mode operation (Training & Inference)
- Rich colonist state extraction (21 fields, 0.003ms per colonist)
- Triple-threaded Python client (Listener/Inference/Actor)
- Gymnasium-compatible environment wrapper
- Docker-based integration testing

## System Requirements

- RimWorld 1.6+
- Harmony 2.x (automatically loaded from Steam Workshop)
- Python 3.11+ (for ML clients)
- 4GB RAM recommended

## Installation

### For Modders:
1. Extract this folder to your RimWorld Mods/ directory
2. Enable "RimTCP" in the game's mod settings
3. Ensure Harmony is enabled (loaded before RimTCP)
4. Start a game and check Player.log for "[RimTCP]" logs indicating the TCP+Protobuf server started

### For ML Researchers:
```bash
pip install rimgym==$Version
```

See docs/ for detailed usage instructions.

## Full Changelog

See: https://github.com/jmduea/RimGym/releases/tag/v$Version

## Support

- GitHub Issues: https://github.com/jmduea/RimGym/issues
- Documentation: https://jmduea.github.io/RimGym/
- Discussions: https://github.com/jmduea/RimGym/discussions
"@

$changelogContent | Out-File -FilePath "$packagePath\CHANGELOG.md" -Encoding utf8 -Force
Write-Host "  ✓ CHANGELOG.md created" -ForegroundColor Green

# Update About.xml with version
Write-Host "[6/7] Updating About.xml with version..." -ForegroundColor Green
$aboutXmlPath = "$packagePath\About\About.xml"
if (Test-Path $aboutXmlPath) {
    $aboutXml = [xml](Get-Content $aboutXmlPath)
    
    # Update version in description if version node doesn't exist
    if (-not $aboutXml.ModMetaData.modVersion) {
        $versionNode = $aboutXml.CreateElement("modVersion")
        $versionNode.InnerText = $Version
        $aboutXml.ModMetaData.AppendChild($versionNode) | Out-Null
    }
    else {
        $aboutXml.ModMetaData.modVersion = $Version
    }
    
    $aboutXml.Save($aboutXmlPath)
    Write-Host "  ✓ Version $Version written to About.xml" -ForegroundColor Green
}

# Create ZIP archive if requested
if ($CreateZip) {
    Write-Host "[7/7] Creating ZIP archive..." -ForegroundColor Green
    $zipPath = Join-Path $OutputDir "$packageName.zip"
    
    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    
    Compress-Archive -Path "$packagePath\*" -DestinationPath $zipPath -CompressionLevel Optimal
    
    # Calculate SHA256
    $hash = Get-FileHash -Path $zipPath -Algorithm SHA256
    $hash.Hash | Out-File -FilePath "$zipPath.sha256" -NoNewline -Encoding ascii
    
    Write-Host "  ✓ Created: $zipPath" -ForegroundColor Green
    Write-Host "  ✓ SHA256:  $($hash.Hash)" -ForegroundColor Gray
}
else {
    Write-Host "[7/7] Skipping ZIP creation (use -CreateZip to create)..." -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Package created successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Package location: $packagePath" -ForegroundColor Yellow
if ($CreateZip) {
    Write-Host "ZIP archive:      $(Join-Path $OutputDir "$packageName.zip")" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Test the mod by copying to RimWorld/Mods/" -ForegroundColor White
Write-Host "  2. Verify it loads without errors" -ForegroundColor White
Write-Host "  3. Upload to Steam Workshop using SteamCMD or Publishing Tools" -ForegroundColor White
Write-Host ""
Write-Host "For Steam Workshop upload instructions, see:" -ForegroundColor Cyan
Write-Host "  docs/guides/steam-workshop-upload.md" -ForegroundColor White
Write-Host ""
