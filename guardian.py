#!/usr/bin/env python3
"""
Guardian — AI聊天记录自动清理工具
当你无法再亲自操作时，帮你清理各AI平台的聊天记录。
"""

import argparse
import json
import os
import smtplib
import sys
import time
from email.mime.text import MIMEText
from pathlib import Path

import yaml

from crypto_utils import decrypt_credentials, encrypt_credentials, generate_key

CONFIG_FILE = Path(__file__).parent / "config.yaml"
STATE_FILE = Path(__file__).parent / ".guardian-state.json"
KEY_FILE = Path(__file__).parent / "guardian.key"
CRED_FILE = Path(__file__).parent / "credentials.enc"


def load_config():
    if not CONFIG_FILE.exists():
        print("❌ 找不到 config.yaml")
        print("   请先复制 config.example.yaml 为 config.yaml 并填写配置")
        sys.exit(1)
    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f)


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "alerted": False,
            "confirmed": False,
            "cleaned": False,
            "last_check": 0,
        }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_last_activity(config):
    method = config["silence"]["check_method"]

    if method == "telegram":
        offset_file = os.path.expanduser(config["silence"]["telegram_offset_file"])
        try:
            return os.path.getmtime(offset_file)
        except FileNotFoundError:
            return 0

    elif method == "file_mtime":
        watch_file = os.path.expanduser(config["silence"]["watch_file"])
        try:
            return os.path.getmtime(watch_file)
        except FileNotFoundError:
            return 0

    elif method == "heartbeat_url":
        import urllib.request
        try:
            url = config["silence"]["heartbeat_url"]
            resp = urllib.request.urlopen(url, timeout=10)
            data = json.loads(resp.read())
            return data.get("last_active", 0)
        except Exception:
            return 0

    return 0


def send_alert_email(config, silence_hours):
    alert = config["alert"]
    creds = decrypt_credentials(KEY_FILE, CRED_FILE)
    smtp_password = creds.get("smtp_password", "")

    subject = alert.get(
        "subject", "自动通知：我可能出了状况"
    )
    default_body = (
        "你好，这是一封自动通知。\n\n"
        "我已经超过{hours}小时没有任何活动。请确认我是否安全。\n\n"
        "如果一切正常，请忽略这封邮件。\n"
        "如果我确实出了状况，请回复「确认」来启动数据清理流程。\n\n"
        "—— Guardian 自动通知系统"
    )
    body = alert.get("body", default_body).format(hours=int(silence_hours))

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = alert["email_from"]
    msg["To"] = alert["email_to"]

    with smtplib.SMTP(alert["smtp_server"], alert["smtp_port"]) as server:
        server.starttls()
        server.login(alert["email_from"], smtp_password)
        server.sendmail(alert["email_from"], [alert["email_to"]], msg.as_string())

    print(f"✅ 告警邮件已发送到 {alert['email_to']}")


def check_confirmation(config):
    """检查紧急联系人是否确认（简化版：检查 state 文件中的 confirmed 标志）"""
    # 实际部署时可以：
    # 1. IMAP 检查回复邮件
    # 2. 提供一个 webhook URL 让联系人点击确认
    # 这里用 manual confirm 命令作为 MVP
    state = load_state()
    return state.get("confirmed", False)


def run_cleanup(config):
    """执行平台清理"""
    creds = decrypt_credentials(KEY_FILE, CRED_FILE)
    results = {}

    for platform in config["platforms"]:
        if not platform.get("enabled"):
            continue

        name = platform["name"]
        method = platform["method"]
        print(f"\n🧹 正在清理 {name}...")

        try:
            if method == "api":
                from cleaners import api_cleaner
                result = api_cleaner.clean(name, platform, creds)
            elif method == "browser":
                from cleaners import browser_cleaner
                result = browser_cleaner.clean(name, platform, creds)
            else:
                result = {"status": "skip", "reason": f"未知清理方式: {method}"}

            results[name] = result
            status = result.get("status", "unknown")
            if status == "ok":
                print(f"   ✅ {name} 清理完成")
            else:
                print(f"   ⚠️  {name}: {result.get('reason', '未知错误')}")

        except Exception as e:
            results[name] = {"status": "error", "reason": str(e)}
            print(f"   ❌ {name} 清理失败: {e}")

    return results


# ── CLI Commands ──────────────────────────────────────────


def cmd_setup(args):
    """交互式配置：加密存储密码和密钥"""
    print("🔐 Guardian 凭据设置\n")

    if not KEY_FILE.exists():
        generate_key(KEY_FILE)
        print(f"✅ 加密密钥已生成: {KEY_FILE}")
    else:
        print(f"ℹ️  加密密钥已存在: {KEY_FILE}")

    config = load_config()
    creds = {}

    # SMTP 密码
    print("\n📧 邮箱 SMTP 密码（用于发送告警邮件）")
    smtp_pass = input(f"  {config['alert']['email_from']} 的密码/应用密码: ").strip()
    if smtp_pass:
        creds["smtp_password"] = smtp_pass

    # 各平台凭据
    for platform in config["platforms"]:
        if not platform.get("enabled"):
            continue

        name = platform["name"]
        method = platform["method"]
        print(f"\n🔑 {name} 凭据")

        if method == "api":
            key = input(f"  {name} API Key: ").strip()
            if key:
                creds[f"{name}_api_key"] = key
        elif method == "browser":
            email = input(f"  {name} 邮箱/用户名: ").strip()
            password = input(f"  {name} 密码: ").strip()
            if email:
                creds[f"{name}_email"] = email
            if password:
                creds[f"{name}_password"] = password

    encrypt_credentials(KEY_FILE, CRED_FILE, creds)
    print(f"\n✅ 凭据已加密存储到 {CRED_FILE}")
    print("⚠️  请妥善保管 guardian.key，丢失后需要重新配置")


def cmd_test(args):
    """测试模式：检查配置和连接，不执行清理"""
    print("🧪 Guardian 测试模式\n")

    config = load_config()
    print("✅ config.yaml 读取成功")

    if not KEY_FILE.exists() or not CRED_FILE.exists():
        print("❌ 未找到加密凭据，请先运行: python guardian.py setup")
        return

    creds = decrypt_credentials(KEY_FILE, CRED_FILE)
    print(f"✅ 凭据解密成功，共 {len(creds)} 项")

    # 检查静默检测
    last = get_last_activity(config)
    if last > 0:
        hours = (time.time() - last) / 3600
        print(f"✅ 静默检测正常，最后活动 {hours:.1f} 小时前")
    else:
        print("⚠️  无法获取最后活动时间（可能是首次运行）")

    # 检查 SMTP
    print("\n📧 测试邮件发送...")
    try:
        alert = config["alert"]
        smtp_password = creds.get("smtp_password", "")
        with smtplib.SMTP(alert["smtp_server"], alert["smtp_port"]) as server:
            server.starttls()
            server.login(alert["email_from"], smtp_password)
            print("✅ SMTP 登录成功")
    except Exception as e:
        print(f"❌ SMTP 连接失败: {e}")

    # 检查各平台
    for platform in config["platforms"]:
        if not platform.get("enabled"):
            continue
        name = platform["name"]
        has_cred = any(k.startswith(name) for k in creds)
        print(f"{'✅' if has_cred else '❌'} {name}: {'凭据已配置' if has_cred else '缺少凭据'}")

    print("\n🧪 测试完成（未执行任何清理操作）")


def cmd_start(args):
    """启动守护：单次检查（配合 cron/launchd 定时调用）"""
    config = load_config()
    state = load_state()
    now = time.time()

    # 已经清理过了
    if state.get("cleaned"):
        print("[guardian] 已完成清理，跳过。如需重置: python guardian.py reset")
        return

    # 检查静默
    last = get_last_activity(config)
    if last == 0:
        print("[guardian] 无法获取活动时间，跳过本次检查")
        state["last_check"] = now
        save_state(state)
        return

    silence_hours = (now - last) / 3600
    threshold = config["silence"]["threshold_hours"]
    print(
        f"[guardian] 静默 {silence_hours:.1f}h / 阈值 {threshold}h | "
        f"alerted={state.get('alerted')} confirmed={state.get('confirmed')}"
    )

    # 还没超时
    if silence_hours < threshold:
        state["last_check"] = now
        save_state(state)
        return

    # 超时了，还没告警 → 发邮件
    if not state.get("alerted"):
        print(f"[guardian] ⚠️  静默 {silence_hours:.1f}h，发送告警...")
        try:
            send_alert_email(config, silence_hours)
            state["alerted"] = True
            state["alert_time"] = now
        except Exception as e:
            print(f"[guardian] 告警发送失败: {e}")
        state["last_check"] = now
        save_state(state)
        return

    # 已告警，需要确认
    if config["alert"].get("require_confirmation", True):
        if not state.get("confirmed"):
            print("[guardian] 等待紧急联系人确认...")
            if check_confirmation(config):
                state["confirmed"] = True
                state["confirm_time"] = now
                print("[guardian] ✅ 确认收到")
            else:
                state["last_check"] = now
                save_state(state)
                return

        # 确认后有 grace period
        grace = config["alert"].get("grace_period_hours", 24)
        confirm_time = state.get("confirm_time", now)
        waited = (now - confirm_time) / 3600
        if waited < grace:
            print(f"[guardian] 反悔窗口: 还剩 {grace - waited:.1f}h")
            state["last_check"] = now
            save_state(state)
            return

    # 执行清理
    print("[guardian] 🧹 开始清理...")
    results = run_cleanup(config)
    state["cleaned"] = True
    state["clean_time"] = now
    state["results"] = results
    save_state(state)
    print("\n[guardian] ✅ 清理流程完成")


def cmd_confirm(args):
    """手动确认触发清理（模拟紧急联系人确认）"""
    state = load_state()
    if not state.get("alerted"):
        print("❌ 还没有发送过告警，无法确认")
        return
    state["confirmed"] = True
    state["confirm_time"] = time.time()
    save_state(state)
    print("✅ 已确认。清理将在 grace period 后执行。")


def cmd_reset(args):
    """重置状态（取消告警/清理标志）"""
    save_state({
        "alerted": False,
        "confirmed": False,
        "cleaned": False,
        "last_check": time.time(),
    })
    print("✅ 状态已重置")


def cmd_status(args):
    """查看当前状态"""
    config = load_config()
    state = load_state()

    last = get_last_activity(config)
    if last > 0:
        hours = (time.time() - last) / 3600
        print(f"📊 最后活动: {hours:.1f} 小时前")
    else:
        print("📊 最后活动: 未知")

    print(f"🔔 告警: {'已发送' if state.get('alerted') else '未触发'}")
    print(f"✅ 确认: {'已确认' if state.get('confirmed') else '未确认'}")
    print(f"🧹 清理: {'已完成' if state.get('cleaned') else '未执行'}")

    enabled = [p["name"] for p in config["platforms"] if p.get("enabled")]
    print(f"📋 启用平台: {', '.join(enabled) if enabled else '无'}")


def main():
    parser = argparse.ArgumentParser(
        description="Guardian — AI聊天记录自动清理工具"
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("setup", help="配置凭据（加密存储）")
    sub.add_parser("test", help="测试配置和连接")
    sub.add_parser("start", help="执行一次检查（配合 cron 使用）")
    sub.add_parser("confirm", help="手动确认清理（模拟紧急联系人）")
    sub.add_parser("reset", help="重置状态")
    sub.add_parser("status", help="查看当前状态")

    args = parser.parse_args()

    commands = {
        "setup": cmd_setup,
        "test": cmd_test,
        "start": cmd_start,
        "confirm": cmd_confirm,
        "reset": cmd_reset,
        "status": cmd_status,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
