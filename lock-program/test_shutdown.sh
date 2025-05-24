#!/bin/bash

# Test Script for Bedtime Enforcer - 测试关机功能
# 这个脚本可以帮您安全地测试Bedtime Enforcer的实际关机能力

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🧪 Bedtime Enforcer 关机测试脚本${NC}"
echo "========================================"
echo
echo -e "${YELLOW}⚠️  警告：这个测试会真正关机您的电脑！${NC}"
echo -e "${YELLOW}⚠️  请确保已保存所有重要工作！${NC}"
echo

# 获取当前时间
current_time=$(date '+%H:%M')
echo "当前时间: $current_time"
echo

echo "选择测试类型："
echo "1. 快速测试 (2分钟后关机)"
echo "2. 标准测试 (5分钟后关机)"
echo "3. 禁止时段测试 (立即模拟禁止时间开机)"
echo "4. 取消测试"
echo

read -p "请选择 (1-4): " choice

case $choice in
    1)
        # 快速测试 - 2分钟后关机
        echo
        echo -e "${GREEN}✅ 配置快速测试 (2分钟后关机)${NC}"
        
        # 计算2分钟后的时间
        target_time=$(date -v+2M '+%H:%M')
        target_hour=$(date -v+2M '+%H' | sed 's/^0*//')
        target_minute=$(date -v+2M '+%M' | sed 's/^0*//')
        
        # 备份原始脚本
        cp bedtime_enforcer.sh bedtime_enforcer.sh.backup
        
        # 修改脚本中的时间
        sed -i '' "s/BEDTIME_HOUR=22/BEDTIME_HOUR=$target_hour/" bedtime_enforcer.sh
        sed -i '' "s/BEDTIME_MINUTE=30/BEDTIME_MINUTE=$target_minute/" bedtime_enforcer.sh
        
        echo "已设置关机时间为: $target_time"
        echo
        echo -e "${YELLOW}开始倒计时...${NC}"
        echo "15分钟警告: 立即显示"
        echo "5分钟警告: 立即显示"  
        echo "关机时间: $target_time"
        echo
        
        # 启动测试
        ./bedtime_enforcer.sh --enable
        ;;
        
    2)
        # 标准测试 - 5分钟后关机
        echo
        echo -e "${GREEN}✅ 配置标准测试 (5分钟后关机)${NC}"
        
        # 计算5分钟后的时间
        target_time=$(date -v+5M '+%H:%M')
        target_hour=$(date -v+5M '+%H' | sed 's/^0*//')
        target_minute=$(date -v+5M '+%M' | sed 's/^0*//')
        
        # 备份原始脚本
        cp bedtime_enforcer.sh bedtime_enforcer.sh.backup
        
        # 修改脚本中的时间
        sed -i '' "s/BEDTIME_HOUR=22/BEDTIME_HOUR=$target_hour/" bedtime_enforcer.sh
        sed -i '' "s/BEDTIME_MINUTE=30/BEDTIME_MINUTE=$target_minute/" bedtime_enforcer.sh
        
        echo "已设置关机时间为: $target_time"
        echo
        echo -e "${YELLOW}测试流程:${NC}"
        echo "立即显示: 15分钟警告"
        echo "立即显示: 5分钟警告"
        echo "5分钟后: 强制关机"
        echo
        
        # 启动测试
        ./bedtime_enforcer.sh --enable
        ;;
        
    3)
        # 禁止时段测试
        echo
        echo -e "${GREEN}✅ 配置禁止时段测试${NC}"
        
        # 备份原始脚本
        cp bedtime_enforcer.sh bedtime_enforcer.sh.backup
        
        # 设置当前时间为禁止时段
        current_hour=$(date '+%H' | sed 's/^0*//')
        current_minute=$(date '+%M' | sed 's/^0*//')
        
        # 将起床时间设置为1小时后，睡觉时间设置为当前时间前1分钟
        wakeup_hour=$(date -v+1H '+%H' | sed 's/^0*//')
        bedtime_minute=$((current_minute - 1))
        if [ $bedtime_minute -lt 0 ]; then
            bedtime_minute=$((bedtime_minute + 60))
            bedtime_hour=$((current_hour - 1))
        else
            bedtime_hour=$current_hour
        fi
        
        # 修改脚本
        sed -i '' "s/BEDTIME_HOUR=22/BEDTIME_HOUR=$bedtime_hour/" bedtime_enforcer.sh
        sed -i '' "s/BEDTIME_MINUTE=30/BEDTIME_MINUTE=$bedtime_minute/" bedtime_enforcer.sh
        sed -i '' "s/WAKEUP_HOUR=6/WAKEUP_HOUR=$wakeup_hour/" bedtime_enforcer.sh
        
        echo "已设置禁止时段: $(printf "%02d:%02d" $bedtime_hour $bedtime_minute) - $(printf "%02d:%02d" $wakeup_hour 30)"
        echo "当前时间在禁止时段内，应该立即关机"
        echo
        
        # 启动测试
        ./bedtime_enforcer.sh --enable
        ;;
        
    4)
        echo
        echo -e "${GREEN}✅ 测试已取消${NC}"
        exit 0
        ;;
        
    *)
        echo
        echo -e "${RED}❌ 无效选择${NC}"
        exit 1
        ;;
esac

echo
echo -e "${BLUE}📝 测试说明：${NC}"
echo "• 如果测试成功，电脑会按时关机"
echo "• 如果想取消测试，请立即获取TOTP验证码并禁用："
echo "  ./totp_generator.sh"
echo "  ./bedtime_enforcer.sh --disable"
echo
echo "• 重启后恢复原始设置："
echo "  mv bedtime_enforcer.sh.backup bedtime_enforcer.sh"
echo
echo -e "${GREEN}🚀 测试已启动！${NC}" 