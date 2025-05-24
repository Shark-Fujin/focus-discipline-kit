@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

title Bedtime Enforcer - 严格作息执行器

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [错误] 需要管理员权限才能运行此程序
    echo.
    echo 请右键点击此文件，选择 "以管理员身份运行"
    echo.
    pause
    exit /b 1
)

:MAIN_MENU
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                🌙 Bedtime Enforcer for Windows               ║
echo ║                    严格作息执行器 v1.0                        ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║                                                              ║
echo ║  这个工具将帮助您建立规律的睡眠习惯：                          ║
echo ║  • 在睡觉时间（22:30）自动关机                                ║
echo ║  • 在起床时间（06:30）自动开机                                ║
echo ║  • 防止在睡眠时间段使用电脑                                    ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 请选择操作：
echo.
echo  [1] 启用严格作息模式   (Enable)
echo  [2] 禁用严格作息模式   (Disable)  
echo  [3] 查看当前状态       (Status)
echo  [4] 测试警告对话框     (Test)
echo  [5] 打开PowerShell脚本目录
echo  [6] 查看帮助说明
echo  [0] 退出程序
echo.
echo ⚠️  警告：此程序会在设定时间强制关机您的计算机！
echo ⚠️  使用前请务必保存重要工作。
echo.

set /p choice="请输入选项 (0-6): "

if "%choice%"=="1" goto ENABLE
if "%choice%"=="2" goto DISABLE
if "%choice%"=="3" goto STATUS
if "%choice%"=="4" goto TEST
if "%choice%"=="5" goto OPEN_FOLDER
if "%choice%"=="6" goto HELP
if "%choice%"=="0" goto EXIT
goto INVALID_CHOICE

:ENABLE
cls
echo.
echo ═══════════════════════════════════════════════════════════════
echo  启用严格作息模式
echo ═══════════════════════════════════════════════════════════════
echo.
echo 正在启用严格作息模式...
echo.
powershell.exe -ExecutionPolicy Bypass -File "%~dp0bedtime_enforcer.ps1" -Action enable
echo.
echo 按任意键返回主菜单...
pause >nul
goto MAIN_MENU

:DISABLE
cls
echo.
echo ═══════════════════════════════════════════════════════════════
echo  禁用严格作息模式
echo ═══════════════════════════════════════════════════════════════
echo.
echo 正在禁用严格作息模式...
echo.
powershell.exe -ExecutionPolicy Bypass -File "%~dp0bedtime_enforcer.ps1" -Action disable
echo.
echo 按任意键返回主菜单...
pause >nul
goto MAIN_MENU

:STATUS
cls
echo.
echo ═══════════════════════════════════════════════════════════════
echo  当前状态
echo ═══════════════════════════════════════════════════════════════
echo.
powershell.exe -ExecutionPolicy Bypass -File "%~dp0bedtime_enforcer.ps1" -Action status
echo.
echo 按任意键返回主菜单...
pause >nul
goto MAIN_MENU

:TEST
cls
echo.
echo ═══════════════════════════════════════════════════════════════
echo  测试警告对话框
echo ═══════════════════════════════════════════════════════════════
echo.
echo 这将显示5分钟警告对话框（仅测试，不会关机）
echo.
powershell.exe -ExecutionPolicy Bypass -File "%~dp0bedtime_enforcer.ps1" -Action test
echo.
echo 按任意键返回主菜单...
pause >nul
goto MAIN_MENU

:OPEN_FOLDER
explorer.exe "%~dp0"
goto MAIN_MENU

:HELP
cls
echo.
echo ═══════════════════════════════════════════════════════════════
echo  帮助说明
echo ═══════════════════════════════════════════════════════════════
echo.
echo 📋 默认配置：
echo   • 睡觉时间：22:30 (晚上10点30分)
echo   • 起床时间：06:30 (早上6点30分)
echo   • 禁止时段：22:30 - 06:30
echo.
echo 🔧 自定义设置：
echo   编辑 bedtime_enforcer.ps1 文件顶部的配置变量
echo.
echo 🛠️ 工作原理：
echo   1. 使用Windows任务计划程序设置定时关机
echo   2. 创建开机检查任务防止在睡眠时间使用
echo   3. 支持自动唤醒（需要BIOS支持）
echo.
echo 📊 任务管理：
echo   可以在 "任务计划程序" (taskschd.msc) 中查看和管理
echo.
echo 🎯 生物钟调整建议：
echo   1. 渐进式调整：每天提前15分钟睡觉
echo   2. 坚持21天以上形成习惯
echo   3. 配合环境优化（调暗灯光、减少蓝光等）
echo   4. 固定起床时间，包括周末
echo.
echo 🔍 故障排除：
echo   • 确保以管理员身份运行
echo   • 检查PowerShell执行策略
echo   • 验证BIOS中的RTC唤醒设置
echo.
echo 📄 详细说明请参考：README_Windows.md
echo.
echo 按任意键返回主菜单...
pause >nul
goto MAIN_MENU

:INVALID_CHOICE
cls
echo.
echo [错误] 无效的选项，请输入 0-6 之间的数字
echo.
echo 按任意键重新选择...
pause >nul
goto MAIN_MENU

:EXIT
cls
echo.
echo 感谢使用 Bedtime Enforcer！
echo 希望这个工具能帮助您建立健康的睡眠习惯。
echo.
echo 记住：良好的睡眠是健康生活的基础 🌙
echo.
echo 程序即将退出...
timeout /t 3 /nobreak >nul
exit /b 0 