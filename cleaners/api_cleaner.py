"""API方式清理 — DeepSeek等支持API删除的平台"""

import json
import urllib.request


def clean(name, platform, creds):
    if name == "deepseek":
        return clean_deepseek(platform, creds)
    return {"status": "skip", "reason": f"不支持的API平台: {name}"}


def clean_deepseek(platform, creds):
    """DeepSeek: 用API删除所有对话"""
    api_key = creds.get("deepseek_api_key")
    if not api_key:
        return {"status": "error", "reason": "缺少 API Key"}

    base = platform.get("api_base", "https://api.deepseek.com")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 获取对话列表
    try:
        req = urllib.request.Request(
            f"{base}/v1/chat/conversations",
            headers=headers,
        )
        resp = urllib.request.urlopen(req, timeout=30)
        conversations = json.loads(resp.read()).get("data", [])
    except Exception as e:
        return {"status": "error", "reason": f"获取对话列表失败: {e}"}

    if not conversations:
        return {"status": "ok", "deleted": 0, "reason": "没有对话需要清理"}

    deleted = 0
    errors = []
    for conv in conversations:
        conv_id = conv.get("id")
        if not conv_id:
            continue
        try:
            req = urllib.request.Request(
                f"{base}/v1/chat/conversations/{conv_id}",
                headers=headers,
                method="DELETE",
            )
            urllib.request.urlopen(req, timeout=30)
            deleted += 1
        except Exception as e:
            errors.append(f"{conv_id}: {e}")

    result = {"status": "ok", "deleted": deleted}
    if errors:
        result["errors"] = errors
        result["status"] = "partial"
    return result
