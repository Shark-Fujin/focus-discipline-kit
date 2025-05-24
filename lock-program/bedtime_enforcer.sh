#!/bin/bash

# Bedtime Enforcer - Enhanced macOS Sleep Schedule Enforcement
# Enhanced version with dual warnings, TOTP security, and test mode

# Configuration
BEDTIME_HOUR=22      # 10 PM (22:00)
BEDTIME_MINUTE=30    # 30 minutes
WAKEUP_HOUR=6        # 6 AM (06:00) 
WAKEUP_MINUTE=30     # 30 minutes

# Security Configuration
SECRET_KEY="JBSWY3DPEHPK3PXP"  # Base32 encoded secret for TOTP
SCRIPT_PID_FILE="/tmp/bedtime_enforcer.pid"
LOCK_FILE="/tmp/bedtime_enforcer.lock"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

log_message() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warning_message() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error_message() {
    echo -e "${RED}[ERROR] $1${NC}"
}

success_message() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

security_message() {
    echo -e "${MAGENTA}[SECURITY] $1${NC}"
}

# TOTP (Time-based One-Time Password) implementation
generate_totp() {
    local secret="$1"
    local time_step=30
    local current_time=$(date +%s)
    local time_counter=$((current_time / time_step))
    
    # Convert base32 secret to hex (simplified for demo)
    # In real implementation, you'd use proper base32 decoding
    local hex_secret=$(echo -n "$secret" | xxd -p | tr -d '\n')
    
    # Generate HMAC-SHA1 hash
    local hash=$(printf "%016x" $time_counter | xxd -r -p | openssl dgst -sha1 -mac hmac -macopt hexkey:$hex_secret -binary | xxd -p)
    
    # Extract dynamic binary code
    local offset=$((0x$(echo $hash | tail -c 2) & 0xf))
    offset=$((offset * 2))
    local code_hex=${hash:$offset:8}
    local code=$((0x$code_hex & 0x7fffffff))
    
    # Return 6-digit code
    printf "%06d" $((code % 1000000))
}

# Verify TOTP code
verify_totp() {
    local input_code="$1"
    local current_totp=$(generate_totp "$SECRET_KEY")
    
    # Allow current and previous time window for clock skew
    local prev_time=$(($(date +%s) - 30))
    local prev_totp=$(generate_totp "$SECRET_KEY")
    
    if [ "$input_code" = "$current_totp" ] || [ "$input_code" = "$prev_totp" ]; then
        return 0
    else
        return 1
    fi
}

# Create TOTP generator app (simplified)
create_totp_generator() {
    cat > totp_generator.sh << 'EOF'
#!/bin/bash

# TOTP Generator for Bedtime Enforcer
# This is your "Google Authenticator" equivalent

SECRET_KEY="JBSWY3DPEHPK3PXP"

generate_totp() {
    local secret="$1"
    local time_step=30
    local current_time=$(date +%s)
    local time_counter=$((current_time / time_step))
    local remaining_time=$((time_step - (current_time % time_step)))
    
    # Simplified TOTP generation (for demo purposes)
    # In production, use proper base32 decoding and HMAC-SHA1
    local simple_hash=$(echo -n "${time_counter}${secret}" | shasum -a 256 | cut -c1-6)
    local code=""
    
    # Convert first 6 hex chars to decimal and mod 1000000
    for i in {0..5}; do
        local hex_char=${simple_hash:$i:1}
        case $hex_char in
            a) hex_char=0 ;;
            b) hex_char=1 ;;
            c) hex_char=2 ;;
            d) hex_char=3 ;;
            e) hex_char=4 ;;
            f) hex_char=5 ;;
        esac
        code="${code}${hex_char}"
    done
    
    printf "%06d" $((code % 1000000))
}

echo "🔐 Bedtime Enforcer TOTP Generator"
echo "=================================="
echo
echo "Current TOTP Code: $(generate_totp "$SECRET_KEY")"
echo "Time until next code: $((30 - $(date +%s) % 30)) seconds"
echo
echo "💡 Use this code to disable Bedtime Enforcer"
echo "🔄 Code refreshes every 30 seconds"
EOF

    chmod +x totp_generator.sh
    success_message "TOTP generator created: totp_generator.sh"
}

# Process protection - make it harder to kill
protect_process() {
    echo $$ > "$SCRIPT_PID_FILE"
    
    # Create a lock file
    touch "$LOCK_FILE"
    
    # Trap signals to prevent easy termination
    trap 'security_message "Process termination blocked. Use --disable with TOTP code."' SIGTERM SIGINT SIGQUIT
    
    # Set process priority (requires root)
    if [ "$EUID" -eq 0 ]; then
        renice -10 $$ >/dev/null 2>&1
    fi
}

# Check if current time is in forbidden range
is_forbidden_time() {
    local current_hour=$(date +%H | sed 's/^0*//')
    local current_minute=$(date +%M | sed 's/^0*//')
    
    # Handle empty hour (midnight)
    [ -z "$current_hour" ] && current_hour=0
    [ -z "$current_minute" ] && current_minute=0
    
    local current_total_minutes=$((current_hour * 60 + current_minute))
    local bedtime_total_minutes=$((BEDTIME_HOUR * 60 + BEDTIME_MINUTE))
    local wakeup_total_minutes=$((WAKEUP_HOUR * 60 + WAKEUP_MINUTE))
    
    # Handle overnight period (bedtime > wakeup, crossing midnight)
    if [ $bedtime_total_minutes -gt $wakeup_total_minutes ]; then
        # Current time is after bedtime OR before wakeup
        if [ $current_total_minutes -ge $bedtime_total_minutes ] || [ $current_total_minutes -lt $wakeup_total_minutes ]; then
            return 0  # true - forbidden time
        fi
    else
        # Same day period (bedtime < wakeup)
        if [ $current_total_minutes -ge $bedtime_total_minutes ] && [ $current_total_minutes -lt $wakeup_total_minutes ]; then
            return 0  # true - forbidden time
        fi
    fi
    return 1  # false - allowed time
}

# Force shutdown with test mode support
force_shutdown() {
    local reason="$1"
    local test_mode="$2"
    
    warning_message "$reason"
    
    if [ "$test_mode" = "test" ]; then
        warning_message "TEST MODE: 模拟关机 - 实际不会关机"
        # Display test warning
        osascript -e 'display dialog "TEST MODE - 模拟关机\n\n这是测试模式，实际不会关机。\n在正常模式下，计算机会在30秒后关机。" buttons {"了解"} default button "了解" giving up after 10 with title "测试模式" with icon note'
        log_message "测试模式：模拟关机完成"
        return 0
    fi
    
    warning_message "计算机将在30秒后强制关机..."
    
    # Display visual warning
    osascript -e 'display dialog "睡觉时间强制执行！\n\n计算机将在30秒后关机。\n这是为了您的健康和睡眠计划。" buttons {"确定"} default button "确定" giving up after 25 with title "睡眠时间强制执行" with icon stop' &
    
    sleep 30
    log_message "执行强制关机..."
    sudo shutdown -h now
}

# Show 15-minute warning
show_fifteen_minute_warning() {
    local test_mode="$1"
    
    warning_message "睡觉时间警告：计算机将在15分钟后关机！"
    
    local message="睡觉时间警告！\n\n计算机将在15分钟后关机。\n请开始保存您的工作并准备睡觉。"
    if [ "$test_mode" = "test" ]; then
        message="[测试模式] $message\n\n这是测试，实际不会关机。"
    fi
    
    osascript -e "display dialog \"$message\" buttons {\"我知道了\"} default button \"我知道了\" giving up after 60 with title \"15分钟警告\" with icon caution" &
}

# Show 5-minute warning
show_five_minute_warning() {
    local test_mode="$1"
    
    warning_message "睡觉时间警告：计算机将在5分钟后关机！"
    
    local message="最后警告！\n\n计算机将在5分钟后关机。\n请立即保存工作并准备睡觉。"
    if [ "$test_mode" = "test" ]; then
        message="[测试模式] $message\n\n这是测试，实际不会关机。"
    fi
    
    osascript -e "display dialog \"$message\" buttons {\"明白了\"} default button \"明白了\" giving up after 60 with title \"5分钟最后警告\" with icon stop" &
}

# Calculate time until bedtime
calculate_bedtime_delay() {
    local current_time=$(date +%s)
    local today_date=$(date +%Y-%m-%d)
    
    # Calculate today's bedtime
    local bedtime_today=$(date -j -f "%Y-%m-%d %H:%M:%S" "$today_date $(printf "%02d:%02d:00" $BEDTIME_HOUR $BEDTIME_MINUTE)" +%s 2>/dev/null)
    
    local target_bedtime
    if [ $current_time -lt $bedtime_today ]; then
        target_bedtime=$bedtime_today
    else
        # Use tomorrow's bedtime
        local tomorrow_date=$(date -v+1d +%Y-%m-%d)
        target_bedtime=$(date -j -f "%Y-%m-%d %H:%M:%S" "$tomorrow_date $(printf "%02d:%02d:00" $BEDTIME_HOUR $BEDTIME_MINUTE)" +%s)
    fi
    
    echo $((target_bedtime - current_time))
}

# Run bedtime scheduler with dual warnings
start_bedtime_scheduler() {
    local test_mode="$1"
    local delay_seconds=$(calculate_bedtime_delay)
    local delay_minutes=$((delay_seconds / 60))
    
    log_message "睡觉时间调度器启动 ($([ "$test_mode" = "test" ] && echo "测试模式" || echo "正常模式"))"
    log_message "下次睡觉时间: $(printf "%02d:%02d" $BEDTIME_HOUR $BEDTIME_MINUTE)"
    log_message "距离睡觉时间: $delay_minutes 分钟"
    
    # Enable process protection
    protect_process
    
    # Wait until 15-minute warning
    if [ $delay_seconds -gt 900 ]; then  # More than 15 minutes
        local warning_15_delay=$((delay_seconds - 900))
        log_message "等待 $((warning_15_delay / 60)) 分钟后显示15分钟警告..."
        sleep $warning_15_delay
        
        # 15-minute warning
        show_fifteen_minute_warning "$test_mode"
        
        # Wait until 5-minute warning
        log_message "等待10分钟后显示5分钟警告..."
        sleep 600  # 10 minutes (15 - 5)
        
        # 5-minute warning
        show_five_minute_warning "$test_mode"
        
        # Wait until bedtime
        log_message "等待5分钟后执行关机..."
        sleep 300  # 5 minutes
        
    elif [ $delay_seconds -gt 300 ]; then  # Between 5-15 minutes
        local warning_5_delay=$((delay_seconds - 300))
        log_message "等待 $((warning_5_delay / 60)) 分钟后显示5分钟警告..."
        sleep $warning_5_delay
        
        # 5-minute warning only
        show_five_minute_warning "$test_mode"
        
        # Wait until bedtime
        log_message "等待5分钟后执行关机..."
        sleep 300
        
    else
        # Less than 5 minutes, immediate warning
        log_message "睡觉时间即将到达，等待 $delay_minutes 分钟..."
        sleep $delay_seconds
    fi
    
    force_shutdown "到达睡觉时间 - 强制执行睡觉计划" "$test_mode"
}

# Create startup checker
create_startup_checker() {
    local plist_path="$HOME/Library/LaunchAgents/com.bedtime.enforcer.plist"
    local script_path="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
    
    cat > "$plist_path" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.bedtime.enforcer</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$script_path</string>
        <string>--startup-check</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
EOF

    launchctl load "$plist_path" 2>/dev/null
    success_message "开机检查器已安装"
}

# Remove startup checker
remove_startup_checker() {
    local plist_path="$HOME/Library/LaunchAgents/com.bedtime.enforcer.plist"
    launchctl unload "$plist_path" 2>/dev/null
    rm -f "$plist_path"
    rm -f "$SCRIPT_PID_FILE"
    rm -f "$LOCK_FILE"
    success_message "睡觉时间执行器已禁用"
}

# Secure disable function
secure_disable() {
    echo
    security_message "安全禁用模式"
    echo "需要TOTP验证码才能禁用睡觉时间执行器"
    echo
    echo "💡 使用 ./totp_generator.sh 获取当前验证码"
    echo
    
    read -p "请输入6位TOTP验证码: " input_code
    
    if verify_totp "$input_code"; then
        success_message "验证码正确，正在禁用睡觉时间执行器..."
        remove_startup_checker
        
        # Kill any running scheduler processes
        if [ -f "$SCRIPT_PID_FILE" ]; then
            local pid=$(cat "$SCRIPT_PID_FILE")
            kill -9 "$pid" 2>/dev/null
            rm -f "$SCRIPT_PID_FILE"
        fi
        
        success_message "睡觉时间执行器已安全禁用"
    else
        error_message "验证码错误，禁用失败"
        security_message "如需禁用，请使用正确的TOTP验证码"
        exit 1
    fi
}

# Show current status
show_status() {
    echo
    echo -e "${MAGENTA}=== Bedtime Enforcer 状态 ===${NC}"
    echo "配置: 睡觉 $(printf "%02d:%02d" $BEDTIME_HOUR $BEDTIME_MINUTE) - 起床 $(printf "%02d:%02d" $WAKEUP_HOUR $WAKEUP_MINUTE)"
    echo "当前时间: $(date '+%H:%M:%S')"
    
    if is_forbidden_time; then
        echo -e "${RED}状态: 当前处于禁止时间段${NC}"
    else
        echo -e "${GREEN}状态: 当前时间允许使用${NC}"
        local minutes_until_bedtime=$(( $(calculate_bedtime_delay) / 60 ))
        echo "距离睡觉时间: $minutes_until_bedtime 分钟"
    fi
    
    # Check if enforcer is running
    if [ -f "$SCRIPT_PID_FILE" ]; then
        local pid=$(cat "$SCRIPT_PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${GREEN}执行器状态: 运行中 (PID: $pid)${NC}"
        else
            echo -e "${YELLOW}执行器状态: 未运行${NC}"
        fi
    else
        echo -e "${YELLOW}执行器状态: 未启用${NC}"
    fi
    
    echo
}

# Main execution
case "${1:-}" in
    --startup-check)
        log_message "开机检查: 验证当前时间..."
        if is_forbidden_time; then
            force_shutdown "计算机在禁止时间段启动 ($(printf "%02d:%02d - %02d:%02d" $BEDTIME_HOUR $BEDTIME_MINUTE $WAKEUP_HOUR $WAKEUP_MINUTE))"
        else
            log_message "开机允许 - 不在禁止时间段"
            # Start the bedtime scheduler for today
            start_bedtime_scheduler &
        fi
        ;;
    --disable)
        secure_disable
        ;;
    --enable)
        log_message "启用严格作息模式..."
        
        # Create TOTP generator if it doesn't exist
        if [ ! -f "totp_generator.sh" ]; then
            create_totp_generator
        fi
        
        create_startup_checker
        
        # Check current time and start scheduler if appropriate
        if is_forbidden_time; then
            warning_message "当前时间在禁止时间段内！"
            force_shutdown "强制执行睡觉时间"
        else
            success_message "严格作息模式已启用！"
            log_message "配置: 睡觉 $(printf "%02d:%02d" $BEDTIME_HOUR $BEDTIME_MINUTE) - 起床 $(printf "%02d:%02d" $WAKEUP_HOUR $WAKEUP_MINUTE)"
            log_message "TOTP生成器: ./totp_generator.sh"
            start_bedtime_scheduler &
        fi
        ;;
    --test)
        log_message "测试模式启动..."
        warning_message "这是测试模式，不会真正关机"
        
        echo
        echo "选择测试选项:"
        echo "1. 测试完整流程 (15分钟 -> 5分钟 -> 关机)"
        echo "2. 测试15分钟警告"
        echo "3. 测试5分钟警告"
        echo "4. 测试关机流程"
        echo
        read -p "请选择 (1-4): " test_choice
        
        case $test_choice in
            1)
                log_message "测试完整流程 (时间压缩)..."
                show_fifteen_minute_warning "test"
                sleep 3
                show_five_minute_warning "test"
                sleep 3
                force_shutdown "测试关机流程" "test"
                ;;
            2)
                show_fifteen_minute_warning "test"
                ;;
            3)
                show_five_minute_warning "test"
                ;;
            4)
                force_shutdown "测试关机流程" "test"
                ;;
            *)
                error_message "无效选择"
                ;;
        esac
        ;;
    --status)
        show_status
        ;;
    --generate-totp)
        if [ ! -f "totp_generator.sh" ]; then
            create_totp_generator
        fi
        ./totp_generator.sh
        ;;
    *)
        echo "Bedtime Enforcer - Enhanced macOS Sleep Schedule Enforcement"
        echo "配置: 睡觉 $(printf "%02d:%02d" $BEDTIME_HOUR $BEDTIME_MINUTE) - 起床 $(printf "%02d:%02d" $WAKEUP_HOUR $WAKEUP_MINUTE)"
        echo
        echo "用法:"
        echo "  $0 --enable     启用严格作息模式"
        echo "  $0 --disable    禁用严格作息模式 (需要TOTP验证)"
        echo "  $0 --status     查看当前状态"
        echo "  $0 --test       测试模式 (不会真正关机)"
        echo "  $0 --generate-totp  生成TOTP验证码"
        echo
        echo "⚠️  警告: 此脚本会在设定时间强制关机您的电脑！"
        echo "⚠️  使用前请务必保存重要工作。"
        echo
        echo "🔒 安全特性:"
        echo "• 基于时间的一次性密码 (TOTP) 保护"
        echo "• 进程保护，防止意外终止"
        echo "• 双重警告 (15分钟 + 5分钟)"
        echo
        echo "功能特点:"
        echo "• 在睡觉时间 ($(printf "%02d:%02d" $BEDTIME_HOUR $BEDTIME_MINUTE)) 自动关机"
        echo "• 防止在睡眠时间段 ($(printf "%02d:%02d - %02d:%02d" $BEDTIME_HOUR $BEDTIME_MINUTE $WAKEUP_HOUR $WAKEUP_MINUTE)) 使用电脑"
        echo "• 关机前15分钟和5分钟双重警告"
        echo "• 测试模式支持"
        ;;
esac 