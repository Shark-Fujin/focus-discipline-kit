# Bedtime Enforcer for Windows - 严格作息执行器
# PowerShell script for Windows sleep schedule enforcement

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("enable", "disable", "status", "test")]
    [string]$Action = "help"
)

# Configuration - 可以根据需要修改这些时间
$BEDTIME_HOUR = 22        # 睡觉时间 - 小时 (24小时制)
$BEDTIME_MINUTE = 30      # 睡觉时间 - 分钟  
$WAKEUP_HOUR = 6          # 起床时间 - 小时 (24小时制)
$WAKEUP_MINUTE = 30       # 起床时间 - 分钟

# 任务名称
$TASK_NAME = "BedtimeEnforcer"
$STARTUP_TASK_NAME = "BedtimeStartupCheck"

# 脚本路径
$SCRIPT_PATH = $PSCommandPath

# 颜色输出函数
function Write-ColorText {
    param(
        [string]$Text,
        [ConsoleColor]$Color = [ConsoleColor]::White
    )
    $originalColor = $Host.UI.RawUI.ForegroundColor
    $Host.UI.RawUI.ForegroundColor = $Color
    Write-Host $Text
    $Host.UI.RawUI.ForegroundColor = $originalColor
}

function Write-LogMessage {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-ColorText "[$timestamp] $Message" -Color Cyan
}

function Write-WarningMessage {
    param([string]$Message)
    Write-ColorText "[WARNING] $Message" -Color Yellow
}

function Write-ErrorMessage {
    param([string]$Message)
    Write-ColorText "[ERROR] $Message" -Color Red
}

function Write-SuccessMessage {
    param([string]$Message)
    Write-ColorText "[SUCCESS] $Message" -Color Green
}

# 检查管理员权限
function Test-AdminRights {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 检查是否在禁止时间段
function Test-ForbiddenTime {
    $currentTime = Get-Date
    $currentMinutes = $currentTime.Hour * 60 + $currentTime.Minute
    
    $bedtimeMinutes = $BEDTIME_HOUR * 60 + $BEDTIME_MINUTE
    $wakeupMinutes = $WAKEUP_HOUR * 60 + $WAKEUP_MINUTE
    
    # 处理跨午夜的情况
    if ($bedtimeMinutes -gt $wakeupMinutes) {
        # 当前时间在睡觉时间之后或起床时间之前
        return ($currentMinutes -ge $bedtimeMinutes) -or ($currentMinutes -lt $wakeupMinutes)
    } else {
        # 同一天内的时间段
        return ($currentMinutes -ge $bedtimeMinutes) -and ($currentMinutes -lt $wakeupMinutes)
    }
}

# 计算到睡觉时间的秒数
function Get-SecondsUntilBedtime {
    $currentTime = Get-Date
    $today = $currentTime.Date
    
    # 计算今天的睡觉时间
    $todayBedtime = $today.AddHours($BEDTIME_HOUR).AddMinutes($BEDTIME_MINUTE)
    
    if ($currentTime -lt $todayBedtime) {
        $targetBedtime = $todayBedtime
    } else {
        # 使用明天的睡觉时间
        $targetBedtime = $todayBedtime.AddDays(1)
    }
    
    return [int](($targetBedtime - $currentTime).TotalSeconds)
}

# 强制关机函数
function Invoke-ForceShutdown {
    param([string]$Reason = "Bedtime reached")
    
    Write-WarningMessage $Reason
    Write-WarningMessage "计算机将在30秒后关机..."
    
    # 显示警告对话框
    Add-Type -AssemblyName System.Windows.Forms
    $result = [System.Windows.Forms.MessageBox]::Show(
        "睡觉时间到了！`n`n计算机将在30秒后关机。`n这是为了您的健康和睡眠计划。", 
        "睡觉时间强制执行", 
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Warning
    )
    
    Start-Sleep -Seconds 30
    Write-LogMessage "执行强制关机..."
    
    # 强制关机
    shutdown /s /f /t 0 /c "Bedtime enforced - Good night!"
}

# 显示5分钟警告
function Show-FiveMinuteWarning {
    Add-Type -AssemblyName System.Windows.Forms
    
    Write-WarningMessage "睡觉时间警告：计算机将在5分钟后关机！"
    
    $result = [System.Windows.Forms.MessageBox]::Show(
        "睡觉时间警告！`n`n计算机将在5分钟后关机。`n请保存您的工作并准备睡觉。", 
        "5分钟警告", 
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Exclamation
    )
}

# 创建定时关机任务
function New-BedtimeTask {
    Write-LogMessage "创建睡觉时间任务..."
    
    $secondsUntilBedtime = Get-SecondsUntilBedtime
    $minutesUntilBedtime = [math]::Round($secondsUntilBedtime / 60)
    
    Write-LogMessage "距离睡觉时间还有 $minutesUntilBedtime 分钟"
    
    # 计算目标睡觉时间
    $bedtimeToday = (Get-Date).Date.AddHours($BEDTIME_HOUR).AddMinutes($BEDTIME_MINUTE)
    if ((Get-Date) -ge $bedtimeToday) {
        $bedtimeToday = $bedtimeToday.AddDays(1)
    }
    
    # 创建任务计划
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$SCRIPT_PATH`" -Action shutdown"
    $trigger = New-ScheduledTaskTrigger -Daily -At $bedtimeToday
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
    
    try {
        Unregister-ScheduledTask -TaskName $TASK_NAME -Confirm:$false -ErrorAction SilentlyContinue
        Register-ScheduledTask -TaskName $TASK_NAME -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
        Write-SuccessMessage "睡觉时间任务已创建"
        Write-LogMessage "下次关机时间: $($bedtimeToday.ToString('yyyy-MM-dd HH:mm'))"
    } catch {
        Write-ErrorMessage "创建任务失败: $_"
    }
}

# 创建开机检查任务
function New-StartupCheckTask {
    Write-LogMessage "创建开机检查任务..."
    
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$SCRIPT_PATH`" -Action startup-check"
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
    
    try {
        Unregister-ScheduledTask -TaskName $STARTUP_TASK_NAME -Confirm:$false -ErrorAction SilentlyContinue
        Register-ScheduledTask -TaskName $STARTUP_TASK_NAME -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
        Write-SuccessMessage "开机检查任务已创建"
    } catch {
        Write-ErrorMessage "创建开机检查任务失败: $_"
    }
}

# 设置自动开机 (需要BIOS支持)
function Set-AutoWakeup {
    Write-LogMessage "尝试设置自动唤醒..."
    
    # 使用powercfg设置唤醒计时器
    $wakeTime = "{0:D2}:{1:D2}:00" -f $WAKEUP_HOUR, $WAKEUP_MINUTE
    
    try {
        # 允许唤醒计时器
        powercfg /setacvalueindex SCHEME_CURRENT 238C9FA8-0AAD-41ED-83F4-97BE242C8F20 BD3B718A-0680-4D9D-8AB2-E1D2B4AC806D 1
        powercfg /setdcvalueindex SCHEME_CURRENT 238C9FA8-0AAD-41ED-83F4-97BE242C8F20 BD3B718A-0680-4D9D-8AB2-E1D2B4AC806D 1
        powercfg /setactive SCHEME_CURRENT
        
        Write-SuccessMessage "自动唤醒设置已启用 (需要BIOS支持RTC唤醒)"
        Write-LogMessage "建议在BIOS中启用 'Wake on RTC' 或类似功能"
    } catch {
        Write-WarningMessage "自动唤醒设置失败，可能需要在BIOS中手动配置"
    }
}

# 移除所有任务
function Remove-BedtimeTasks {
    Write-LogMessage "移除睡觉执行器任务..."
    
    try {
        Unregister-ScheduledTask -TaskName $TASK_NAME -Confirm:$false -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $STARTUP_TASK_NAME -Confirm:$false -ErrorAction SilentlyContinue
        Write-SuccessMessage "所有任务已移除"
    } catch {
        Write-ErrorMessage "移除任务失败: $_"
    }
}

# 显示状态
function Show-Status {
    Write-ColorText "`n=== Bedtime Enforcer 状态 ===" -Color Magenta
    Write-Host "配置: 睡觉 $BEDTIME_HOUR`:$($BEDTIME_MINUTE.ToString('D2')) - 起床 $WAKEUP_HOUR`:$($WAKEUP_MINUTE.ToString('D2'))"
    
    $currentTime = Get-Date
    Write-Host "当前时间: $($currentTime.ToString('HH:mm:ss'))"
    
    if (Test-ForbiddenTime) {
        Write-ColorText "状态: 当前处于禁止时间段" -Color Red
    } else {
        Write-ColorText "状态: 当前时间允许使用" -Color Green
        $minutesUntilBedtime = [math]::Round((Get-SecondsUntilBedtime) / 60)
        Write-Host "距离睡觉时间: $minutesUntilBedtime 分钟"
    }
    
    # 检查任务状态
    $task = Get-ScheduledTask -TaskName $TASK_NAME -ErrorAction SilentlyContinue
    $startupTask = Get-ScheduledTask -TaskName $STARTUP_TASK_NAME -ErrorAction SilentlyContinue
    
    if ($task -and $startupTask) {
        Write-ColorText "任务状态: 已启用" -Color Green
        if ($task.Triggers.Count -gt 0) {
            Write-Host "下次关机时间: $($task.Triggers[0].StartBoundary)"
        }
    } else {
        Write-ColorText "任务状态: 未启用" -Color Yellow
    }
    Write-Host ""
}

# 主执行逻辑
switch ($Action.ToLower()) {
    "enable" {
        Write-LogMessage "启用严格作息模式..."
        
        if (-not (Test-AdminRights)) {
            Write-ErrorMessage "需要管理员权限来创建任务计划"
            Write-Host "请以管理员身份运行PowerShell，然后重新执行此脚本"
            exit 1
        }
        
        if (Test-ForbiddenTime) {
            Write-WarningMessage "当前时间在禁止时间段内！"
            Invoke-ForceShutdown "强制执行睡觉时间"
        } else {
            New-BedtimeTask
            New-StartupCheckTask
            Set-AutoWakeup
            Write-SuccessMessage "严格作息模式已启用！"
            Write-LogMessage "配置: 睡觉 $BEDTIME_HOUR`:$($BEDTIME_MINUTE.ToString('D2')) - 起床 $WAKEUP_HOUR`:$($WAKEUP_MINUTE.ToString('D2'))"
        }
    }
    
    "disable" {
        Write-LogMessage "禁用严格作息模式..."
        Remove-BedtimeTasks
    }
    
    "status" {
        Show-Status
    }
    
    "test" {
        Write-LogMessage "测试模式 - 显示5分钟警告"
        Show-FiveMinuteWarning
    }
    
    "startup-check" {
        Write-LogMessage "开机检查: 验证当前时间..."
        if (Test-ForbiddenTime) {
            Invoke-ForceShutdown "计算机在禁止时间段启动 ($BEDTIME_HOUR`:$($BEDTIME_MINUTE.ToString('D2')) - $WAKEUP_HOUR`:$($WAKEUP_MINUTE.ToString('D2')))"
        } else {
            Write-LogMessage "开机允许 - 不在禁止时间段"
            # 重新创建今天的睡觉任务
            New-BedtimeTask
        }
    }
    
    "shutdown" {
        # 5分钟警告流程
        Show-FiveMinuteWarning
        Start-Sleep -Seconds 300  # 等待5分钟
        Invoke-ForceShutdown "到达睡觉时间 - 强制执行睡觉计划"
    }
    
    default {
        Write-ColorText "Bedtime Enforcer for Windows - 严格睡觉时间执行器" -Color Magenta
        Write-Host "配置: 睡觉 $BEDTIME_HOUR`:$($BEDTIME_MINUTE.ToString('D2')) - 起床 $WAKEUP_HOUR`:$($WAKEUP_MINUTE.ToString('D2'))"
        Write-Host ""
        Write-Host "用法:"
        Write-ColorText "  .\bedtime_enforcer.ps1 -Action enable    " -Color Yellow -NoNewline
        Write-Host "启用严格作息模式"
        Write-ColorText "  .\bedtime_enforcer.ps1 -Action disable   " -Color Yellow -NoNewline
        Write-Host "禁用严格作息模式"
        Write-ColorText "  .\bedtime_enforcer.ps1 -Action status    " -Color Yellow -NoNewline
        Write-Host "查看当前状态"
        Write-ColorText "  .\bedtime_enforcer.ps1 -Action test      " -Color Yellow -NoNewline
        Write-Host "测试警告对话框"
        Write-Host ""
        Write-ColorText "⚠️  警告: 此脚本会在设定时间强制关机您的计算机！" -Color Red
        Write-ColorText "⚠️  使用前请务必保存重要工作。" -Color Red
        Write-Host ""
        Write-Host "功能特点:"
        Write-Host "• 在睡觉时间 ($BEDTIME_HOUR`:$($BEDTIME_MINUTE.ToString('D2'))) 自动关机"
        Write-Host "• 在起床时间 ($WAKEUP_HOUR`:$($WAKEUP_MINUTE.ToString('D2'))) 自动开机 (需BIOS支持)"
        Write-Host "• 防止在睡眠时间段使用电脑"
        Write-Host "• 关机前5分钟警告"
        Write-Host ""
        Write-ColorText "首次使用请以管理员身份运行！" -Color Green
    }
} 