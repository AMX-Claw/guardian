"""浏览器自动化清理 — Playwright驱动登录+删除聊天"""

import time


def clean(name, platform, creds):
    cleaners = {
        "claude": clean_claude,
        "chatgpt": clean_chatgpt,
        "gemini": clean_gemini,
        "grok": clean_grok,
    }
    fn = cleaners.get(name)
    if not fn:
        return {"status": "skip", "reason": f"不支持的浏览器平台: {name}"}
    return fn(platform, creds)


def _launch_browser():
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    )
    return pw, browser, ctx


def clean_claude(platform, creds):
    """Claude: 登录 → Settings → Delete All Conversations"""
    email = creds.get("claude_email")
    password = creds.get("claude_password")
    if not email or not password:
        return {"status": "error", "reason": "缺少 Claude 登录凭据"}

    pw, browser, ctx = _launch_browser()
    try:
        page = ctx.new_page()
        page.goto("https://claude.ai/login", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # 邮箱登录
        email_input = page.locator('input[type="email"]')
        if email_input.count() > 0:
            email_input.fill(email)
            page.locator('button:has-text("Continue"), button:has-text("继续")').click()
            time.sleep(2)

        # 密码
        pw_input = page.locator('input[type="password"]')
        if pw_input.count() > 0:
            pw_input.fill(password)
            page.locator('button:has-text("Continue"), button:has-text("Sign in"), button:has-text("登录")').click()
            time.sleep(5)

        # 进入设置
        page.goto("https://claude.ai/settings", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # 找到"删除所有对话"按钮
        delete_btn = page.locator('button:has-text("Delete All"), button:has-text("删除所有")')
        if delete_btn.count() > 0:
            delete_btn.click()
            time.sleep(1)
            # 确认弹窗
            confirm = page.locator('button:has-text("Delete"), button:has-text("确认"), button:has-text("确定")')
            if confirm.count() > 0:
                confirm.click()
                time.sleep(3)
            return {"status": "ok"}
        else:
            return {"status": "error", "reason": "找不到删除按钮，页面结构可能已变"}

    except Exception as e:
        return {"status": "error", "reason": str(e)}
    finally:
        browser.close()
        pw.stop()


def clean_chatgpt(platform, creds):
    """ChatGPT: 登录 → Settings → Delete all chats"""
    email = creds.get("chatgpt_email")
    password = creds.get("chatgpt_password")
    if not email or not password:
        return {"status": "error", "reason": "缺少 ChatGPT 登录凭据"}

    pw, browser, ctx = _launch_browser()
    try:
        page = ctx.new_page()
        page.goto("https://chatgpt.com/auth/login", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # Log in 按钮
        login_btn = page.locator('button:has-text("Log in")')
        if login_btn.count() > 0:
            login_btn.click()
            time.sleep(2)

        # 邮箱
        email_input = page.locator('input[name="email"], input[type="email"]')
        if email_input.count() > 0:
            email_input.fill(email)
            page.locator('button:has-text("Continue")').click()
            time.sleep(2)

        # 密码
        pw_input = page.locator('input[type="password"]')
        if pw_input.count() > 0:
            pw_input.fill(password)
            page.locator('button:has-text("Continue")').click()
            time.sleep(5)

        # 进入设置
        page.goto("https://chatgpt.com/#settings", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # 找到 Data Controls → Delete all chats
        data_ctrl = page.locator('text=Data controls, text=数据控制')
        if data_ctrl.count() > 0:
            data_ctrl.click()
            time.sleep(1)

        delete_btn = page.locator('button:has-text("Delete all chats"), button:has-text("删除所有聊天")')
        if delete_btn.count() > 0:
            delete_btn.click()
            time.sleep(1)
            confirm = page.locator('button:has-text("Confirm"), button:has-text("确认")')
            if confirm.count() > 0:
                confirm.click()
                time.sleep(3)
            return {"status": "ok"}
        else:
            return {"status": "error", "reason": "找不到删除按钮，页面结构可能已变"}

    except Exception as e:
        return {"status": "error", "reason": str(e)}
    finally:
        browser.close()
        pw.stop()


def clean_gemini(platform, creds):
    """Gemini: Google账号登录 → 删除活动"""
    email = creds.get("gemini_email")
    password = creds.get("gemini_password")
    if not email or not password:
        return {"status": "error", "reason": "缺少 Google 登录凭据"}

    pw, browser, ctx = _launch_browser()
    try:
        page = ctx.new_page()
        page.goto("https://gemini.google.com", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # Google 登录流程
        signin = page.locator('a:has-text("Sign in"), a:has-text("登录")')
        if signin.count() > 0:
            signin.click()
            time.sleep(2)

        email_input = page.locator('input[type="email"]')
        if email_input.count() > 0:
            email_input.fill(email)
            page.locator('#identifierNext, button:has-text("Next"), button:has-text("下一步")').click()
            time.sleep(3)

        pw_input = page.locator('input[type="password"]')
        if pw_input.count() > 0:
            pw_input.fill(password)
            page.locator('#passwordNext, button:has-text("Next"), button:has-text("下一步")').click()
            time.sleep(5)

        # Gemini Activity 页面删除
        page.goto(
            "https://myactivity.google.com/product/gemini?utm_source=gemini",
            wait_until="networkidle",
            timeout=30000,
        )
        time.sleep(2)

        delete_btn = page.locator('button:has-text("Delete"), button:has-text("删除")')
        if delete_btn.count() > 0:
            delete_btn.first.click()
            time.sleep(1)
            all_time = page.locator('text=All time, text=所有时间')
            if all_time.count() > 0:
                all_time.click()
                time.sleep(1)
            confirm = page.locator('button:has-text("Delete"), button:has-text("删除")')
            if confirm.count() > 0:
                confirm.last.click()
                time.sleep(3)
            return {"status": "ok"}
        else:
            return {"status": "error", "reason": "找不到删除按钮"}

    except Exception as e:
        return {"status": "error", "reason": str(e)}
    finally:
        browser.close()
        pw.stop()


def clean_grok(platform, creds):
    """Grok: X账号登录 → 删除对话"""
    email = creds.get("grok_email")
    password = creds.get("grok_password")
    if not email or not password:
        return {"status": "error", "reason": "缺少 X/Grok 登录凭据"}

    pw, browser, ctx = _launch_browser()
    try:
        page = ctx.new_page()
        page.goto("https://grok.x.ai", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # X 登录
        signin = page.locator('a:has-text("Sign in"), button:has-text("Sign in")')
        if signin.count() > 0:
            signin.click()
            time.sleep(2)

        email_input = page.locator('input[autocomplete="username"], input[name="text"]')
        if email_input.count() > 0:
            email_input.fill(email)
            page.locator('button:has-text("Next"), button:has-text("下一步")').click()
            time.sleep(2)

        pw_input = page.locator('input[type="password"]')
        if pw_input.count() > 0:
            pw_input.fill(password)
            page.locator('button:has-text("Log in"), button:has-text("登录")').click()
            time.sleep(5)

        # Grok 设置 → 删除对话
        # grok.x.ai 的 UI 可能会变，这里尝试常见路径
        page.goto("https://grok.x.ai", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # 侧边栏对话列表：逐个删除
        conversations = page.locator('[data-testid="conversation-item"], .conversation-item')
        count = conversations.count()
        deleted = 0

        if count == 0:
            # 尝试菜单方式
            menu = page.locator('button[aria-label="Menu"], button[aria-label="菜单"]')
            if menu.count() > 0:
                menu.click()
                time.sleep(1)
                clear = page.locator('text=Clear conversations, text=清除对话')
                if clear.count() > 0:
                    clear.click()
                    time.sleep(1)
                    confirm = page.locator('button:has-text("Confirm"), button:has-text("确认")')
                    if confirm.count() > 0:
                        confirm.click()
                        time.sleep(2)
                    return {"status": "ok"}

        for i in range(count):
            try:
                conv = conversations.nth(0)
                conv.click(button="right")
                time.sleep(0.5)
                delete = page.locator('text=Delete, text=删除')
                if delete.count() > 0:
                    delete.click()
                    time.sleep(0.5)
                    confirm = page.locator('button:has-text("Delete"), button:has-text("确认")')
                    if confirm.count() > 0:
                        confirm.click()
                        time.sleep(1)
                    deleted += 1
            except Exception:
                break

        return {"status": "ok", "deleted": deleted}

    except Exception as e:
        return {"status": "error", "reason": str(e)}
    finally:
        browser.close()
        pw.stop()
