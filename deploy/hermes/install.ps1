<#
.SYNOPSIS
  Installs the Job Radar cron wrapper into Hermes' scripts directory.

.DESCRIPTION
  Copies job_radar_daily.py to the Hermes scripts folder and substitutes the
  repository path. Re-run it after moving the repository.

.EXAMPLE
  ./deploy/hermes/install.ps1
  hermes cron create "0 7 * * *" --no-agent --script job_radar_daily.py `
      --deliver telegram --name job-radar-daily --timezone Asia/Jakarta --catch-up on
#>
[CmdletBinding()]
param(
    [string]$ProjectDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string]$ScriptsDir = (Join-Path $env:LOCALAPPDATA "hermes\scripts"),
    [string]$TargetName = "job_radar_daily.py"
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force $ScriptsDir | Out-Null
$template = Get-Content (Join-Path $PSScriptRoot "job_radar_daily.py") -Raw
$target = Join-Path $ScriptsDir $TargetName
$template.Replace("__PROJECT_DIR__", $ProjectDir) | Set-Content $target -Encoding utf8
Write-Host "Installed $target (project: $ProjectDir)"
