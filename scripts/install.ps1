Param(
  [string]$Owner = $(if ($env:BAKUFU_REPO_OWNER) { $env:BAKUFU_REPO_OWNER } else { "anthonyspiteri" }),
  [string]$Repo = $(if ($env:BAKUFU_REPO_NAME) { $env:BAKUFU_REPO_NAME } else { "veeam-cli" }),
  [string]$InstallDir = $(if ($env:BAKUFU_INSTALL_DIR) { $env:BAKUFU_INSTALL_DIR } else { "$env:USERPROFILE\bin" })
)

$ErrorActionPreference = "Stop"
$BinaryName = "bakufu.exe"

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
  } else {
    $headers = @{}
    if ($env:GITHUB_TOKEN) {
      $headers["Authorization"] = "Bearer $($env:GITHUB_TOKEN)"
    }
    $release = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$Owner/$Repo/releases/latest"
    $match = $release.assets | Where-Object { $_.name -eq $asset } | Select-Object -First 1
    if (-not $match) {
      throw "Asset '$asset' not found. For private repos use gh auth login or set GITHUB_TOKEN."
    }
    Invoke-WebRequest -Headers $headers -Uri $match.browser_download_url -OutFile (Join-Path $tmp $asset)
  }

  $source = Join-Path $tmp $asset
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
