param(
    [string]$BaseUrl = "http://localhost:8000",
    [string]$ImagePath = (Join-Path $PSScriptRoot "..\test_assets\image0.jpeg")
)

$ErrorActionPreference = "Stop"

$imageFile = Get-Item -LiteralPath $ImagePath -ErrorAction Stop
if ($imageFile.PSIsContainer) {
    throw "Test image path is a directory: $ImagePath"
}

$imageBytes = [System.IO.File]::ReadAllBytes($imageFile.FullName)
$payload = @{
    uuid  = [guid]::NewGuid().ToString()
    image = [Convert]::ToBase64String($imageBytes)
} | ConvertTo-Json -Compress

$response = Invoke-RestMethod `
    -Method Post `
    -Uri "$BaseUrl/api/predict" `
    -ContentType "application/json" `
    -Body $payload

if ($response.uuid -ne ($payload | ConvertFrom-Json).uuid) {
    throw "API response uuid does not match the request"
}

Write-Output "Prediction request succeeded"
$response | Select-Object uuid, count, detections, speed_preprocess_ms, speed_inference_ms, speed_postprocess_ms
