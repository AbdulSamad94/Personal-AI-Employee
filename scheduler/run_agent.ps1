$ErrorActionPreference = "Stop"

# Get the absolute path to the project root
$ScriptPath = $MyInvocation.MyCommand.Path
$BaseDir = Split-Path (Split-Path $ScriptPath)
Set-Location $BaseDir

# Directories
$VaultDir = Join-Path $BaseDir "vault"
$LogsDir = Join-Path $VaultDir "Logs"
if (-not (Test-Path $LogsDir)) { New-Item -ItemType Directory -Path $LogsDir | Out-Null }
$LogFile = Join-Path $LogsDir "scheduler.log"

function Log-Message([string]$Message) {
    $Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $LogEntry = "$Timestamp | $Message"
    Add-Content -Path $LogFile -Value $LogEntry
    Write-Host $LogEntry
}

Log-Message "=== Task Scheduler Run Started ==="

# 1. Start Orchestrator if it's not already running
# We use WMI to reliably check full command line arguments
$OrchestratorProcess = Get-WmiObject Win32_Process -Filter "name='python.exe' or name='uv.exe'" | Where-Object { $_.CommandLine -match "orchestrator.py" }

if (-not $OrchestratorProcess) {
    Log-Message "orchestrator.py is not running. Starting it in the background..."
    # Start it completely detached without a new visible window
    Start-Process -FilePath "uv" -ArgumentList "run orchestrator.py" -WindowStyle Hidden
} else {
    Log-Message "orchestrator.py is already running."
}

# 2. Run Qwen Code autonomously
Log-Message "Starting Qwen Code processing..."

try {
    # Using 'qwen' CLI. The positional argument runs a single prompt and exits.
    $Prompt = "Process all pending tasks in vault/Needs_Action/ according to the process-tasks skill, and update the dashboard (vault/Dashboard.md). If there are no tasks, just update the dashboard. IMPORTANT: Use the skills! IMPORTANT TOOL NOTE: Do NOT try to use tools named 'write_file' or 'run_shell_command'. Only use the exact tool names available in your registry (such as 'todo_write' or whatever is listed for file editing)."
    qwen $Prompt | Out-File -FilePath "$LogsDir\qwen_run_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
    Log-Message "Qwen Code execution finished."
} catch {
    Log-Message "Error running Qwen Command: $_"
}

Log-Message "=== Task Scheduler Run Completed ==="
