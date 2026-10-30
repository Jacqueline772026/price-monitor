# Architecture
- `app/run_all.py` 编排：mistore → (启动专用 Chrome) → micom → retail(EURO/OleOle) → check_report → maintenance。日志 `data/logs/`。
- 数据：`price_table.xlsx`(输入，只读) → `price_log.xlsx`(输出，每天一 sheet，新的在前) ；`data/history.csv` 明细；`data/raw/` 原始页面(7 天)。
- Mi-Store：HTTP 抓取类目页建立匹配，再读商品页 JSON-LD `availability` 判断库存。
- mi.com/pl：调用页面使用的 `productdetail` 接口（每个型号一次请求，含全部内存/颜色）。
- EURO/OleOle：Playwright 经 CDP 连接专用 Chrome，读取 JSON-LD 与页面数据（颜色变体、价差、配送可用性）。
- Allegro：agent/人工读取 → `import_manual.py` 同规则比价写入。
- `cell.py` 统一生成单元格文字；`check_setup.py` 对照价格表检查配置缺项；`maintenance.py` 清理历史防止文件堆积。
