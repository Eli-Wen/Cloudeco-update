param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

Set-Location $projectRoot
$env:PYTHONDONTWRITEBYTECODE = "1"

python -m uvicorn app.main:app --host 127.0.0.1 --port $Port --reload
