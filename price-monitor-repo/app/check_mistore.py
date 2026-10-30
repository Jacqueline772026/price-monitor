"""读 Excel -> 抓 Mi-Store -> 对比 'RRP after Promotion' -> 填 GG 列 -> 另存 结果_日期.xlsx
用法: python check_mistore.py 表.xlsx            (联网抓取)
      python check_mistore.py 表.xlsx --offline  (用 raw/ 里已保存的页面，测试用)
价格、日期每次都从 Excel 读取，脚本里没有任何写死的价格。"""
import copy, csv, datetime as dt, pathlib, re, sys, time
import openpyxl, requests
import cell, config, hist, mistore

APP = pathlib.Path(__file__).parent
OUT = APP.parent
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
           "Accept-Language": "pl-PL,pl;q=0.9"}
ITEM = re.compile(r"^(?:(?:Smartfon|Tablet) )?(?P<model>.+?) (?P<mem>\d+\+\d+(?:GB|TB)?) (?P<color>.+)$")

def mem_key(s):
    """'12+1T' / '12+1024GB' / '4+128' -> (12, 1024)，统一后精确比较"""
    m = re.fullmatch(r"\s*(\d+)\s*\+\s*(\d+)\s*(GB|TB|T|G)?\s*", str(s or ""), re.I)
    if not m: return None
    ram, rom, u = int(m[1]), int(m[2]), (m[3] or "GB").upper()
    return ram, rom * 1024 if u in ("T", "TB") else rom

def load_page(page, offline):
    if offline:
        f = OUT / "data" / "raw" / ("MS_" + page)
        return f.read_text(encoding="utf-8", errors="ignore") if f.exists() else None
    r = requests.get(config.BASE + page, headers=HEADERS, timeout=25)
    (OUT / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (OUT / "data" / "raw" / ("MS_" + page)).write_text(r.text, encoding="utf-8", errors="ignore")
    time.sleep(1.5)
    return r.text if r.status_code == 200 else None

STOCK, COUNT = {}, {"available": 0, "unavailable": 0, "unknown": 0, "读取失败": 0}

def stock(url, offline):
    """读商品详情页判断库存；同一个商品只读一次。"""
    if not url: return None
    if url in STOCK: return STOCK[url]
    pid = re.search(r"product-\w+-(\d+)", url); f = OUT / "data" / "raw" / f"MS_prod_{pid.group(1) if pid else abs(hash(url))}.html"
    html = None
    if offline: html = f.read_text(encoding="utf-8", errors="ignore") if f.exists() else None
    else:
        try:
            r = requests.get(url, headers=HEADERS, timeout=25)
            if r.status_code == 200: html = r.text; f.parent.mkdir(parents=True, exist_ok=True); f.write_text(html, encoding="utf-8", errors="ignore")
        except Exception: html = None
        time.sleep(1.2)
    STOCK[url] = mistore.stock_status(html) if html else None
    COUNT[STOCK[url][0] if STOCK[url] else "读取失败"] += 1
    return STOCK[url]

def refine(matched, urls, offline):
    out = []
    for (c, p, st, t), u in zip(matched, urls):
        res = stock(u, offline)
        if res is None: st, t = "unknown", "详情页读取失败"
        else: st, t = res[0], res[1]
        out.append((c, p, st, t))
    return out

def fmt(p): return f"{p:g}"

def save_daily_sheet(wb_in, ws_in, out_path, sheet_name):
    """把填好结果的表复制成 price_log.xlsx 里的一个新 sheet(名字=日期)；同一天重跑会覆盖当天那一张。"""
    master = openpyxl.load_workbook(out_path) if out_path.exists() else openpyxl.Workbook()
    if "Sheet" in master.sheetnames and len(master.sheetnames) == 1 and master["Sheet"].max_row == 1 and master["Sheet"]["A1"].value is None:
        del master["Sheet"]
    keep = {}      # 同一天重跑时，保留已有的 EURO / Oleole 两列结果(它们由 check_retail.py 写入)
    if sheet_name in master.sheetnames:
        old_ws = master[sheet_name]
        for c in old_ws[1]:
            if c.value and str(c.value).split("\n")[0].strip().lower() in ("euro", "oleole"):
                for r in range(2, old_ws.max_row + 1):
                    if old_ws.cell(r, c.column).value not in (None, ""): keep[(r, c.column)] = old_ws.cell(r, c.column).value
        del master[sheet_name]
    ws = master.create_sheet(sheet_name, 0)           # 最新的放最前面
    for row in ws_in.iter_rows():
        for c in row:
            n = ws.cell(c.row, c.column, c.value)
            if c.has_style:
                n.font, n.fill, n.border = copy.copy(c.font), copy.copy(c.fill), copy.copy(c.border)
                n.alignment, n.number_format = copy.copy(c.alignment), c.number_format
    for k, d in ws_in.column_dimensions.items(): ws.column_dimensions[k].width = d.width
    for k, d in ws_in.row_dimensions.items(): ws.row_dimensions[k].height = d.height
    for (r, c), v in keep.items():
        if ws.cell(r, c).value in (None, ""): ws.cell(r, c).value = v
    ws.freeze_panes = ws_in.freeze_panes
    master.save(out_path)

def main(xlsx, offline=False):
    if (OUT / "~$price_log.xlsx").exists(): sys.exit("price_log.xlsx 正在被 Excel 打开。请先关闭 Excel(提示保存时选\"不保存\")，再重新运行。")
    wb = openpyxl.load_workbook(xlsx); ws = wb.worksheets[0]
    hdr = {str(c.value).split("\n")[0].strip().lower(): c.column for c in ws[1] if c.value}
    col = lambda name: hdr[name.lower()]
    gg = next(c for k, c in hdr.items() if k.startswith("gg"))
    today = dt.date.today()
    pages, log = {}, []
    for row in range(2, ws.max_row + 1):
        name = ws.cell(row, col("product name")).value
        mem = ws.cell(row, col("memory")).value
        promo = ws.cell(row, col("rrp after promotion")).value
        if not (name and mem and promo): continue
        name = str(name).strip()
        cfg = config.MISTORE.get(name)
        if not cfg:
            ws.cell(row, gg).value = "未配置(型号未确认)"; continue
        if cfg["page"] not in pages:
            html = load_page(cfg["page"], offline)
            pages[cfg["page"]] = mistore.parse_category(html) if html else None
        items = pages[cfg["page"]]
        if items is None:
            ws.cell(row, gg).value = "抓取失败"; continue
        want = mem_key(mem); matched = []; murls = []
        for it in items:
            m = ITEM.match(it["name"] or "")
            models = [cfg["model"]] if isinstance(cfg["model"], str) else list(cfg["model"])
            if m and m["model"] in models and mem_key(m["mem"]) == want and "+" not in m["color"]:  # 排除 +键盘/+保护套 套装
                color_txt = m["color"] if m["model"] == models[0] else f'{m["color"]} ({m["model"][len(models[0]):].strip()})'
                matched.append((color_txt, it["price"], it.get("status", "available"), it.get("status_text", ""))); murls.append(it.get("url"))
        if not matched:
            ws.cell(row, gg).value = "未找到该内存版本"; continue
        matched = refine(matched, murls, offline)
        live = [x for x in matched if x[2] != "unavailable"]
        diff = [f"{c} {fmt(p)}" for c, p, st, _ in live if abs(p - float(promo)) > 0.005]
        unav = [c for c, p, st, _ in matched if st == "unavailable"]
        unk = [f"{c}({t[:20]})" for c, p, st, t in matched if st == "unknown"]
        okc = [c for c, p, st, _ in live if abs(p - float(promo)) <= 0.005]
        txt = "unavailable" if not live else cell.build(okc, diff, [("unavailable", unav)], unk)
        if not live and unk: txt = cell.build([], [], [], unk)
        s, e = ws.cell(row, col("offer start date")).value, ws.cell(row, col("offer end date")).value
        s = s.date() if isinstance(s, dt.datetime) else s; e = e.date() if isinstance(e, dt.datetime) else e
        if isinstance(s, dt.date) and isinstance(e, dt.date) and not (s <= today <= e):
            txt = "[促销期外] " + txt
        ws.cell(row, gg).value = txt
        for c, p, st, _ in matched:
            log.append([today.isoformat(), "Mi-Store", name, mem, c, p, promo, st])
    out = OUT / "price_log.xlsx"
    save_daily_sheet(wb, ws, out, today.isoformat())
    hist.append_rows(OUT / "data" / "history.csv", log)
    n = sum(COUNT.values())
    print(f"商品详情页库存核对 {n} 个: 有货 {COUNT['available']}，缺货 {COUNT['unavailable']}，状态不明 {COUNT['unknown']}，读取失败 {COUNT['读取失败']}")
    if n >= 10 and COUNT["unavailable"] / n > 0.6: print("⚠ 缺货比例异常高，可能是详情页判断规则误判，请把 data/raw/MS_prod_*.html 里任意两个交给维护者或 agent")
    if n >= 10 and (COUNT["unknown"] + COUNT["读取失败"]) / n > 0.3: print("⚠ 大量商品库存状态不明，请把 data/raw/MS_prod_*.html 里任意两个交给维护者或 agent")
    print(f"完成 -> {out.name} 的 [{today.isoformat()}] 工作表，历史记录 {len(log)} 条 -> history.csv")
    for row in range(2, ws.max_row + 1):
        v = ws.cell(row, gg).value
        if v: print(f"  行{row} {ws.cell(row, col('product name')).value} {ws.cell(row, col('memory')).value}: {v}")

if __name__ == "__main__":
    main(sys.argv[1], "--offline" in sys.argv)
