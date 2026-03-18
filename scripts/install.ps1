# Installer for bakufu release binaries (Windows).
# Works with private repos when either:
# - gh CLI is authenticated, or
# - GITHUB_TOKEN is set.
#
# Usage:
#   .\scripts\install.ps1                        # install latest
#   .\scripts\install.ps1 -Version v0.2.0        # install specific version
#   .\scripts\install.ps1 -Check                 # check installed vs latest
#   irm .../install.ps1 | iex                    # one-liner (latest)

Param(
  [string]$Owner = $(if ($env:BAKUFU_REPO_OWNER) { $env:BAKUFU_REPO_OWNER } else { "anthonyspiteri" }),
  [string]$Repo = $(if ($env:BAKUFU_REPO_NAME) { $env:BAKUFU_REPO_NAME } else { "veeam-cli" }),
  [string]$InstallDir = $(if ($env:BAKUFU_INSTALL_DIR) { $env:BAKUFU_INSTALL_DIR } else { "$env:USERPROFILE\bin" }),
  [string]$Version = "",
  [switch]$Check
)

$ErrorActionPreference = "Stop"
$BinaryName = "bakufu.exe"
$ChecksumName = "SHA256SUMS.txt"

# ── Ensure install directory exists ──────────────────────────────────
if (-not (Test-Path $InstallDir)) {
  New-Item -ItemType Directory -Path $InstallDir | Out-Null
  Write-Host "Created install directory: $InstallDir"
}

# ── Check existing installation ──────────────────────────────────────
$existingVersion = $null
$existingPath = $null
$target = Join-Path $InstallDir $BinaryName

if (Test-Path $target) {
  try {
    $existingVersion = & $target version 2>$null
    $existingPath = $target
    Write-Host "Existing installation found: $existingVersion ($existingPath)"
  } catch {
    Write-Host "Existing binary found at $target but failed version check."
  }
} elseif (Get-Command bakufu -ErrorAction SilentlyContinue) {
  try {
    $existingVersion = & bakufu version 2>$null
    $existingPath = (Get-Command bakufu).Source
    Write-Host "Existing installation found: $existingVersion ($existingPath)"
  } catch {}
}

# ── Resolve latest release tag ───────────────────────────────────────
$latestTag = $null
if (Get-Command gh -ErrorAction SilentlyContinue) {
  try {
    $latestTag = (gh release view --repo "$Owner/$Repo" --json tagName -q ".tagName" 2>$null)
  } catch {}
}

if ($Check) {
  if (-not $existingVersion) {
    Write-Host "bakufu is not installed."
  } else {
    Write-Host "Installed: $existingVersion"
  }
  if ($latestTag) {
    Write-Host "Latest release: $latestTag"
    $stripped = $latestTag -replace '^v', ''
    if ($existingVersion -and $existingVersion -like "*$stripped*") {
      Write-Host "Already up to date."
    } else {
      Write-Host "Run install.ps1 to upgrade."
    }
  } else {
    Write-Host "Could not determine latest release (gh CLI may not be authenticated)."
  }
  exit 0
}

# Skip download if already at latest and no specific version requested
if ($existingVersion -and $latestTag -and -not $Version) {
  $stripped = $latestTag -replace '^v', ''
  if ($existingVersion -like "*$stripped*") {
    Write-Host "Already at latest version ($existingVersion). Use -Version TAG to force a specific version."
    exit 0
  }
}

if ($existingVersion) {
  Write-Host "Upgrading bakufu from $existingVersion..."
}

# ── Detect architecture ──────────────────────────────────────────────
$arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLower()
if ($arch -ne "x64" -and $arch -ne "amd64") {
  Write-Host "Warning: non-x64 architecture detected ($arch). Using x86_64 asset."
}
$asset = "bakufu-windows-x86_64.exe"

if ($Version) {
  Write-Host "Installing $asset ($Version) from $Owner/$Repo..."
} else {
  Write-Host "Installing $asset (latest) from $Owner/$Repo..."
}

# ── Download release assets ──────────────────────────────────────────
$tmp = Join-Path $env:TEMP ("bakufu-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tmp | Out-Null

try {
  if (Get-Command gh -ErrorAction SilentlyContinue) {
    if ($Version) {
      gh release download $Version --repo "$Owner/$Repo" --pattern $asset --dir $tmp --clobber | Out-Null
      gh release download $Version --repo "$Owner/$Repo" --pattern $ChecksumName --dir $tmp --clobber | Out-Null
    } else {
      gh release download --repo "$Owner/$Repo" --pattern $asset --dir $tmp --clobber | Out-Null
      gh release download --repo "$Owner/$Repo" --pattern $ChecksumName --dir $tmp --clobber | Out-Null
    }
  } else {
    $headers = @{}
    if ($env:GITHUB_TOKEN) {
      $headers["Authorization"] = "Bearer $($env:GITHUB_TOKEN)"
    }
    if ($Version) {
      $release = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$Owner/$Repo/releases/tags/$Version"
    } else {
      $release = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$Owner/$Repo/releases/latest"
    }
    $match = $release.assets | Where-Object { $_.name -eq $asset } | Select-Object -First 1
    $sum = $release.assets | Where-Object { $_.name -eq $ChecksumName } | Select-Object -First 1
    if (-not $match) {
      throw "Asset '$asset' not found. For private repos use gh auth login or set GITHUB_TOKEN."
    }
    if (-not $sum) {
      throw "Missing '$ChecksumName' in release. Refusing unsigned install."
    }
    Invoke-WebRequest -Headers $headers -Uri $match.browser_download_url -OutFile (Join-Path $tmp $asset)
    Invoke-WebRequest -Headers $headers -Uri $sum.browser_download_url -OutFile (Join-Path $tmp $ChecksumName)
  }

  # ── Verify checksum ────────────────────────────────────────────────
  $source = Join-Path $tmp $asset
  $checksumFile = Join-Path $tmp $ChecksumName
  if (-not (Test-Path $checksumFile)) {
    throw "Missing checksum file '$ChecksumName'."
  }

  $expected = $null
  foreach ($line in Get-Content $checksumFile) {
    if ($line -match '^([A-Fa-f0-9]{64})\s+\*?(.+)$') {
      if ($Matches[2] -eq $asset) {
        $expected = $Matches[1].ToLower()
        break
      }
    }
  }
  if (-not $expected) {
    throw "No checksum entry for '$asset' in '$ChecksumName'."
  }
  $actual = (Get-FileHash -Algorithm SHA256 -Path $source).Hash.ToLower()
  if ($actual -ne $expected) {
    throw "Checksum verification failed for '$asset'."
  }
  Write-Host "Checksum verified."

  # ── Install binary ─────────────────────────────────────────────────
  Move-Item -Force $source $target
  Write-Host "Installed $target"

  # ── Verify installation ────────────────────────────────────────────
  try {
    $newVersion = & $target version 2>$null
    Write-Host "Version: $newVersion"
  } catch {
    Write-Host "Warning: installed binary failed self-check."
  }

  # ── PATH check ─────────────────────────────────────────────────────
  if ($env:Path -notlike "*$InstallDir*") {
    Write-Host ""
    Write-Host "Warning: $InstallDir is not in your PATH."
    Write-Host "Add to current session:"
    Write-Host "  `$env:Path += ';$InstallDir'"
    Write-Host "Add permanently (user scope):"
    Write-Host "  [Environment]::SetEnvironmentVariable('Path', `$env:Path + ';$InstallDir', 'User')"
  }

  # ── Next steps ─────────────────────────────────────────────────────
  Write-Host ""
  Write-Host "Next steps:"
  Write-Host "  bakufu auth setup <name> --default    # configure VBR connection"
  Write-Host "  bakufu getting-started                # guided tour"

} finally {
  if (Test-Path $tmp) {
    Remove-Item -Recurse -Force $tmp
  }
}
