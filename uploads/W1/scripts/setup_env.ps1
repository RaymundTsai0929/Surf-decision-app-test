$ErrorActionPreference = "Stop"

$project = "D:\VibeCoding\研究論文Prototype\W1"
$venvActivate = Join-Path $project ".venv\Scripts\Activate.ps1"

if (-not (Test-Path $project)) {
    Write-Error "找不到專案資料夾：$project"
}
Set-Location $project

$env:PIP_CACHE_DIR = "D:\VibeCoding\pip_cache"
$env:TEMP = "D:\VibeCoding\tmp"
$env:TMP = "D:\VibeCoding\tmp"

New-Item -ItemType Directory -Path $env:PIP_CACHE_DIR -Force | Out-Null
New-Item -ItemType Directory -Path $env:TEMP -Force | Out-Null

if (-not (Test-Path $venvActivate)) {
    Write-Error "找不到虛擬環境啟用檔：$venvActivate"
}

. $venvActivate

Write-Host "已進入專案環境：$project" -ForegroundColor Green
Write-Host "Python：$(python -c 'import sys; print(sys.executable)')"
