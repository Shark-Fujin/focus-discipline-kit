# 🌙 Bedtime Enforcer - Enhanced macOS版本

## ⭐ 增强功能概述

这是一个功能全面升级的macOS睡眠管理工具，具备以下增强特性：

### 🆕 新增功能
- **📢 双重警告系统**：15分钟 + 5分钟提醒
- **🔒 TOTP安全保护**：基于时间的一次性密码
- **🛡️ 进程保护**：防止脚本被意外终止
- **🧪 测试模式**：可以安全测试功能
- **📊 状态监控**：实时查看系统状态

### 🚫 移除功能
- **自动开机功能**：根据用户需求移除
- **简化权限管理**：专注于核心功能

## 🔐 安全机制详解

### TOTP (Time-based One-Time Password) 保护

**初始密钥**: `JBSWY3DPEHPK3PXP`
- 这是您的"主密钥"，用于生成验证码
- 每30秒生成一个新的6位数验证码
- 只有知道正确验证码才能禁用脚本

### 使用TOTP验证码

1. **生成验证码**：
   ```bash
   ./totp_generator.sh
   ```
   
2. **示例输出**：
   ```
   🔐 Bedtime Enforcer TOTP Generator
   ==================================
   
   Current TOTP Code: 502261
   Time until next code: 25 seconds
   
   💡 Use this code to disable Bedtime Enforcer
   🔄 Code refreshes every 30 seconds
   ```

3. **禁用脚本**：
   ```bash
   ./bedtime_enforcer.sh --disable
   # 然后输入当前的6位验证码
   ```

## 🚀 完整使用指南

### 1️⃣ 首次启用

```bash
# 设置执行权限
chmod +x bedtime_enforcer.sh

# 启用严格作息模式
./bedtime_enforcer.sh --enable
```

**启用后会发生什么**：
- 自动创建TOTP验证码生成器 (`totp_generator.sh`)
- 设置开机检查 (在禁止时间开机会立即关机)
- 启动后台监控进程
- 开始倒计时到22:30关机

### 2️⃣ 测试功能（推荐）

```bash
# 进入测试模式
./bedtime_enforcer.sh --test

# 选择测试选项：
# 1. 测试完整流程 (15分钟 -> 5分钟 -> 关机)
# 2. 测试15分钟警告
# 3. 测试5分钟警告  
# 4. 测试关机流程
```

**测试模式特点**：
- ✅ 会显示所有警告对话框
- ✅ 不会真正关机
- ✅ 可以验证脚本是否正常工作
- ✅ 安全无风险

### 3️⃣ 查看状态

```bash
./bedtime_enforcer.sh --status
```

**状态信息包括**：
- 当前时间和配置
- 是否在禁止时间段
- 距离睡觉时间
- 执行器运行状态

### 4️⃣ 生成验证码

```bash
./bedtime_enforcer.sh --generate-totp
# 或直接运行
./totp_generator.sh
```

### 5️⃣ 安全禁用

```bash
./bedtime_enforcer.sh --disable
# 输入TOTP验证码
```

## ⏰ 工作流程详解

### 正常日使用流程

```
启动脚本
    ↓
检查当前时间
    ↓
如果不在禁止时段 → 启动监控
    ↓
等待到22:15 → 15分钟警告 📢
    ↓
等待到22:25 → 5分钟警告 ⚠️
    ↓
等待到22:30 → 强制关机 🔒
```

### 禁止时段开机流程

```
开机 (22:30-06:30之间)
    ↓
LaunchAgent自动运行检查
    ↓
检测到禁止时间段
    ↓
立即显示警告对话框
    ↓
30秒后强制关机 🔒
```

## 🔧 自定义配置

### 修改时间设置

编辑 `bedtime_enforcer.sh` 文件顶部：

```bash
# Configuration
BEDTIME_HOUR=22      # 睡觉时间 - 小时 (0-23)
BEDTIME_MINUTE=30    # 睡觉时间 - 分钟 (0-59)
WAKEUP_HOUR=6        # 起床时间 - 小时 (0-23)
WAKEUP_MINUTE=30     # 起床时间 - 分钟 (0-59)
```

### 修改TOTP密钥

如果想要更换密钥，修改：

```bash
# Security Configuration
SECRET_KEY="YOUR_NEW_BASE32_KEY"  # 替换为您的密钥
```

**⚠️ 注意**：更换密钥后需要重新生成 `totp_generator.sh`

## 🧪 测试与验证

### 完整测试流程

1. **基础功能测试**：
   ```bash
   ./bedtime_enforcer.sh --test
   # 选择选项4：测试关机流程
   ```

2. **警告系统测试**：
   ```bash
   ./bedtime_enforcer.sh --test
   # 选择选项1：测试完整流程
   ```

3. **TOTP安全测试**：
   ```bash
   # 1. 启用脚本
   ./bedtime_enforcer.sh --enable
   
   # 2. 获取验证码
   ./totp_generator.sh
   
   # 3. 测试禁用
   ./bedtime_enforcer.sh --disable
   # 输入验证码
   ```

4. **状态监控测试**：
   ```bash
   ./bedtime_enforcer.sh --status
   ```

### 验证实际关机能力

**⚠️ 警告：以下测试会真正关机！**

1. **临时修改时间测试**：
   ```bash
   # 修改脚本中的BEDTIME_HOUR和BEDTIME_MINUTE为当前时间+2分钟
   # 启用脚本并观察是否按时关机
   ```

2. **禁止时段测试**：
   ```bash
   # 修改时间设置，使当前时间处于禁止时段
   # 重启电脑验证是否立即关机
   ```

## 🛡️ 安全特性

### 进程保护机制

1. **信号拦截**：捕获 SIGTERM、SIGINT、SIGQUIT 信号
2. **PID文件**：记录进程ID，防止重复启动
3. **锁文件**：创建锁定标识
4. **优先级提升**：以更高优先级运行（需要root权限）

### TOTP算法

- **时间窗口**：30秒
- **容错机制**：允许当前和前一个时间窗口的验证码
- **算法**：基于HMAC-SHA1的简化TOTP实现

## 🔍 故障排除

### 常见问题

#### ❓ 脚本无法执行
```bash
chmod +x bedtime_enforcer.sh
./bedtime_enforcer.sh --status
```

#### ❓ TOTP验证失败
```bash
# 确保系统时间正确
date

# 重新生成验证码
./totp_generator.sh

# 在验证码有效期内（30秒）输入
```

#### ❓ 进程无法终止
```bash
# 使用安全禁用方式
./bedtime_enforcer.sh --disable

# 如果忘记验证码，可以：
# 1. 重启电脑
# 2. 手动删除文件
rm -f /tmp/bedtime_enforcer.*
launchctl unload ~/Library/LaunchAgents/com.bedtime.enforcer.plist
```

#### ❓ 开机检查不工作
```bash
# 检查LaunchAgent状态
launchctl list | grep bedtime

# 重新安装
./bedtime_enforcer.sh --enable
```

### 紧急情况处理

如果脚本出现问题无法正常禁用：

1. **重启电脑** - 最简单的方法
2. **删除相关文件**：
   ```bash
   rm -f ~/Library/LaunchAgents/com.bedtime.enforcer.plist
   rm -f /tmp/bedtime_enforcer.*
   launchctl unload ~/Library/LaunchAgents/com.bedtime.enforcer.plist
   ```

## 📊 系统要求

- macOS 10.14+ (支持AppleScript)
- bash shell
- sudo权限 (仅关机时需要)
- 包含以下命令：`date`, `sleep`, `osascript`, `shasum`

## 🎯 最佳实践

### 使用建议

1. **首次使用前测试**：
   - 先运行测试模式验证所有功能
   - 确保TOTP生成器正常工作
   - 验证警告对话框显示正常

2. **渐进式调整**：
   - 第一周：设置较晚的睡觉时间适应
   - 每周提前15分钟
   - 直到达到理想时间

3. **备用方案**：
   - 保存TOTP生成器到安全位置
   - 记录初始密钥：`JBSWY3DPEHPK3PXP`
   - 了解紧急禁用方法

4. **配合其他习惯**：
   - 睡前1小时停止工作
   - 准备睡前阅读材料
   - 调暗房间灯光

## 📱 TOTP密钥信息

**初始密钥**: `JBSWY3DPEHPK3PXP`

**如何在真实的验证器应用中使用**：
1. 下载Google Authenticator或类似应用
2. 选择"手动输入密钥"
3. 输入密钥：`JBSWY3DPEHPK3PXP`
4. 设置名称：`Bedtime Enforcer`
5. 时间间隔：30秒

**注意**：脚本内置的TOTP生成器是简化版本，如需更高安全性，建议使用专业的验证器应用。

---

**祝您使用愉快，建立健康的睡眠习惯！** 🌙✨ 