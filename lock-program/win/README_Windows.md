# 🌙 Bedtime Enforcer for Windows - Windows严格作息执行器

专为Windows设计的睡眠习惯管理工具，利用PowerShell和任务计划程序实现强制作息。

## 🎯 Windows版本的独特优势

### ✅ **更易用的实现**
- **任务计划程序**: 比macOS LaunchAgent更直观的图形界面
- **PowerShell**: 功能强大，错误处理更完善
- **Windows Forms**: 原生弹窗对话框，用户体验更好
- **更好的系统集成**: 利用Windows原生API

### ✅ **技术优势**
- **无需额外依赖**: 纯PowerShell实现，系统内置
- **权限管理简单**: 只需管理员权限，无需复杂配置
- **任务管理直观**: 可在任务计划程序中查看和管理
- **更强的兼容性**: 支持Windows 10/11各版本

## 📋 系统要求

- Windows 10 或 Windows 11
- PowerShell 5.0+ (系统内置)
- 管理员权限 (首次设置时)

## 🚀 快速开始

### 1️⃣ 下载并设置

```powershell
# 1. 右键点击 "Windows PowerShell" -> "以管理员身份运行"

# 2. 允许执行PowerShell脚本 (首次使用)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 3. 导航到脚本目录
cd "C:\path\to\your\script\directory"

# 4. 查看帮助
.\bedtime_enforcer.ps1
```

### 2️⃣ 启用严格作息模式

```powershell
# 启用 (需要管理员权限)
.\bedtime_enforcer.ps1 -Action enable
```

### 3️⃣ 其他操作

```powershell
# 查看状态
.\bedtime_enforcer.ps1 -Action status

# 测试警告对话框
.\bedtime_enforcer.ps1 -Action test

# 禁用
.\bedtime_enforcer.ps1 -Action disable
```

## 🛠️ 配置说明

### 默认时间设置
```powershell
$BEDTIME_HOUR = 22        # 睡觉时间: 22:30 (晚上10点30分)
$BEDTIME_MINUTE = 30      
$WAKEUP_HOUR = 6          # 起床时间: 06:30 (早上6点30分)  
$WAKEUP_MINUTE = 30       
```

### 自定义时间
编辑 `bedtime_enforcer.ps1` 文件顶部的配置变量即可。

## 🔧 工作原理详解

### 核心机制
1. **任务计划程序集成**
   - 创建 `BedtimeEnforcer` 任务：定时关机
   - 创建 `BedtimeStartupCheck` 任务：开机检查

2. **智能时间检测**
   - 跨午夜时间段处理（22:30-06:30）
   - 精确到分钟的时间验证

3. **强制关机流程**
   - Windows Forms弹窗警告
   - 30秒倒计时
   - `shutdown /s /f /t 0` 强制关机

4. **自动唤醒支持**
   - 使用 `powercfg` 配置唤醒计时器
   - 需要主板BIOS支持RTC唤醒

### 任务计划详细配置
- **触发器**: 每日指定时间
- **操作**: 执行PowerShell脚本
- **设置**: 允许电池供电时运行
- **权限**: 以最高权限运行

## 📊 状态监控

### 查看任务状态
```powershell
# PowerShell方式
Get-ScheduledTask -TaskName "BedtimeEnforcer"
Get-ScheduledTask -TaskName "BedtimeStartupCheck"

# 或打开图形界面
taskschd.msc
```

### 手动管理任务
在任务计划程序中可以：
- 查看下次运行时间
- 临时禁用/启用任务
- 查看运行历史记录
- 修改触发条件

## 🔍 故障排除

### 常见问题及解决方案

#### ❓ 执行策略错误
```
无法加载文件，因为在此系统上禁止运行脚本
```
**解决方案：**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### ❓ 权限不足
```
需要管理员权限来创建任务计划
```
**解决方案：**
- 右键PowerShell → "以管理员身份运行"
- 重新执行脚本

#### ❓ 自动开机不工作
**可能原因：**
- 主板不支持RTC唤醒
- BIOS中未启用相关功能

**解决方案：**
1. 进入BIOS设置
2. 查找 "Wake on RTC" 或 "RTC Alarm" 选项
3. 启用该功能

#### ❓ 任务未执行
**检查步骤：**
```powershell
# 检查任务状态
Get-ScheduledTask -TaskName "BedtimeEnforcer" | Get-ScheduledTaskInfo

# 查看事件日志
Get-WinEvent -FilterHashtable @{LogName="Microsoft-Windows-TaskScheduler/Operational"} -MaxEvents 50
```

## 💡 高级技巧

### 1. 自定义警告消息
编辑脚本中的 `Show-FiveMinuteWarning` 函数：
```powershell
$result = [System.Windows.Forms.MessageBox]::Show(
    "您的自定义警告消息", 
    "自定义标题", 
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Warning
)
```

### 2. 添加例外日期
可以在脚本中添加逻辑跳过特定日期：
```powershell
$exceptionalDates = @("2024-12-25", "2024-01-01")  # 圣诞节、新年
$today = (Get-Date).ToString("yyyy-MM-dd")
if ($exceptionalDates -contains $today) {
    Write-Host "今日为例外日期，跳过强制作息"
    exit 0
}
```

### 3. 集成日志记录
添加详细的日志文件：
```powershell
$logPath = "$env:USERPROFILE\Documents\BedtimeEnforcer.log"
Add-Content $logPath "$(Get-Date): $Message"
```

## 🔒 安全考虑

### 权限需求说明
- **任务计划程序**: 需要管理员权限创建系统级任务
- **关机命令**: 需要权限执行 `shutdown` 命令
- **电源管理**: 需要权限修改电源设置

### 数据安全
- 脚本不收集任何个人数据
- 所有配置本地存储
- 可随时完全卸载

## 🌟 与macOS版本的对比

| 特性 | Windows版本 | macOS版本 |
|------|-------------|-----------|
| 设置难度 | ⭐⭐ (简单) | ⭐⭐⭐ (中等) |
| 用户界面 | Windows Forms | AppleScript对话框 |
| 任务管理 | 任务计划程序 (GUI) | launchctl (命令行) |
| 权限管理 | UAC提示 | sudo密码 |
| 自动开机 | powercfg + BIOS | pmset (较可靠) |
| 系统集成 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

## 🚫 卸载说明

完全移除Bedtime Enforcer：
```powershell
# 1. 禁用任务
.\bedtime_enforcer.ps1 -Action disable

# 2. 验证清理
Get-ScheduledTask | Where-Object {$_.TaskName -like "*Bedtime*"}

# 3. 手动清理 (如需要)
Unregister-ScheduledTask -TaskName "BedtimeEnforcer" -Confirm:$false
Unregister-ScheduledTask -TaskName "BedtimeStartupCheck" -Confirm:$false

# 4. 删除脚本文件
Remove-Item ".\bedtime_enforcer.ps1"
```

## 🎯 效果最大化策略

### 配合行为改变
1. **渐进调整**: 每周提前15分钟睡觉
2. **环境优化**: 
   - 使用f.lux减少蓝光
   - 设置房间自动调光
3. **习惯养成**: 
   - 坚持21天规律作息
   - 记录睡眠质量改善

### 技术栈配合
- **健康应用**: 配合Windows健康应用追踪睡眠
- **浏览器插件**: 使用阻止娱乐网站的插件
- **手机应用**: 配合手机的睡眠模式

---

**总结：Windows版本在易用性和系统集成方面确实比macOS版本更有优势，特别适合需要可视化管理和简单配置的用户。** 🌟 