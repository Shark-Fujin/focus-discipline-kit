#!/bin/bash

# 安全配置脚本 - 只允许免密执行关机命令
# 这比将密码写入脚本安全得多

echo "🔒 配置安全的免密关机..."
echo

# 检查是否有sudo权限
if ! sudo -n true 2>/dev/null; then
    echo "请输入您的密码以配置安全设置（这是唯一一次需要输入密码）："
    sudo -v
fi

# 创建sudoers配置文件（只允许shutdown命令免密）
SUDOERS_FILE="/etc/sudoers.d/bedtime_enforcer"
USERNAME=$(whoami)

echo "正在创建安全配置文件..."

# 写入sudoers规则（只允许shutdown命令免密）
sudo tee "$SUDOERS_FILE" > /dev/null << EOF
# Bedtime Enforcer - 只允许免密执行关机命令
# 这比将密码写入脚本安全得多
$USERNAME ALL=(ALL) NOPASSWD: /sbin/shutdown
EOF

# 设置正确的权限
sudo chmod 440 "$SUDOERS_FILE"

# 验证配置
if sudo visudo -c; then
    echo "✅ 安全配置成功！"
    echo "现在shutdown命令可以免密执行"
    echo
    echo "测试一下："
    echo "sudo shutdown -h +60"  # 1小时后关机（测试用）
    echo
    echo "取消测试："
    echo "sudo shutdown -c"
    echo
else
    echo "❌ 配置失败，删除有问题的文件"
    sudo rm -f "$SUDOERS_FILE"
    exit 1
fi

echo "🎯 现在您可以安全使用Bedtime Enforcer了！" 