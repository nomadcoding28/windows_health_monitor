# Paths to Python executable and monitoring script
$pythonPath = "C:\Python312\python.exe"
$scriptPath = "C:\Users\sasum\OneDrive\Documents\windows-health-monitor\monitor.py"

# Log file for PowerShell metrics
$logFile = "C:\Users\sasum\OneDrive\Documents\windows-health-monitor\monitor.log"

# Thresholds for alerts (adjust these based on your needs)
$cpuThreshold = 80
$memoryThreshold = 80
$diskThreshold = 90
$gpuThreshold = 80

# Start Python monitoring script
Write-Output "Starting Python monitoring script..."
try {
    Start-Process -NoNewWindow -FilePath $pythonPath -ArgumentList $scriptPath
}
catch {
    Write-Output "Error running Python script: $($_.Exception.Message)" | Out-File -FilePath $logFile -Append
}

# Function to fetch GPU metrics using WMI
function Get-GPUStats {
    $gpuInfo = Get-WmiObject Win32_VideoController
    foreach ($gpu in $gpuInfo) {
        [PSCustomObject]@{
            Name          = $gpu.Name
            DriverVersion = $gpu.DriverVersion
            Memory        = ($gpu.AdapterRAM / 1MB) -as [int]
        }
    }
}

# Function to fetch CPU temperature (requires OpenHardwareMonitor)
function Get-CPUTemperature {
    $ohmPath = "C:\Path\To\OpenHardwareMonitor.exe"
    if (-Not (Get-Process | Where-Object { $_.Path -eq $ohmPath })) {
        Start-Process $ohmPath
    }
    $temp = Get-CimInstance Win32_PerfFormattedData_Counters_ThermalZoneInformation | 
    Select-Object -ExpandProperty Temperature | Measure-Object -Average
    return ($temp.Average / 10) - 273.15  # Convert to Celsius
}

# Function to log system metrics
function Log-SystemMetrics {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $cpuUsage = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue
    $memoryUsage = (Get-Counter '\Memory\% Committed Bytes In Use').CounterSamples.CookedValue
    $diskUsage = (Get-Volume | Where-Object { $_.DriveType -eq "Fixed" } | Select-Object -ExpandProperty SizeRemaining) -as [int]
    $gpuMetrics = Get-GPUStats

    $metrics = @"
$timestamp | CPU: $cpuUsage% | Memory: $memoryUsage% | Disk: $diskUsage% | GPU: $($gpuMetrics.Name), Driver: $($gpuMetrics.DriverVersion), Memory: $($gpuMetrics.Memory) MB
"@

    # Log metrics to file
    $metrics | Out-File -FilePath $logFile -Append

    # Check thresholds and trigger alerts
    if ($cpuUsage -gt $cpuThreshold) {
        Show-Notification -Title "High CPU Usage" -Message "CPU usage is $cpuUsage%!"
    }
    if ($memoryUsage -gt $memoryThreshold) {
        Show-Notification -Title "High Memory Usage" -Message "Memory usage is $memoryUsage%!"
    }
}

# Function to show system tray notification
function Show-Notification {
    param (
        [string]$Title,
        [string]$Message
    )
    [reflection.assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null
    $notifyIcon = New-Object System.Windows.Forms.NotifyIcon
    $notifyIcon.BalloonTipTitle = $Title
    $notifyIcon.BalloonTipText = $Message
    $notifyIcon.Icon = [System.Drawing.SystemIcons]::Information
    $notifyIcon.Visible = $true
    $notifyIcon.ShowBalloonTip(5000)
}

# Monitor system metrics periodically
Write-Output "Monitoring system metrics..."
while ($true) {
    Log-SystemMetrics
    Start-Sleep -Seconds 5
}
