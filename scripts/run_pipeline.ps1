# run_pipeline.ps1 - Run the full email processing pipeline
# Usage: powershell -ExecutionPolicy Bypass -File scripts/run_pipeline.ps1 [-ConfigFile config/pipeline_config.json] [-BatchSize 100]

param(
    [string]$ConfigFile = "config/pipeline_config.json",
    [int]$BatchSize = 0,
    [int]$Workers = 0,
    [switch]$SkipOllamaRestart
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptDir

Set-Location $projectDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Email Processing Pipeline" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Load config
if (-not (Test-Path $ConfigFile)) {
    Write-Host "ERROR: Config file not found: $ConfigFile" -ForegroundColor Red
    exit 1
}

$config = Get-Content $ConfigFile | ConvertFrom-Json
Write-Host "Config: $ConfigFile" -ForegroundColor Gray

# Override with command line params
if ($BatchSize -gt 0) { $config.pipeline.batch_size = $BatchSize }
if ($Workers -gt 0) { $config.pipeline.workers = $Workers }

Write-Host "  Model: $($config.ollama.model)"
Write-Host "  Batch size: $($config.pipeline.batch_size)"
Write-Host "  Workers: $($config.pipeline.workers)"
Write-Host "  OLLAMA_NUM_PARALLEL: $($config.ollama.num_parallel)"
Write-Host ""

# Step 1: Stop Ollama
if (-not $SkipOllamaRestart) {
    Write-Host "[1/3] Stopping Ollama server..." -ForegroundColor Yellow
    & powershell -ExecutionPolicy Bypass -File "$scriptDir/ollama_stop.ps1"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Failed to stop Ollama cleanly" -ForegroundColor Yellow
    }
    Start-Sleep -Seconds 2
}

# Step 2: Start Ollama with config
if (-not $SkipOllamaRestart) {
    Write-Host ""
    Write-Host "[2/3] Starting Ollama server..." -ForegroundColor Yellow
    & powershell -ExecutionPolicy Bypass -File "$scriptDir/ollama_start.ps1" -ConfigFile $ConfigFile
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to start Ollama" -ForegroundColor Red
        exit 1
    }
    Start-Sleep -Seconds 2
}

# Step 3: Run pipeline
Write-Host ""
Write-Host "[3/3] Running pipeline..." -ForegroundColor Yellow
Write-Host ""

$startTime = Get-Date

& uv run python -m utils.pipe_parallel `
    --batch-size $config.pipeline.batch_size `
    --workers $config.pipeline.workers `
    --model $config.ollama.model

$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Pipeline Complete" -ForegroundColor Cyan
Write-Host "  Duration: $($duration.TotalSeconds.ToString('F1')) seconds" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
