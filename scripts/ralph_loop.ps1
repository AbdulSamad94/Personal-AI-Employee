# scripts/ralph_loop.ps1
# Ralph Wiggum Loop for OpenCode CLI
# Keeps OpenCode working on a task until it's finished.

param (
    [Parameter(Mandatory=$true)]
    [string]$TaskDescription,
    
    [int]$MaxIterations = 5
)

$TaskName = "TASK_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".md"
$NeedsActionDir = Join-Path -Path $PSScriptRoot -ChildPath "..\vault\Needs_Action"
$DoneDir = Join-Path -Path $PSScriptRoot -ChildPath "..\vault\Done"

if (-not (Test-Path $NeedsActionDir)) { New-Item -ItemType Directory -Force -Path $NeedsActionDir | Out-Null }
if (-not (Test-Path $DoneDir)) { New-Item -ItemType Directory -Force -Path $DoneDir | Out-Null }

$TaskFile = Join-Path -Path $NeedsActionDir -ChildPath $TaskName
Set-Content -Path $TaskFile -Value "---`ntype: autonomous_task`nstatus: pending`n---`n`n## Task Description`n$TaskDescription`n`nWhen complete, move this file to /Vault/Done/"

Write-Host "Created task file: $TaskName"
Write-Host "Starting Ralph Wiggum Loop..."

$iteration = 1
$completed = $false

while (($iteration -le $MaxIterations) -and (-not $completed)) {
    Write-Host "`n--- Iteration $iteration ---"
    
    # Check if file moved to Done
    $DoneTaskFile = Join-Path -Path $DoneDir -ChildPath $TaskName
    if (Test-Path $DoneTaskFile) {
        Write-Host "Task complete! Found file in /Done."
        $completed = $true
        break
    }
    
    # Inject the prompt to OpenCode
    $Prompt = "Please read the task $TaskName in vault/Needs_Action. Execute the instructions. When fully complete, move the file to vault/Done and say TASK_COMPLETE."

    Write-Host "Invoking OpenCode CLI..."

    # Run OpenCode non-interactively; --auto approves permissions not explicitly denied in opencode.json
    opencode run $Prompt --auto

    # Re-evaluate
    if (Test-Path $DoneTaskFile) {
        Write-Host "Task complete! Found file in /Done."
        $completed = $true
        break
    } else {
        Write-Host "OpenCode exited but task file is not in /Done. Looping again..."
    }
    
    $iteration++
}

if (-not $completed) {
    Write-Host ("`nMax iterations ({0}) reached. Task incomplete." -f $MaxIterations) -ForegroundColor Red
} else {
    Write-Host "`nTask completed successfully." -ForegroundColor Green
}
