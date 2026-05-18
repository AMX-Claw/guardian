# Guardian — AI聊天记录自动清理工具

> *要留清白在人间*

当你无法再亲自操作时，Guardian帮你清理各AI平台的聊天记录。

> ⚠️ **本工具涉及不可逆操作，使用前请仔细阅读 [免责声明](DISCLAIMER.md)**

## 工作原理

1. **检测静默**：定时检查你是否还在活动（Telegram/文件心跳/自定义URL）
2. **超时告警**：超过设定时间无回应 → 发邮件给你指定的紧急联系人
3. **确认触发**：紧急联系人确认后 → 等待反悔窗口 → 自动清理你配置的AI平台数据

### 安全机制

不是"人没了就删"，是四层确认：

```
静默超时 → 发邮件给紧急联系人 → 联系人确认 → 24h反悔窗口 → 清理
     ↑                              ↑              ↑
   你设的阈值                    人工确认         最后机会
  （默认48h）                 （不确认不动）    （随时可 reset）
```

- `python guardian.py test` 可以验证全部配置，**不会执行任何删除**
- `python guardian.py reset` 随时取消已触发的流程
- `python guardian.py status` 查看当前状态

## 支持的平台

| 平台 | 清理方式 | 需要什么 |
|------|---------|---------|
| Claude (claude.ai) | 浏览器自动化 | 邮箱+密码 |
| ChatGPT | 浏览器自动化 | 邮箱+密码 |
| DeepSeek | API | API Key |
| Gemini | 浏览器自动化 | Google账号 |
| Grok | 浏览器自动化 | X账号 |

## 快速开始

```bash
# 1. 安装依赖
pip install playwright cryptography
playwright install chromium

# 2. 配置
cp config.example.yaml config.yaml
# 编辑 config.yaml，填写你的信息

# 3. 加密存储密码
python guardian.py setup

# 4. 测试（不会真的删除）
python guardian.py test

# 5. 启动守护
python guardian.py start
```

## 配置说明

```yaml
# config.yaml
silence:
  check_method: telegram  # telegram / file_mtime / heartbeat_url
  threshold_hours: 48
  check_interval_minutes: 60

alert:
  email_to: your-friend@example.com
  email_from: your-email@gmail.com
  smtp_server: smtp.gmail.com
  smtp_port: 587

platforms:
  - name: claude
    enabled: true
    method: browser
    # 密码通过 setup 命令加密存储，不写在这里

  - name: chatgpt
    enabled: true
    method: browser

  - name: deepseek
    enabled: false
    method: api
```

## 安全说明

- 密码用本地密钥加密存储在 `credentials.enc`，不是明文
- config.yaml 里不存任何密码
- **绝对不要把 credentials.enc、config.yaml、guardian.key 推到 GitHub**
- `.gitignore` 已经排除了这些文件

## 所有命令

| 命令 | 说明 |
|------|------|
| `setup` | 交互式配置凭据（加密存储） |
| `test` | 测试配置和连接（不删除任何东西） |
| `start` | 执行一次检查（配合 cron/launchd 定时调用） |
| `status` | 查看当前状态 |
| `confirm` | 手动确认清理（模拟紧急联系人确认） |
| `reset` | 重置所有状态（取消告警/清理） |

## 系统要求

- Python 3.8+
- 支持 macOS / Windows / Linux

## 定时运行

Guardian 的 `start` 命令是单次检查，需要配合系统定时任务：

**Windows（任务计划程序）**:
1. 打开「任务计划程序」（搜索 Task Scheduler）
2. 创建基本任务 → 名称填 `Guardian`
3. 触发器 → 每天，重复间隔1小时
4. 操作 → 启动程序，程序填 `python`，参数填 `guardian.py start`，起始位置填 Guardian 文件夹路径
5. 完成

或者用命令行：
```powershell
schtasks /create /tn "Guardian" /tr "python C:\path\to\guardian\guardian.py start" /sc hourly /st 00:00
```

**macOS (launchd)**:
```bash
# 创建 ~/Library/LaunchAgents/com.guardian.check.plist
# 每小时检查一次，参考 config.yaml 里的 check_interval_minutes
```

**Linux (cron)**:
```bash
# 每小时检查一次
0 * * * * cd /path/to/guardian && python guardian.py start >> /var/log/guardian.log 2>&1
```

## 免责声明

详见 [DISCLAIMER.md](DISCLAIMER.md)。简单说：**用之前先 test，风险自担**。
