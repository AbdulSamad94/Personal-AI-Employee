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

# Prevent two overlapping scheduled runs from both passing the "orchestrator not running" check
# and each spawning their own orchestrator.py + 4 watchers (this happened in practice on 2026-07-09:
# two full watcher trees ran simultaneously and produced duplicate task files in Needs_Action/).
# A named Mutex is atomic across processes, unlike a point-in-time WMI process query.
$Mutex = New-Object System.Threading.Mutex($false, "Global\AIEmployeeRunAgentLock")
$AcquiredLock = $Mutex.WaitOne(0)

if (-not $AcquiredLock) {
    Log-Message "Another run_agent.ps1 instance is already active. Exiting without starting duplicate work."
    exit 0
}

try {
    Log-Message "=== Task Scheduler Run Started ==="

    # 1. Start Orchestrator if it's not already running, tracked via a PID lock file
    # (faster and more reliable than a WMI CommandLine scan, which can miss the brief window
    # while `uv run orchestrator.py` is still starting up).
    $OrchestratorLockFile = Join-Path $BaseDir ".orchestrator.pid"
    $OrchestratorRunning = $false

    if (Test-Path $OrchestratorLockFile) {
        $LockedPid = Get-Content $OrchestratorLockFile -ErrorAction SilentlyContinue
        if ($LockedPid) {
            $ExistingProc = Get-Process -Id $LockedPid -ErrorAction SilentlyContinue
            if ($ExistingProc) { $OrchestratorRunning = $true }
        }
    }

    if (-not $OrchestratorRunning) {
        Log-Message "orchestrator.py is not running. Starting it in the background..."
        $OrchestratorProc = Start-Process -FilePath "uv" -ArgumentList "run orchestrator.py" -WindowStyle Hidden -PassThru
        Set-Content -Path $OrchestratorLockFile -Value $OrchestratorProc.Id
    } else {
        Log-Message "orchestrator.py is already running (PID $LockedPid)."
    }

    # 2. Run OpenCode autonomously
    Log-Message "Starting OpenCode processing..."

    try {
        $Prompt = "Process all pending tasks in vault/Needs_Action/ according to the process-tasks skill, and update the dashboard (vault/Dashboard.md). If there are no tasks, just update the dashboard. IMPORTANT: Use the skills!"
        $RunLog = "$LogsDir\opencode_run_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
        $ErrLog = "$LogsDir\opencode_err_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

        # --auto approves permissions not explicitly denied in opencode.json, allowing unattended runs.
        # HITL safety still comes from the vault Pending_Approval -> Approved gate, not from tool permissions.
        # Must target opencode.cmd explicitly: npm's global install on Windows also creates an opencode.ps1
        # shim, and Start-Process uses raw CreateProcess (unlike interactive PowerShell command resolution),
        # which cannot execute a .ps1 directly -- it fails with "%1 is not a valid Win32 application."
        $OpenCodeCmd = (Get-Command "opencode.cmd" -ErrorAction SilentlyContinue).Source
        if (-not $OpenCodeCmd) { $OpenCodeCmd = "opencode.cmd" }

        $proc = Start-Process -FilePath $OpenCodeCmd `
            -ArgumentList "run", "`"$Prompt`"", "--auto" `
            -RedirectStandardOutput $RunLog `
            -RedirectStandardError $ErrLog `
            -NoNewWindow `
            -Wait `
            -PassThru

        if ($proc.ExitCode -ne 0) {
            Log-Message "WARNING: OpenCode exited with code $($proc.ExitCode). Check logs for details."
        } else {
            Log-Message "OpenCode execution finished successfully."
        }
    } catch {
        Log-Message "Error running OpenCode Command: $_"
    }

    Log-Message "=== Task Scheduler Run Completed ==="
} finally {
    $Mutex.ReleaseMutex() | Out-Null
    $Mutex.Dispose()
}
