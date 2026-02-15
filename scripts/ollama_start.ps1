# ollama_start.ps1 - Start Ollama server with configuration
# Usage: powershell -ExecutionPolicy Bypass -File scripts/ollama_start.ps1 [-ConfigFile config/pipeline_config.json]

param(
    [string]$ConfigFile = "config/pipeline_config.json",
    [int]$NumParallel = 0,
    [int]$Port = 0,
    [switch]$Wait
)

$ErrorActionPreference = "Stop"

# Load config if exists
$config = @{
    num_parallel = 4
    port = 11434
    model = "qwen2.5:0.5b"
    flash_attention = $false
    kv_cache_type = ""
}

if (Test-Path $ConfigFile) {
    Write-Host "Loading config from: $ConfigFile" -ForegroundColor Cyan
    $jsonConfig = Get-Content $ConfigFile | ConvertFrom-Json
    if ($jsonConfig.ollama) {
        if ($jsonConfig.ollama.num_parallel) { $config.num_parallel = $jsonConfig.ollama.num_parallel }
        if ($jsonConfig.ollama.port) { $config.port = $jsonConfig.ollama.port }
        if ($jsonConfig.ollama.model) { $config.model = $jsonConfig.ollama.model }
        if ($jsonConfig.ollama.flash_attention -eq $true) { $config.flash_attention = $true }
        if ($jsonConfig.ollama.kv_cache_type) { $config.kv_cache_type = $jsonConfig.ollama.kv_cache_type }
    }
}

# Override with command line params if provided
if ($NumParallel -gt 0) { $config.num_parallel = $NumParallel }
if ($Port -gt 0) { $config.port = $Port }

Write-Host "Starting Ollama server..." -ForegroundColor Yellow
Write-Host "  OLLAMA_NUM_PARALLEL: $($config.num_parallel)"
Write-Host "  OLLAMA_HOST: 127.0.0.1:$($config.port)"
if ($config.flash_attention) { Write-Host "  OLLAMA_FLASH_ATTENTION: 1" }
if ($config.kv_cache_type) { Write-Host "  OLLAMA_KV_CACHE_TYPE: $($config.kv_cache_type)" }

# Set environment variables
$env:OLLAMA_NUM_PARALLEL = $config.num_parallel
$env:OLLAMA_HOST = "127.0.0.1:$($config.port)"
if ($config.flash_attention) { $env:OLLAMA_FLASH_ATTENTION = "1" }
if ($config.kv_cache_type) { $env:OLLAMA_KV_CACHE_TYPE = $config.kv_cache_type }

# Always stop existing Ollama instances first
Write-Host "Checking for existing Ollama instances..." -ForegroundColor Gray
$ollamaProcesses = Get-Process -Name "ollama*" -ErrorAction SilentlyContinue
if ($ollamaProcesses) {
    Write-Host "  Stopping existing Ollama instances..." -ForegroundColor Yellow
    foreach ($proc in $ollamaProcesses) {
        Write-Host "    Stopping PID: $($proc.Id)"
        Stop-Process -Id $proc.Id -Force
    }
    Start-Sleep -Seconds 2
}

# Find Ollama executable
$ollamaPaths = @(
    "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe",
    "C:\Program Files\Ollama\ollama.exe",
    "ollama"  # Fallback to PATH
)

$ollamaExe = $null
foreach ($p in $ollamaPaths) {
    if (Test-Path $p) {
        $ollamaExe = $p
        break
    }
}

if (-not $ollamaExe) {
    # Try to find via where command
    $ollamaExe = (Get-Command ollama -ErrorAction SilentlyContinue).Source
}

if (-not $ollamaExe) {
    Write-Host "ERROR: Cannot find ollama.exe" -ForegroundColor Red
    exit 1
}

Write-Host "  Ollama path: $ollamaExe" -ForegroundColor Gray

# Start Ollama server
if ($Wait) {
    # Run in foreground (blocking)
    Write-Host "Starting Ollama in foreground mode (Ctrl+C to stop)..." -ForegroundColor Green
    & $ollamaExe serve
} else {
    # Run in background with environment variables
    Write-Host "Starting Ollama in background..." -ForegroundColor Green

    # Create a batch file to set env vars and start Ollama
    $batchLines = @(
        "@echo off",
        "set OLLAMA_NUM_PARALLEL=$($config.num_parallel)",
        "set OLLAMA_HOST=127.0.0.1:$($config.port)"
    )
    if ($config.flash_attention) { $batchLines += "set OLLAMA_FLASH_ATTENTION=1" }
    if ($config.kv_cache_type) { $batchLines += "set OLLAMA_KV_CACHE_TYPE=$($config.kv_cache_type)" }
    $batchLines += "`"$ollamaExe`" serve"
    $batchContent = $batchLines -join "`r`n"
    $batchFile = "$env:TEMP\start_ollama.bat"
    $batchContent | Out-File -FilePath $batchFile -Encoding ASCII

    $process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $batchFile -PassThru -WindowStyle Hidden

    # Wait for server to be ready
    $maxWait = 30
    $waited = 0
    $serverReady = $false

    while ($waited -lt $maxWait -and -not $serverReady) {
        Start-Sleep -Seconds 1
        $waited++

        # Use curl for more reliable HTTP check
        $result = & curl.exe -s -o NUL -w "%{http_code}" "http://127.0.0.1:$($config.port)/api/tags" 2>$null
        if ($result -eq "200") {
            $serverReady = $true
            Write-Host "Ollama server ready (PID: $($process.Id))" -ForegroundColor Green
        } else {
            Write-Host "  Waiting for server... ($waited/$maxWait)" -ForegroundColor Gray
        }
    }

    if (-not $serverReady) {
        Write-Host "ERROR: Ollama server failed to start within $maxWait seconds" -ForegroundColor Red
        exit 1
    }

    # Pre-load model using curl
    Write-Host "Pre-loading model: $($config.model)..." -ForegroundColor Cyan
    $body = "{`"model`":`"$($config.model)`",`"prompt`":`"hi`",`"options`":{`"num_predict`":1}}"
    & curl.exe -s -X POST "http://127.0.0.1:$($config.port)/api/generate" -d $body | Out-Null
    Write-Host "Model loaded successfully" -ForegroundColor Green

    exit 0
}
