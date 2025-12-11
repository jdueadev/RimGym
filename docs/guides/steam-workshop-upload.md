# Steam Workshop Upload Guide

This guide covers uploading RimWorld ML Bridge to the Steam Workshop.

## Prerequisites

1. **RimWorld** installed via Steam
2. **Steam account** with RimWorld ownership
3. **Packaged mod** (use `scripts/package-mod.ps1`)
4. **SteamCMD** (optional, for automated uploads)

## Method 1: RimWorld's Built-in Publishing Tools (Recommended)

### Step 1: Prepare Mod for Upload

1. Build and package the mod:

   ```powershell
   .\scripts\package-mod.ps1 -Version 1.0.0 -CreateZip
   ```

2. Copy packaged mod to RimWorld Mods folder:

   ```powershell
   Copy-Item -Path "release\RimworldMLBridge-v1.0.0\*" `
             -Destination "C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Mods\RimworldMLBridge" `
             -Recurse -Force
   ```

### Step 2: Create Preview Image

Create a 640x360 PNG image showcasing the mod:

- Show the connection working (Python client connected)
- Include project logo or RimWorld screenshot
- Save as `About/Preview.png` in the mod folder

**Tips**:

- Use clear, readable text
- Highlight key features visually
- Keep it simple and professional

### Step 3: Update About.xml

Ensure `About/About.xml` contains all required metadata:

```xml
<?xml version="1.0" encoding="utf-8"?>
<ModMetaData>
  <name>RimWorld ML Bridge</name>
  <author>jmduea</author>
  <packageId>jmduea.rimworldmlbridge</packageId>
  <supportedVersions>
    <li>1.6</li>
  </supportedVersions>
  <modVersion>0.5.0</modVersion>
  <description>Machine Learning Bridge for RimWorld - Connect AI agents via TCP + Protocol Buffers.

Features:
- High-performance TCP communication
- Rich state extraction (21 colonist fields)
- Dual-mode operation (Training/Inference)
- Python client with Gymnasium wrapper
- Docker support for integration testing

Requires Harmony 2.x (loads automatically from Steam Workshop).

Documentation: https://github.com/jmduea/RimworldMLBridge
  </description>
  <modDependencies>
    <li>
      <packageId>brrainz.harmony</packageId>
      <displayName>Harmony</displayName>
      <steamWorkshopUrl>steam://url/CommunityFilePage/2009463077</steamWorkshopUrl>
    </li>
  </modDependencies>
</ModMetaData>
```

### Step 4: Upload via RimWorld

1. Launch RimWorld
2. Go to **Mods** menu
3. Select **"RimWorld ML Bridge"** from your mod list
4. Click **"Upload to Workshop"** button
5. Fill in Steam Workshop details:
   - **Title**: RimWorld ML Bridge
   - **Description**: (Copy from About.xml, add formatting)
   - **Tags**: Select relevant tags (Gameplay, Tools, etc.)
   - **Visibility**: Public
6. Click **"Upload"**

### Step 5: Update Workshop Page

After upload, visit your Workshop page to:

- Add additional screenshots
- Format description with BBCode
- Add links to documentation
- Enable discussions and comments

## Method 2: SteamCMD (Automated)

For automated publishing in CI/CD:

### Install SteamCMD

**Windows**:

```powershell
# Download SteamCMD
Invoke-WebRequest -Uri "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip" `
                  -OutFile "steamcmd.zip"
Expand-Archive steamcmd.zip -DestinationPath "C:\steamcmd"
```

**Linux**:

```bash
# Install SteamCMD
sudo add-apt-repository multiverse
sudo apt update
sudo apt install steamcmd
```

### Create Workshop Config

Create `workshop_config.vdf`:

```vdf
"workshopitem"
{
  "appid" "294100"  // RimWorld App ID
  "publishedfileid" "YOUR_WORKSHOP_ID"  // Leave blank for first upload
  "contentfolder" "C:\\path\\to\\RimworldMLBridge"
  "previewfile" "C:\\path\\to\\About\\Preview.png"
  "visibility" "0"  // 0 = public, 1 = friends only, 2 = private
  "title" "RimWorld ML Bridge"
  "description" "Your description here"
  "changenote" "Initial release v1.0.0"
  
  "tags"
  {
    "0" "1.6"
  }
}
```

### Upload Script

Create `upload-workshop.ps1`:

```powershell
param(
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [Parameter(Mandatory=$true)]
    [SecureString]$Password,
    
    [Parameter(Mandatory=$true)]
    [string]$ConfigPath
)

$plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($Password)
)

& "C:\steamcmd\steamcmd.exe" `
    +login $Username $plainPassword `
    +workshop_build_item $ConfigPath `
    +quit

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Upload successful!" -ForegroundColor Green
} else {
    Write-Error "Upload failed with code $LASTEXITCODE"
}
```

**Note**: For security, use Steam Guard and store credentials securely (e.g., GitHub Secrets for CI/CD).

### Run Upload

```powershell
.\upload-workshop.ps1 -Username "yourusername" `
                       -Password (Read-Host -AsSecureString "Password") `
                       -ConfigPath ".\workshop_config.vdf"
```

## Method 3: GitHub Actions (CI/CD)

For automated Workshop updates on release:

```yaml
name: Publish to Steam Workshop

on:
  release:
    types: [published]

jobs:
  publish-workshop:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Mod Package
        run: ./scripts/package-mod.ps1 -Version ${{ github.ref_name }}
      
      - name: Upload to Workshop
        uses: game-ci/steam-deploy@v3
        with:
          username: ${{ secrets.STEAM_USERNAME }}
          password: ${{ secrets.STEAM_PASSWORD }}
          configVdf: ${{ secrets.STEAM_CONFIG_VDF }}
          appId: 294100
          depot1Path: ./release/RimworldMLBridge-${{ github.ref_name }}
```

## Post-Upload Checklist

- [ ] Verify mod appears in Steam Workshop
- [ ] Test subscribing and downloading via Steam
- [ ] Check that all files are included
- [ ] Verify preview image displays correctly
- [ ] Test mod loads in RimWorld without errors
- [ ] Update GitHub README with Workshop link
- [ ] Announce release in community channels

## Updating the Mod

For updates:

1. Increment version in `package-mod.ps1`
2. Update `CHANGELOG.md` with changes
3. Rebuild and repackage
4. Upload with new version number
5. Add change notes in Workshop description

## Troubleshooting

### "Failed to upload"

- Check Steam Guard is disabled for this account OR use SteamCMD with web auth
- Verify RimWorld ownership on the account
- Check file paths in config VDF are correct

### "Files not included"

- Ensure `.dll` files are in `1.6/Assemblies/`
- Verify no `.pdb` or native DLL files included
- Check `About.xml` exists and is valid XML

### "Mod doesn't load"

- Test locally before uploading
- Check RimWorld `Player.log` for errors
- Verify Harmony dependency is listed

## Resources

- [RimWorld Modding Wiki](https://rimworldwiki.com/wiki/Modding_Tutorials)
- [Steam Workshop Developer Docs](https://partner.steamgames.com/doc/features/workshop)
- [SteamCMD Documentation](https://developer.valvesoftware.com/wiki/SteamCMD)

---

**Questions?** Open an issue on GitHub or ask in the Steam Workshop discussions.
