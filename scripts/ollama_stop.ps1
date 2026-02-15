# ollama_stop.ps1 - Stop Ollama server gracefully
# Usage: powershell -ExecutionPolicy Bypass -File scripts/ollama_stop.ps1

$ErrorActionPreference = "Stop"

Write-Host "Stopping Ollama server..." -ForegroundColor Yellow

# Find and stop Ollama processes
$ollamaProcesses = Get-Process -Name "ollama*" -ErrorAction SilentlyContinue

if ($ollamaProcesses) {
    foreach ($proc in $ollamaProcesses) {
        Write-Host "  Stopping process: $($proc.Name) (PID: $($proc.Id))"
        Stop-Process -Id $proc.Id -Force
    }

    # Wait for processes to terminate
    Start-Sleep -Seconds 2

    # Verify stopped
    $remaining = Get-Process -Name "ollama*" -ErrorAction SilentlyContinue
    if ($remaining) {
        Write-Host "WARNING: Some Ollama processes still running" -ForegroundColor Red
        exit 1
    }

    Write-Host "Ollama server stopped successfully" -ForegroundColor Green
} else {
    Write-Host "No Ollama processes found" -ForegroundColor Cyan
}

exit 0
