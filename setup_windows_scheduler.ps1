<#>
.SYNOPSIS
    Sets up Windows Task Scheduler to run the cartoon pipeline automatically every week.
    Run ONCE as Administrator after first setup.

.DESCRIPTION
    Creates a scheduled task that runs:
    - python run_pipeline.py --auto
    Every Monday at 10:00 AM (configurable)
    Runs whether user is logged in or not.
#>

param(
    [string]$ProjectPath = "C:\cartoon_channel",  # CHANGE THIS to your actual path
    [string]$PythonExe = "python",                 # Or full path: "C:\Python311\python.exe"
    [string]$TaskName = "CartoonChannelPipeline",
    [string]$RunTime = "10:00",                    # 24-hour format
    [string]$Day = "Monday"                        # Monday, Tuesday, etc.
)

# Check admin
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "❌ Please run PowerShell as Administrator!"
    exit 1
}

# Verify project path
if (-not (Test-Path $ProjectPath)) {
    Write-Error "❌ Project path not found: $ProjectPath"
    exit 1
}

if (-not (Test-Path "$ProjectPath\run_pipeline.py")) {
    Write-Error "❌ run_pipeline.py not found in $ProjectPath"
    exit 1
}

# Get Python full path
$PythonFullPath = (Get-Command $PythonExe -ErrorAction SilentlyContinue).Source
if (-not $PythonFullPath) {
    Write-Error "❌ Python not found: $PythonExe"
    exit 1
}

Write-Host "🔧 Setting up Windows Task Scheduler..."
Write-Host "   Project: $ProjectPath"
Write-Host "   Python:  $PythonFullPath"
Write-Host "   Schedule: $Day at $RunTime"

# Create action
$Action = New-ScheduledTaskAction `
    -Execute $PythonFullPath `
    -Argument "run_pipeline.py --auto" `
    -WorkingDirectory $ProjectPath

# Create trigger (weekly)
$Trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek $Day `
    -At $RunTime

# Settings: run whether logged in or not, with highest privileges
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 4)

# Register task
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Automated cartoon channel pipeline - generates, renders, uploads weekly" `
        -Force

    Write-Host "✅ Task '$TaskName' created successfully!"
    Write-Host "   Runs: Every $Day at $RunTime"
    Write-Host "   User: SYSTEM (runs even when logged out)"
}
catch {
    Write-Error "❌ Failed to create task: $_"
    exit 1
}

# Also create a daily check task (optional - runs quick check)
$DailyAction = New-ScheduledTaskAction `
    -Execute $PythonFullPath `
    -Argument "run_pipeline.py --auto" `
    -WorkingDirectory $ProjectPath

$DailyTrigger = New-ScheduledTaskTrigger -Daily -At "06:00"

try {
    Register-ScheduledTask `
        -TaskName "$TaskName-DailyCheck" `
        -Action $DailyAction `
        -Trigger $DailyTrigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Daily quick check for cartoon pipeline" `
        -Force
    Write-Host "✅ Daily check task created (runs 6:00 AM daily)"
}
catch {
    Write-Host "⚠️ Daily check task failed (optional): $_"
}

Write-Host ""
Write-Host "🎉 SETUP COMPLETE!"
Write-Host ""
Write-Host "To verify:"
Write-Host "  1. Open 'Task Scheduler' (taskschd.msc)"
Write-Host "  2. Find '$TaskName' in Task Scheduler Library"
Write-Host "  3. Right-click → Run to test now"
Write-Host ""
Write-Host "To view logs:"
Write-Host "  Check: $ProjectPath\logs\ (created by pipeline)"
Write-Host ""
Write-Host "To disable:"
Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"