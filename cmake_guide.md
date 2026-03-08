# Blender MCP Server - Build Guide

**Version:** 1.0  
**Last Updated:** March 2026  
**Platforms:** Windows 64-bit (MSI), macOS Silicon (DMG)

---

## Table of Contents

1. [Overview](#overview)
2. [Preparation](#preparation)
3. [Windows 64-bit MSI Build](#windows-64-bit-msi-build)
4. [macOS Silicon DMG Build](#macos-silicon-dmg-build)
5. [CI/CD Automation](#cicd-automation)
6. [Testing and Verification](#testing-and-verification)
7. [Distribution](#distribution)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This guide describes the build and packaging process for Blender MCP Server for:
- **Windows 64-bit** (.msi installer)
- **macOS Silicon** (.dmg installer)

### Build Outputs

| Platform | Output | Size | Time |
|----------|--------|------|------|
| Windows x64 | .msi | ~50MB | 5-10 min |
| macOS Silicon | .dmg | ~45MB | 5-8 min |
| macOS Universal | .dmg | ~80MB | 10-15 min |

---

## Preparation

### Common Requirements

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.11+ | Same version as Blender |
| Node.js | 18+ | For web interface |
| Git | Latest | Version control |

### Project Structure

```
blender-mcp/
├── src/                          # Source code
│   ├── server/
│   ├── llm/
│   ├── prompts/
│   └── web_interface/
├── addon/                        # Blender addon
├── build/                        # Build scripts
│   ├── windows/
│   │   ├── installer.wxs
│   │   └── build.ps1
│   └── macos/
│       ├── entitlements.plist
│       └── build.sh
├── dist/                         # Output packages
└── requirements.txt
```

---

## Windows 64-bit MSI Build

### Requirements

```powershell
# Install Python
winget install Python.Python.3.11

# Install WiX Toolset (for MSI)
winget install WixToolset.WixToolset

# Install Node.js (optional, for web UI)
winget install OpenJS.NodeJS.LTS
```

### Environment Setup

```powershell
# Create project directory
mkdir C:\dev\blender-mcp
cd C:\dev\blender-mcp

# Clone repository
git clone https://github.com/your-org/blender-mcp.git .

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller cx_Freeze
```

### Create Executable with PyInstaller

**File: `build/windows/pyinstaller_spec.py`**

```python
# PyInstaller spec file for Blender MCP Server
from PyInstaller.utils.hooks import collect_submodules
import os

project_root = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(project_root, '..', '..', 'src')

a = Analysis(
    [os.path.join(src_dir, 'server', 'websocket_server.py')],
    pathex=[src_dir],
    binaries=[],
    datas=[
        (os.path.join(src_dir, 'web_interface', 'index.html'), 'web_interface'),
        (os.path.join(src_dir, '..', 'requirements.txt'), '.'),
    ],
    hiddenimports=[
        'websockets',
        'aiohttp',
        'requests',
        'anthropic',
        'openai',
    ] + collect_submodules('bpy'),
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BlenderMCPServer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'icon.ico'),
)
```

**Run build:**

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Build executable
pyinstaller build/windows/pyinstaller_spec.py --clean

# Output will be in dist/BlenderMCPServer.exe
```

### Create WiX Installer

**File: `build/windows/installer.wxs`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" 
           Name="Blender MCP Server" 
           Language="1033" 
           Version="1.0.0" 
           Manufacturer="Blender MCP Team" 
           UpgradeCode="PUT-YOUR-UPGRADE-CODE-HERE">
    
    <Package InstallerVersion="200" 
             Compressed="yes" 
             InstallScope="perMachine" 
             Description="Blender MCP Server Installer"/>
    
    <MajorUpgrade DowngradeErrorMessage="A newer version of [ProductName] is already installed."/>
    <MediaTemplate EmbedCab="yes"/>
    
    <!-- Features -->
    <Feature Id="MainApplication" Title="Blender MCP Server" Level="1">
      <ComponentGroupRef Id="ProductComponents"/>
      <ComponentRef Id="ApplicationShortcut"/>
    </Feature>
    
    <!-- UI -->
    <UI>
      <UIRef Id="WixUI_InstallDir"/>
    </UI>
    <Property Id="WIXUI_INSTALLDIR" Value="INSTALLFOLDER"/>
    
    <!-- Directory Structure -->
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFiles64Folder">
        <Directory Id="INSTALLFOLDER" Name="Blender MCP Server">
          
          <!-- Main executable -->
          <Component Id="MainExe" Guid="*">
            <File Id="MainExeFile" 
                  Source="$(var.BuildDir)\dist\BlenderMCPServer.exe" 
                  KeyPath="yes"/>
          </Component>
          
          <!-- Python dependencies -->
          <Component Id="PythonDeps" Guid="*">
            <File Id="RequirementsFile" 
                  Source="$(var.BuildDir)\requirements.txt" 
                  KeyPath="yes"/>
          </Component>
          
          <!-- Web interface -->
          <Directory Id="WebInterface" Name="web_interface">
            <Component Id="WebUI" Guid="*">
              <File Id="IndexHtml" 
                    Source="$(var.BuildDir)\src\web_interface\index.html" 
                    KeyPath="yes"/>
            </Component>
          </Directory>
          
        </Directory>
      </Directory>
      
      <!-- Start Menu Shortcut -->
      <Directory Id="ProgramMenuFolder">
        <Directory Id="ApplicationProgramsFolder" Name="Blender MCP Server">
          <Component Id="ApplicationShortcut" Guid="*">
            <Shortcut Id="ApplicationStartMenuShortcut"
                      Name="Blender MCP Server"
                      Description="Blender MCP Server"
                      Target="[INSTALLFOLDER]BlenderMCPServer.exe"
                      WorkingDirectory="INSTALLFOLDER"/>
            <RemoveFolder Id="ApplicationProgramsFolder" On="uninstall"/>
            <RegistryValue Root="HKCU"
                          Key="Software\BlenderMCP"
                          Name="installed"
                          Type="integer"
                          Value="1"
                          KeyPath="yes"/>
          </Component>
        </Directory>
      </Directory>
    </Directory>
    
    <!-- Environment Variables -->
    <Component Id="SetEnvironment" Guid="*" Directory="INSTALLFOLDER">
      <Environment Id="PATH" 
                   Name="PATH" 
                   Value="[INSTALLFOLDER]" 
                   Permanent="no" 
                   Part="last" 
                   Action="set" 
                   System="yes"/>
    </Component>
    
  </Product>
</Wix>
```

### Build MSI with WiX

**File: `build/windows/build.ps1`**

```powershell
# Build script for Windows MSI
param(
    [string]$Version = "1.0.0",
    [string]$OutputDir = "..\..\dist\windows",
    [switch]$SignCode
)

$ErrorActionPreference = "Stop"

Write-Host "=== Blender MCP Server Windows Build ===" -ForegroundColor Cyan
Write-Host "Version: $Version"
Write-Host ""

# Step 1: Setup
Write-Host "[1/6] Setting up environment..." -ForegroundColor Yellow
$BuildDir = Get-Location
$ProjectRoot = $BuildDir.Parent.Parent.FullName

# Step 2: Install Python dependencies
Write-Host "[2/6] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r "$ProjectRoot\requirements.txt" --quiet
pip install pyinstaller --quiet

# Step 3: Build executable with PyInstaller
Write-Host "[3/6] Building executable with PyInstaller..." -ForegroundColor Yellow
pyinstaller "$BuildDir\pyinstaller_spec.py" --clean --distpath "$BuildDir\dist"

# Step 4: Compile WiX source
Write-Host "[4/6] Compiling WiX source..." -ForegroundColor Yellow
$candleExe = "candle.exe"
$lightExe = "light.exe"

& $candleExe -dBuildDir="$BuildDir" -dVersion="$Version" `
    -out "$BuildDir\installer.wixobj" `
    "$BuildDir\installer.wxs"

if ($LASTEXITCODE -ne 0) {
    throw "WiX compilation failed"
}

# Step 5: Build MSI
Write-Host "[5/6] Building MSI installer..." -ForegroundColor Yellow
$MsiPath = "$OutputDir\BlenderMCP-Server-$Version-x64.msi"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

& $lightExe -out $MsiPath "$BuildDir\installer.wixobj"

if ($LASTEXITCODE -ne 0) {
    throw "MSI build failed"
}

# Step 6: Code signing (optional)
if ($SignCode) {
    Write-Host "[6/6] Signing MSI..." -ForegroundColor Yellow
    $signtool = "C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe"
    & $signtool sign /f "certificate.pfx" /p $env:SignPassword $MsiPath
}

# Summary
Write-Host ""
Write-Host "=== Build Complete ===" -ForegroundColor Green
Write-Host "Output: $MsiPath"
Write-Host "Size: $((Get-Item $MsiPath).Length / 1MB) MB"
```

### Run Build

```powershell
cd build\windows
.\build.ps1 -Version "1.0.0" -SignCode:$false

# Output: dist/windows/BlenderMCP-Server-1.0.0-x64.msi
```

### Silent Installation

```powershell
# Silent install
msiexec /i BlenderMCP-Server-1.0.0-x64.msi /quiet

# Install with custom directory
msiexec /i BlenderMCP-Server-1.0.0-x64.msi /quiet INSTALLDIR="C:\Apps\BlenderMCP"

# Uninstall
msiexec /x {PRODUCT-CODE} /quiet
```

---

## macOS Silicon (ARM64) DMG Build

### Requirements

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Python (ARM64)
brew install python@3.11

# Install create-dmg
brew install create-dmg

# Install codesign tools (optional, for notarization)
# Need Apple Developer ID
```

### Environment Setup

```bash
# Create project directory
mkdir ~/dev/blender-mcp
cd ~/dev/blender-mcp

# Clone repository
git clone https://github.com/your-org/blender-mcp.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller py2app
```

### Create App Bundle with PyInstaller

**File: `build/macos/pyinstaller_spec.py`**

```python
# PyInstaller spec for macOS
from PyInstaller.utils.hooks import collect_submodules
import os
import plistlib

project_root = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(project_root, '..', '..', 'src')

# App info
APP_NAME = 'Blender MCP Server'
BUNDLE_ID = 'com.blender.mcp.server'
VERSION = '1.0.0'

a = Analysis(
    [os.path.join(src_dir, 'server', 'websocket_server.py')],
    pathex=[src_dir],
    binaries=[],
    datas=[
        (os.path.join(src_dir, 'web_interface', 'index.html'), 'web_interface'),
        (os.path.join(src_dir, '..', 'requirements.txt'), '.'),
    ],
    hiddenimports=[
        'websockets',
        'aiohttp',
        'requests',
        'anthropic',
        'openai',
    ] + collect_submodules('bpy'),
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',  # Silicon
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'icon.icns'),
)

# Create app bundle
app = BUNDLE(
    exe,
    name=f'{APP_NAME}.app',
    icon=exe.icon,
    bundle_identifier=BUNDLE_ID,
    version=VERSION,
    info_plist={
        'CFBundleName': APP_NAME,
        'CFBundleDisplayName': APP_NAME,
        'CFBundleIdentifier': BUNDLE_ID,
        'CFBundleVersion': VERSION,
        'CFBundleShortVersionString': VERSION,
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'CFBundleExecutable': os.path.basename(exe.name),
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '12.0',  # macOS Monterey
        'LSArchitecturePriority': ['arm64'],
    }
)
```

### Entitlements File

**File: `build/macos/entitlements.plist`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- App Sandbox -->
    <key>com.apple.security.app-sandbox</key>
    <false/>
    
    <!-- Network -->
    <key>com.apple.security.network.server</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
    
    <!-- Files -->
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
    
    <!-- Python scripting -->
    <key>com.apple.security.scripting-targets</key>
    <true/>
    
    <!-- Hardened Runtime -->
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
</dict>
</plist>
```

### Build Script

**File: `build/macos/build.sh`**

```bash
#!/bin/bash
set -e

# Configuration
VERSION=${1:-"1.0.0"}
OUTPUT_DIR="../../dist/macos"
APP_NAME="Blender MCP Server"
BUNDLE_ID="com.blender.mcp.server"

echo "=== Blender MCP Server macOS Build ==="
echo "Version: $VERSION"
echo ""

# Colors
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Step 1: Setup
echo -e "${YELLOW}[1/7] Setting up environment...${NC}"
BUILD_DIR=$(pwd)
PROJECT_ROOT=$(cd "$BUILD_DIR/../.." && pwd)

# Step 2: Install dependencies
echo -e "${YELLOW}[2/7] Installing Python dependencies...${NC}"
pip install -r "$PROJECT_ROOT/requirements.txt" --quiet
pip install pyinstaller --quiet

# Step 3: Build with PyInstaller
echo -e "${YELLOW}[3/7] Building app bundle with PyInstaller...${NC}"
pyinstaller "$BUILD_DIR/pyinstaller_spec.py" --clean

# Step 4: Codesign (if certificate available)
echo -e "${YELLOW}[4/7] Code signing...${NC}"
if security find-identity -v -p codesigning | grep -q "Developer ID"; then
    CERT=$(security find-identity -v -p codesigning | grep "Developer ID" | head -1 | awk -F'"' '{print $2}')
    echo "Using certificate: $CERT"
    
    codesign --force --deep --sign "$CERT" \
        --entitlements "$BUILD_DIR/entitlements.plist" \
        "$BUILD_DIR/dist/$APP_NAME.app"
    
    echo "✓ Code signed"
else
    echo "⚠ No signing certificate found, skipping codesign"
fi

# Step 5: Create DMG
echo -e "${YELLOW}[5/7] Creating DMG installer...${NC}"
mkdir -p "$OUTPUT_DIR"

DMG_PATH="$OUTPUT_DIR/${APP_NAME}-$VERSION-Silicon.dmg"

# Remove old DMG
rm -f "$DMG_PATH"

# Create DMG with create-dmg
if command -v create-dmg &> /dev/null; then
    create-dmg \
        --volname "$APP_NAME" \
        --volicon "$BUILD_DIR/icon.icns" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "$APP_NAME.app" 150 150 \
        --app-drop-link 450 150 \
        --hide-extension "$APP_NAME.app" \
        "$DMG_PATH" \
        "$BUILD_DIR/dist/$APP_NAME.app"
else
    # Fallback: simple DMG creation
    hdiutil create -volname "$APP_NAME" -srcfolder "$BUILD_DIR/dist/$APP_NAME.app" \
        -ov -format UDZO "$DMG_PATH"
fi

echo "✓ DMG created: $DMG_PATH"

# Step 6: Notarization (optional, requires Apple ID)
echo -e "${YELLOW}[6/7] Notarization...${NC}"
if [ -n "$APPLE_ID" ] && [ -n "$APPLE_APP_PASSWORD" ]; then
    echo "Submitting for notarization..."
    
    xcrun notarytool submit "$DMG_PATH" \
        --apple-id "$APPLE_ID" \
        --password "$APPLE_APP_PASSWORD" \
        --team-id "$TEAM_ID" \
        --wait
    
    # Staple notarization ticket
    xcrun stapler staple "$DMG_PATH"
    echo "✓ Notarized"
else
    echo "⚠ No Apple ID credentials, skipping notarization"
fi

# Step 7: Verify
echo -e "${YELLOW}[7/7] Verifying build...${NC}"
echo "DMG Size: $(du -h "$DMG_PATH" | cut -f1)"
echo "Contents:"
ls -la "$OUTPUT_DIR"

# Summary
echo ""
echo -e "${GREEN}=== Build Complete ===${NC}"
echo "Output: $DMG_PATH"
echo ""
echo "Installation:"
echo "  1. Open $DMG_PATH"
echo "  2. Drag $APP_NAME.app to Applications"
echo "  3. Run from Applications folder"
```

### Run Build

```bash
cd build/macos
chmod +x build.sh

# Basic build
./build.sh 1.0.0

# With notarization (set env vars first)
export APPLE_ID="your@apple.id"
export APPLE_APP_PASSWORD="app-specific-password"
export TEAM_ID="YOUR_TEAM_ID"
./build.sh 1.0.0
```

### Universal Binary (Intel + Silicon)

**File: `build/macos/build_universal.sh`**

```bash
#!/bin/bash
# Build universal binary for both Intel and Apple Silicon

set -e

VERSION=${1:-"1.0.0"}
BUILD_DIR=$(pwd)
DIST_DIR="$BUILD_DIR/dist"

echo "=== Building Universal Binary ==="

# Build for Intel (x86_64)
echo "[1/3] Building Intel binary..."
arch -x86_64 pyinstaller "$BUILD_DIR/pyinstaller_spec.py" \
    --clean \
    --target-arch=x86_64 \
    --distpath "$DIST_DIR/intel"

# Build for Silicon (arm64)
echo "[2/3] Building Silicon binary..."
arch -arm64 pyinstaller "$BUILD_DIR/pyinstaller_spec.py" \
    --clean \
    --target-arch=arm64 \
    --distpath "$DIST_DIR/silicon"

# Merge binaries
echo "[3/3] Creating universal binary..."
lipo -create \
    "$DIST_DIR/intel/Blender MCP Server/Blender MCP Server" \
    "$DIST_DIR/silicon/Blender MCP Server/Blender MCP Server" \
    -output "$DIST_DIR/universal/Blender MCP Server/Blender MCP Server"

echo "✓ Universal binary created"
```

---

## CI/CD Automation

### GitHub Actions Workflow

**File: `.github/workflows/build.yml`**

```yaml
name: Build Installers

on:
  push:
    tags:
      - 'v*.*.*'
  workflow_dispatch:

jobs:
  build-windows:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pyinstaller
    
    - name: Build MSI
      run: |
        cd build/windows
        .\build.ps1 -Version ${{ github.ref_name }}
    
    - name: Upload artifact
      uses: actions/upload-artifact@v4
      with:
        name: windows-installer
        path: dist/windows/*.msi

  build-macos:
    runs-on: macos-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pyinstaller
        brew install create-dmg
    
    - name: Build DMG
      run: |
        cd build/macos
        ./build.sh ${{ github.ref_name }}
    
    - name: Upload artifact
      uses: actions/upload-artifact@v4
      with:
        name: macos-installer
        path: dist/macos/*.dmg

  release:
    needs: [build-windows, build-macos]
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Download artifacts
      uses: actions/download-artifact@v4
    
    - name: Create Release
      uses: softprops/action-gh-release@v1
      with:
        files: |
          windows-installer/*.msi
          macos-installer/*.dmg
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Testing and Verification

### Windows Testing

```powershell
# Test installation
msiexec /i dist/windows/BlenderMCP-Server-1.0.0-x64.msi /quiet /norestart

# Verify installation
Test-Path "C:\Program Files\Blender MCP Server\BlenderMCPServer.exe"

# Test execution
& "C:\Program Files\Blender MCP Server\BlenderMCPServer.exe" --help

# Test uninstallation
msiexec /x {PRODUCT-CODE} /quiet
```

### macOS Testing

```bash
# Test DMG
hdiutil attach dist/macos/Blender\ MCP\ Server-1.0.0-Silicon.dmg

# Verify app bundle
ls -la /Volumes/Blender\ MCP\ Server/

# Test execution
/Volumes/Blender\ MCP\ Server/Blender\ MCP\ Server.app/Contents/MacOS/Blender\ MCP\ Server --help

# Detach
hdiutil detach /Volumes/Blender\ MCP\ Server
```

### Code Signing Verification

**Windows:**
```powershell
# Verify signature
signtool verify /pa "dist/windows/BlenderMCP-Server-1.0.0-x64.msi"
```

**macOS:**
```bash
# Verify signature
codesign --verify --verbose dist/macos/Blender\ MCP\ Server-1.0.0-Silicon.dmg

# Check notarization
spctl --assess --type install dist/macos/Blender\ MCP\ Server-1.0.0-Silicon.dmg
```

---

## Distribution

### Release Checklist

- [ ] Build Windows MSI (x64)
- [ ] Build macOS DMG (Silicon + Universal option)
- [ ] Code sign all installers
- [ ] Notarize macOS installer
- [ ] Test on clean VMs
- [ ] Upload to GitHub Releases
- [ ] Update documentation
- [ ] Announce release

### System Requirements

**Windows:**
- Windows 10/11 (64-bit)
- Python 3.11+ (or use bundled)
- Blender 4.0+
- 500MB free space

**macOS:**
- macOS 12.0+ (Monterey or later)
- Apple Silicon (M1/M2/M3) or Intel
- Python 3.11+ (or use bundled)
- Blender 4.0+
- 500MB free space

---

## Troubleshooting

### Common Issues

**Windows:**

| Issue | Solution |
|-------|----------|
| MSI build fails | Check WiX Toolset installation |
| Missing DLLs | Add to PyInstaller hiddenimports |
| Code sign fails | Check certificate validity |

**macOS:**

| Issue | Solution |
|-------|----------|
| App won't open | Codesign with valid certificate |
| Notarization fails | Check entitlements.plist |
| Universal binary fails | Ensure both archs build separately |

### Debug Build

**Windows:**
```powershell
.\build.ps1 -Version "1.0.0-dev" -SignCode:$false
```

**macOS:**
```bash
# Skip codesign and notarization
./build.sh 1.0.0-dev
```

---

## Quick Reference

### Build Commands

```bash
# Windows
cd build\windows
.\build.ps1 -Version "1.0.0"

# macOS
cd build/macos
./build.sh 1.0.0
```

### Installation Commands

```bash
# Windows silent install
msiexec /i BlenderMCP-Server-1.0.0-x64.msi /quiet

# macOS install
# Open DMG and drag to Applications
```

### Output Locations

```
dist/
├── windows/
│   └── BlenderMCP-Server-1.0.0-x64.msi
└── macos/
    └── Blender MCP Server-1.0.0-Silicon.dmg
```

---

## Next Steps

1. **Automate:** Setup GitHub Actions CI/CD
2. **Sign:** Get code signing certificates
3. **Test:** Test on clean VMs
4. **Distribute:** GitHub Releases, Homebrew, winget

---

**Build Complete!** 🎉

---

**Document Version:** 1.0  
**Last Updated:** March 2026  
**Author:** Blender MCP Team
