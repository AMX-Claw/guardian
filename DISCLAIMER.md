# ⚠️ 免责声明 / Disclaimer

## 中文

Guardian 是一个开源工具，用于在用户无法亲自操作时自动清理AI平台聊天记录。

**使用本工具即表示你理解并同意以下条款：**

1. **风险自担**：本工具涉及不可逆的数据删除操作。一旦执行清理，被删除的聊天记录**无法恢复**。
2. **误触发风险**：虽然本工具设计了多重安全机制（紧急联系人确认、反悔窗口），但**不排除因配置错误、网络异常、平台变更等原因导致误触发的可能**。
3. **平台兼容性**：各AI平台的界面和API随时可能更新。本工具的浏览器自动化清理方式可能因平台UI变更而失效或产生预期外行为。
4. **凭据安全**：虽然密码经过本地加密存储，但你有责任保管好加密密钥文件（guardian.key）。**密钥泄露等于密码泄露**。
5. **无担保**：本工具按"原样"提供，不提供任何明示或暗示的担保。开发者不对因使用本工具造成的任何数据丢失、账号异常或其他损失负责。

**强烈建议：**
- 首次使用前务必运行 `python guardian.py test` 验证配置
- 设置合理的静默阈值（建议不低于48小时）
- 启用紧急联系人确认机制
- 保留足够的反悔窗口时间（建议24小时以上）
- 选择你**完全信任**的人作为紧急联系人

## English

Guardian is an open-source tool for automatically cleaning AI platform chat histories when the user is no longer able to do so.

**By using this tool, you acknowledge and agree to the following:**

1. **Use at your own risk.** This tool performs irreversible data deletion. Deleted chat histories **cannot be recovered**.
2. **False trigger risk.** While multiple safety mechanisms are in place (emergency contact confirmation, grace period), **misconfiguration, network issues, or platform changes may cause unintended triggers**.
3. **Platform compatibility.** AI platforms may update their interfaces at any time. Browser automation may break or behave unexpectedly after UI changes.
4. **Credential security.** Passwords are encrypted locally, but you are responsible for safeguarding the encryption key file (guardian.key). **A leaked key means leaked passwords.**
5. **No warranty.** This tool is provided "as-is" without warranty of any kind. The developers are not liable for any data loss, account issues, or other damages.
