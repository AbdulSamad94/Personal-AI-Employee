$ErrorActionPreference = "Stop"

# Get absolute paths
$ScriptPath = $MyInvocation.MyCommand.Path
$BaseDir = Split-Path $ScriptPath
$RunAgentScript = Join-Path $BaseDir "run_agent.ps1"

$TaskName = "AI-Employee-Runner"

Write-Host "Setting up Windows Scheduled Task: $TaskName"
Write-Host "Target Script: $RunAgentScript"

# Create action to run the PowerShell script hidden
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$RunAgentScript`""

# Create trigger: Start now, repeat every 30 minutes indefinitely
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30)

# Create settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable

try {
    # If it already exists, remove it first
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Removed existing task."
    }

    # Register the task
    Register-ScheduledTask -Action $Action -Trigger $Trigger -Settings $Settings -TaskName $TaskName -Description "Runs the Personal AI Employee agent (Qwen) every 30 minutes to process Needs_Action tasks" -User $env:USERNAME | Out-Null
    
    Write-Host "SUCCESS: Scheduled task '$TaskName' registered."
    Write-Host "The agent will now run automatically in the background every 30 minutes."
    Write-Host "You can view or disable this in the Windows 'Task Scheduler' app."
} catch {
    Write-Host "ERROR: Failed to register scheduled task. Ensure you are running this as Administrator if required."
    Write-Host $_.Exception.Message
}
