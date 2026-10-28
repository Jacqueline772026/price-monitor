# Price Monitor / 竞品价格监控

每天自动检查手机/平板在波兰各渠道（Mi-Store、mi.com/pl、EURO、OleOle；Allegro 手动或 agent 辅助）的价格和库存，对照你的促销价表，结果写入 Excel（每天一个 sheet）。
Daily competitor price & stock check for Poland retail channels, compared against your promo-price table, logged to Excel (one sheet per day).

## 安装 / Setup
需要 Python 3.9+ 和 Google Chrome（或 Edge）。
- Mac: 双击 `setup.command`　·　Windows: 双击 `setup.bat`
- 把你的价格表放在项目根目录，命名 `price_table.xlsx`（表头见 `templates/price_table_template.xlsx`）。
- 复制 `config/links.example.json` 为 `config/links.json`，填入你自己的 EURO / OleOle / Allegro 链接（键 = `SKU|内存`）。
- 在 `app/config.py` 的 `MISTORE` / `MICOM` 里填你的型号对应关系（用 `app/tools/discover_*.py` 辅助）。

## 每日使用 / Daily
1. 关闭 Excel 里的 `price_log.xlsx`（若提示保存选"不保存"）。
2. 运行 `run_daily.command`（Mac）或 `run_daily.bat`（Windows）。脚本会自动打开专用 Chrome（独立 profile，不影响你的日常浏览器）。
3. 被网站拦截时稍后运行 `resume.*` 续跑。
4. 看 `check_report.txt`（问题清单）和 `price_log.xlsx`（今天的 sheet）。

## 单元格含义 / Cell values
`OK` · `OK: Blue | Black 789` · `789`（所有颜色同价）· `unavailable` · `unavailable: Colours` · `unavailable online` · `无链接` · `[未刷新]` · `[促销期外]`

## Allegro 与 AI agent
Allegro 官方 API 无法读取他人商品报价，因此用浏览器读取后导入：`python app/import_manual.py --channel Allegro --csv data/allegro_input.csv`。
任何 agent（Claude、Codex 等）按 `AGENTS.md` / `skills/price-monitor-operator/SKILL.md` 即可代你查价、比价、记录，并在增减机型时补链接。

## 文档
`docs/ARCHITECTURE.md` 架构 · `docs/TROUBLESHOOTING.md` 常见问题 · `python tests/run_tests.py` 离线自检

## 注意 / Notes
仅供对公开页面做低频、礼貌的价格核对；不绕过任何反爬或验证码，被拦截即停止。使用前请遵守各网站服务条款。
本项目不含任何真实价格数据。许可证（LICENSE）由仓库所有者自行选择。
