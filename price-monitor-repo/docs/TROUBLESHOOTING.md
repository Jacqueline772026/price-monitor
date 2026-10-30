# Troubleshooting / 常见问题
- **结果被覆盖/消失**：Excel 里还开着旧的 price_log.xlsx，关闭时保存会覆盖脚本结果。运行前后都关闭并选"不保存"。脚本检测到 `~$price_log.xlsx` 会拒绝运行。
- **连接不上 Chrome (9222)**：专用 Chrome 被关了。运行 `start_chrome.*` 后用 `resume.*` 续跑；运行期间不要关闭它。
- **OleOle 被拦截（Lockdown 页面/跳回首页）**：一天加载约 50 页后常见。脚本已放慢并在连续 2 次拦截后停止该站，未刷新的格子标 `[未刷新]` 沿用旧值；过几小时 `resume.*` 续跑。不要绕过。
- **Mi-Store 全显示可购买**：类目页永远显示"Kup Teraz"，库存必须看商品页（已实现）。
- **EURO/OleOle 价格有小数**：颜色/规格有加价（base + difference），属正常。
- **mi.com 变灰**：视为 unavailable。
- **Allegro API**：官方 API 只能读自己账号的 offer，读不到竞品报价；用浏览器 + `import_manual.py`。
- **Windows**：使用 `.bat`；若 `py` 找不到，安装 Python 并勾选 "Add to PATH"。路径含中文无碍（已 UTF-8）。
- 仍无法解决：把 `debug_bundle.zip`（已自动生成，不含个人信息）发给维护者。
- **EURO 显示"无价格 / 页面无价格数据 / 搜索结果没有找到[共0个结果]"**：多半是被拦截(页面标题 "RTV Euro AGD - Lock" 或 "Blokada")，不是没货。v2 起会识别并自动停站、标 `[未刷新]`；稍后用 `resume.*` 补跑。
- **一开始整批读取超时**：专用 Chrome 刚启动，或系统正弹出密码/授权窗口等你输入。输入完后用 `resume.*` 续跑；v2 已在新启动的 Chrome 后多等 30 秒并自动重试一次。
- **某颜色缺货但有价格**：以页面的可购买状态为准，缺货的颜色单独列在 `unavailable:` 后面。

