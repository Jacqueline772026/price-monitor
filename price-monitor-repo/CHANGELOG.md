# Changelog
## v2 (2026-10-30)
- EURO 拦截页(标题 "Lock"/"Blokada")现在能被识别；之前被误写成"无价格 / 页面无价格数据 / 搜索结果没有找到"。
- EURO 与 OleOle 页面间隔统一放慢到 8–14 秒；读取超时自动重试一次（间隔 20 秒）；mi.com 首页超时 90 秒并重试。
- 专用 Chrome 刚启动后多等 30 秒再开始，避免首批页面超时。
- 续跑(resume)会重新读取含"无价格"的格子。
- 新增 `import_manual.py`（Allegro 等手动/agent 渠道导入）、`check_setup.py`（配置体检）、`tools/add_link.py`（补链接）、AGENTS.md 与 agent skill、Windows/Mac 启动脚本、离线测试。
## v1 (2026-10-28)
- 首个可上传版本：跨平台路径、`run_all.py` 一键入口、清理与自检。
