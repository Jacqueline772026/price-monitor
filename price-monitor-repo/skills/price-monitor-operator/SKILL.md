---
name: price-monitor-operator
description: 操作 price-monitor 项目：每日运行竞品价格检查、处理报错、增减机型并补全链接、用浏览器查 Allegro 并导入表格。Use when asked to run the daily price check, fix problems in check_report.txt, add/remove products, or fill Allegro prices.
---

# Price Monitor Operator

项目根目录 = 含 `app/run_all.py` 的文件夹。所有命令从根目录运行，Python 用 `.venv`（Mac: `.venv/bin/python`，Windows: `.venv\Scripts\python`）。

## 硬规则
- 不绕过验证码/反爬；遇到 captcha、Lockdown、被拦截 → 立即停止该网站，写进汇报，不要重试轰炸。
- 低频：浏览器查价每批 ≤5 个页面，页面之间停 8–14 秒。
- 运行前确认 `price_log.xlsx` 没在 Excel 里打开（存在 `~$price_log.xlsx` 就让用户关掉并选"不保存"）。
- 不修改 `price_table.xlsx`（用户每周手动更新）；不提交 `data/`、真实价格表、`config/links.json` 到 git。

## 1. 每日运行
1. `python app/check_setup.py` — 有配置缺项先走第 3 节。
2. `python app/run_all.py --mode daily`（被拦截后用 `--mode continue` 隔几小时续跑）。
3. 读 `check_report.txt`：0 问题则完成；否则按 `docs/TROUBLESHOOTING.md` 处理，必要时把 `debug_bundle.zip` 交给用户/开发者。
4. Allegro：见第 4 节。

## 2. 单元格含义
`OK` 全部颜色价格正确 · `OK: Blue | Black 789` 部分颜色价格不同 · `789` 所有颜色同价但不等于促销价 · `unavailable` 缺货 · `unavailable: Colours` 部分颜色缺货 · `unavailable online` 仅门店/无法配送 · `无链接` 没配链接（忽略）· `[未刷新]` 本次被拦截，沿用旧值 · `[促销期外]` 促销期外。

## 3. 增减机型 / 补链接
价格表每周更新后：
1. `python app/check_setup.py` 列出缺项（键 = `SKU|内存`，带保护壳的加 `|cover`）。
2. Mi-Store / mi.com：运行 `python app/tools/discover_mistore.py` / `python app/tools/discover_micom.py` 找到商品，把型号名→标识写进 `app/config.py` 的 `MISTORE` / `MICOM`。
3. EURO / OleOle / Allegro：用浏览器（或 WebSearch）在店内搜型号，确认是同一型号和内存后：
   `python app/tools/add_link.py SKU 内存 EURO <网址>`（渠道 EURO/OleOle/Allegro；保护壳加 `--cover`）。
4. 再跑 `check_setup.py` 直到无缺项；可用 `python app/tools/dump_url.py <网址>` 验证链接能被解析。
5. 下架的机型：从价格表删除即可，旧链接留在 links.json 无害。
找不到链接时不要猜：在汇报里列出"待用户确认"。

## 4. Allegro（手动/agent 辅助）
1. 取得待查列表：价格表里每行的 Allegro 链接（`config/links.json`）。
2. 用浏览器逐个打开，每批 ≤5 个；读取各颜色价格与是否可购买（灰色/"Powiadom"/已售罄 = unavailable）。遇验证码立即停止并告知用户。
3. 写 `data/allegro_input.csv`，表头 `sku,memory,color,price,status`（status 留空=有货；整款缺货写一行 color/price 空、status=unavailable；该渠道无此商品 status=no_offer）。
4. `python app/import_manual.py --channel Allegro --csv data/allegro_input.csv`（需今天的 sheet 已存在，即先跑过 mistore 步骤）。
5. 汇报：有多少行 OK、哪些行异常。

## 5. 汇报模板
今日日期 · 各渠道已完成/被拦截 · 异常行（型号、渠道、内容）· 缺链接清单 · 需要用户做的事。
