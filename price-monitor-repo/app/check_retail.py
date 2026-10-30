"""EURO / OleOle 查价(通过你自己的专用 Chrome)。把结果写进 price_log.xlsx 里'今天'那张 sheet 的 EURO / Oleole 列。
前提: 1) 已双击 start_chrome.command  2) 已先运行过 check_mistore.py(生成今天的 sheet)
用法: python check_retail.py 表.xlsx [--rows 8-12] [--resume]\n      --rows 只跑指定行(小范围测试)；--resume 跳过今天已经读到结果的格子(失败的会重试)
价格/日期每次从 Excel 读取；链接来自 links.json(按 SKU+内存)。"""
import csv, datetime as dt, json, pathlib, random, re, sys, time
import openpyxl
from playwright.sync_api import sync_playwright
import paths, cell, hist, retail
from check_mistore import mem_key

APP = pathlib.Path(__file__).parent
OUT = APP.parent
TOL = 1.0     # 价格差小于 1 zł 视为一致(EURO 常见 xxx.99)
SITES = {"EURO": "https://www.euro.com.pl/", "OleOle": "https://www.oleole.pl/"}

class Blocked(Exception): pass

def tokens(s):
    s = re.split(r"\d+\s*/\s*\d+\s*(?:GB|TB)?", s or "", maxsplit=1)[0].lower().replace('"', " ").replace(",", ".")
    s = re.sub(r"\b(smartfon|tablet|xiaomi|lte|wifi|wi-fi|5g|4g|with|cover|etui)\b", " ", s)
    return re.findall(r"[a-z0-9.+]+", s)

def norm_model(s):
    return " ".join(tokens(s))

def same_model(page_name, sheet_name):
    """型号精确一致。页面名里的屏幕尺寸(11,2" 等)忽略，除非表里的型号名本身带这个数字(如 9.7)；
    平板要求 5G 一致；带保护套(+Etui / with cover)要一致。"""
    sheet = tokens(sheet_name)
    # 页面名里带英寸符号的数字(11" / 11,2" / 12,1")是屏幕尺寸，忽略；除非表里的型号名本身就含这个数字(如 9.7)
    strip_inch = lambda m: m.group(0) if m.group(1).replace(",", ".") in sheet else " "
    page = tokens(re.sub(r'(\d+(?:[.,]\d+)?)\s*"', strip_inch, page_name or ""))
    if page != sheet: return False
    f5 = lambda x: bool(re.search(r"\b5g\b", x or "", re.I))
    if ("pad" in sheet or sheet == ["redmi", "note", "17"] or sheet == ["redmi", "note", "17"]) and f5(page_name) != f5(sheet_name): return False
    cover = lambda x: bool(re.search(r"etui|cover", x or "", re.I))
    return cover(page_name) == cover(sheet_name)

def page_mem(name):
    m = re.search(r"(\d+)\s*/\s*(\d+)\s*(GB|TB)?", name or "", re.I)
    return mem_key(f"{m[1]}+{m[2]}{m[3] or 'GB'}") if m else None

def fetch(page, url):
    for attempt in (1, 2):                     # 超时(例如 Chrome 刚启动、网络慢)只重试一次，间隔 20 秒
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000); break
        except Exception as ex:
            if type(ex).__name__ != "TimeoutError" or attempt == 2: raise
            time.sleep(20)
    page.wait_for_timeout(3500)
    html = page.content()
    # 拦截页标题: EURO 是 "RTV Euro AGD - Lock" / "Blokada"，OleOle 是 Lockdown
    if "Access Denied" in html[:3000] or re.search(r"<title>[^<]*(lockdown|access denied|forbidden|\block\b|blokad)", html[:6000], re.I): raise Blocked(url)
    from urllib.parse import urlparse
    if urlparse(page.url).path in ("", "/") and urlparse(url).path not in ("", "/"): raise Blocked("被重定向回首页: " + url)   # 软拦截: 商品页被跳回首页
    lo, hi = 8.0, 14.0     # EURO 和 OleOle 都放慢到 8–14 秒/页，降低被拦截的概率
    time.sleep(random.uniform(lo, hi))
    return html

def check_row(page, site, url, name, mem, promo, log):
    html = fetch(page, url)
    if "search" in url:           # 表里给的是搜索页链接 -> 先在结果里找到对应商品
        items = retail.listing_items(html)
        cands = [u for n, u, _ in items if same_model(n, name) and page_mem(n) == mem_key(mem)]
        if not cands:
            if not items and len(html) < 30000: raise Blocked("搜索页只有很小的页面(疑似拦截页): " + url)
            return f"搜索结果里没有找到该型号/内存 [共{len(items)}个结果]"
        url = cands[0]; html = fetch(page, url)
    slug = url.split("?")[0].rsplit("/", 1)[-1].replace(".bhtml", "")
    info = retail.product_info(html)
    if not info:
        (OUT / "data" / "raw").mkdir(parents=True, exist_ok=True)
        (OUT / "data" / "raw" / f"fail_{site}_{slug[:50]}.html").write_text(html, encoding="utf-8", errors="ignore")
        t = re.search(r"<title>(.*?)</title>", html, re.S)
        return f"页面无价格数据 [{(t.group(1).strip() if t else '无标题')[:40]} | {len(html) // 1000}KB]"
    def verify(inf):
        return same_model(inf["name"], name) and page_mem(inf["name"]) == mem_key(mem)
    if not verify(info):
        return f"链接商品与表不符: 页面是《{info['name'][:55]}》"
    cur_color = re.sub(r"\s*\+.*$", "", info["name"]).split()[-1]
    group = retail.color_group(html, slug) or [(cur_color, slug, None)]
    origin = SITES[site]
    cat = re.search(r"https?://[^/]+/([^/]+)/", url).group(1)
    res = []
    for color, link, grp in group:
        if link == slug: inf, c, hh = info, color, html
        else:
            hh = fetch(page, f"{origin}{grp or cat}/{link}.bhtml")
            inf = retail.product_info(hh); c = color
            if not inf: res.append((c, None, "无价格数据")); continue
            if not verify(inf): res.append((c, None, "型号/内存不符")); continue
        price = float(inf["price"]) if inf["price"] is not None else None
        res.append((c, price, retail.delivery_status(hh, inf.get("availability", ""), link)))
    log.extend([site, name, mem, retail.color_en(c), p, promo, a] for c, p, a in res)
    STAT = ("unavailable", "unavailable online")
    live = [(c, p, a) for c, p, a in res if a not in STAT]
    bad = [f"{retail.color_en(c)} " + ("无价格" if p is None else format(p, "g")) for c, p, a in live if p is None or abs(p - float(promo)) >= TOL]
    unk = [retail.color_en(c) for c, p, a in live if a == "unknown"]
    if not live:
        kinds = sorted({a for _, _, a in res})
        return kinds[0] if len(kinds) == 1 else "; ".join(f"{k}: " + ", ".join(retail.color_en(c) for c, _, a in res if a == k) for k in kinds)
    okc = [retail.color_en(c) for c, p, a in live if p is not None and abs(p - float(promo)) < TOL]
    return cell.build(okc, bad, [(k, [retail.color_en(c) for c, _, a in res if a == k]) for k in ("unavailable online", "unavailable")], unk)

def main(xlsx, rows_arg=None, resume=False):
    if (OUT / "~$price_log.xlsx").exists(): sys.exit("price_log.xlsx 正在被 Excel 打开。请先关闭 Excel(提示保存时选\"不保存\")，再重新运行。")
    links = json.load(open(paths.links_file(), encoding="utf-8"))
    wb_in = openpyxl.load_workbook(xlsx, data_only=True); ws_in = wb_in.worksheets[0]
    hdr = {str(c.value).split("\n")[0].strip().lower(): c.column for c in ws_in[1] if c.value}
    today = dt.date.today(); master_p = OUT / "price_log.xlsx"
    master = openpyxl.load_workbook(master_p)
    if today.isoformat() not in master.sheetnames: sys.exit("请先运行 check_mistore.py 生成今天的 sheet")
    ws = master[today.isoformat()]
    cols = {"EURO": hdr["euro"], "OleOle": hdr["oleole"]}
    lo, hi = (map(int, rows_arg.split("-")) if rows_arg else (2, ws_in.max_row))
    log = []; streak = {s: 0 for s in SITES}; stopped = set(); FAIL = ("页面无价格数据", "读取失败", "被网站拦截", "链接商品与表不符", "搜索结果里没有找到")
    with sync_playwright() as p:
        try:
            ctx = p.chromium.connect_over_cdp("http://localhost:9222").contexts[0]; page = ctx.new_page()
        except Exception: sys.exit("连不上专用 Chrome。请先双击「打开专用Chrome.command」打开它(不要关)，再运行。")
        try:
            for r in range(max(lo, 2), hi + 1):
                sku, mem, name, promo = (ws_in.cell(r, hdr[k]).value for k in ("sku", "memory", "product name", "rrp after promotion"))
                if not (sku and mem and name and promo): continue
                s, e = ws_in.cell(r, hdr["offer start date"]).value, ws_in.cell(r, hdr["offer end date"]).value
                s = s.date() if isinstance(s, dt.datetime) else s; e = e.date() if isinstance(e, dt.datetime) else e
                out_of = isinstance(s, dt.date) and isinstance(e, dt.date) and not (s <= today <= e)
                for site in SITES:
                    cur = ws.cell(r, cols[site]).value
                    if resume and cur and not str(cur).endswith("[未刷新]") and "无价格" not in str(cur) and not str(cur).lstrip("[促销期外] ").startswith(FAIL):
                        print(f"行{r} {site:6} 已有结果，跳过"); continue
                    url = links.get(f"{sku}|{mem}" + ("|cover" if "cover" in str(name).lower() else ""), {}).get(site)
                    if not url: txt = "无链接"
                    elif site in stopped:
                        print(f"行{r} {site:6} 本站已被拦截，今天不再访问"); txt = "被网站拦截"
                    else:
                        try:
                            txt = check_row(page, site, url, str(name).strip(), mem, promo, log) if url else "无链接"
                        except Blocked: txt = "被网站拦截"
                        except Exception as ex:
                            if type(ex).__name__ == "TargetClosedError" or "has been closed" in str(ex): master.save(master_p); sys.exit("专用 Chrome 被关闭或崩溃了，已停止。请双击「打开专用Chrome.command」重新打开它(不要关)，然后双击「继续运行.command」。")
                            txt = f"读取失败({type(ex).__name__}: {str(ex)[:50]})"
                        streak[site] = streak[site] + 1 if txt == "被网站拦截" else 0
                        if streak[site] >= 2 and site not in stopped:
                            stopped.add(site); print(f"!! {site} 连续 2 次被拦截，今天不再访问 {site}，请明天再试。")
                    # 这次没读到、但格子里本来有好结果 -> 保留旧结果并标注未刷新，不要用失败信息覆盖
                    if txt.startswith(FAIL) and cur and not str(cur).lstrip("[促销期外] ").startswith(FAIL):
                        txt = str(cur).replace(" [未刷新]", "") + " [未刷新]"
                    ws.cell(r, cols[site]).value = ("[促销期外] " if out_of and txt != "无链接" and not txt.startswith("[促销期外]") and "[促销期外]" not in txt else "") + txt
                    print(f"行{r} {site:6} {name} {mem}: {txt}")
                master.save(master_p)      # 每行存一次，中途中断也不丢
                if len(stopped) == len(SITES):
                    print("\n所有站点今天都被拦截，已自动停止，已读到的结果已保存。请明天再试。"); break
        finally:
            page.close()
    hist.append_rows(OUT / "data" / "history.csv", [[today.isoformat(), *x] for x in log])
    print(f"完成，已写入 price_log.xlsx [{today.isoformat()}]")

if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[a.index("--rows") + 1] if "--rows" in a else None, "--resume" in a)
