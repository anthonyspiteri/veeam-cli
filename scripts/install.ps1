Param(
  [string]$Owner = $(if ($env:BAKUFU_REPO_OWNER) { $env:BAKUFU_REPO_OWNER } else { "anthonyspiteri" }),
  [string]$Repo = $(if ($env:BAKUFU_REPO_NAME) { $env:BAKUFU_REPO_NAME } else { "veeam-cli" }),
  [string]$InstallDir = $(if ($env:BAKUFU_INSTALL_DIR) { $env:BAKUFU_INSTALL_DIR } else { "$env:USERPROFILE\bin" })
)

$ErrorActionPreference = "Stop"
$BinaryName = "bakufu.exe"
$ChecksumName = "SHA256SUMS.txt"

if (-not (Test-Path $InstallDir)) {
  New-Item -ItemType Directory -Path $InstallDir | Out-Null
}

$arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLower()
if ($arch -ne "x64" -and $arch -ne "amd64") {
  Write-Host "Warning: non-x64 architecture detected ($arch). Using x86_64 asset."
}
$asset = "bakufu-windows-x86_64.exe"
$tmp = Join-Path $env:TEMP ("bakufu-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tmp | Out-Null

try {
  if (Get-Command gh -ErrorAction SilentlyContinue) {
    gh release download --repo "$Owner/$Repo" --pattern $asset --dir $tmp --clobber | Out-Null
    gh release download --repo "$Owner/$Repo" --pattern $ChecksumName --dir $tmp --clobber | Out-Null
  } else {
    $headers = @{}
    if ($env:GITHUB_TOKEN) {
      $headers["Authorization"] = "Bearer $($env:GITHUB_TOKEN)"
    }
    $release = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$Owner/$Repo/releases/latest"
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

  $target = Join-Path $InstallDir $BinaryName
  Move-Item -Force $source $target
  Write-Host "Installed $target"

  if ($env:Path -notlike "*$InstallDir*") {
    Write-Host "Add to PATH for current session:"
    Write-Host "`$env:Path += ';$InstallDir'"
  }

  & $target version
} finally {
  if (Test-Path $tmp) {
    Remove-Item -Recurse -Force $tmp
  }
}
