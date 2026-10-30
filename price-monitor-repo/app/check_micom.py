"""mi.com/pl 查价: 通过专用 Chrome 读取商品详情数据接口(一个型号只请求一次，含全部内存/颜色)。结果写进 price_log.xlsx 今天那张 sheet 的 micom 列。
用法: python app/check_micom.py 表.xlsx [--resume]     前提: 已运行过 check_mistore(生成今天的 sheet)，专用 Chrome 已开。"""
import datetime as dt, pathlib, random, re, sys, time
import openpyxl
from playwright.sync_api import sync_playwright
import cell, config, hist, micom
from check_mistore import mem_key
APP = pathlib.Path(__file__).parent; OUT = APP.parent
API = "https://ams-go.buy.mi.com/pl/v2/item/productdetail?from=pc&tag={}"
FAIL = ("读取失败", "被网站拦截")

class Blocked(Exception): pass

def fetch(page, slug):
    st, body = page.evaluate("""async u => { try { const r = await fetch(u, {credentials: 'include'}); return [r.status, await r.text()]; } catch (e) { return [0, String(e)]; } }""", API.format(slug))
    if st in (403, 429): raise Blocked(slug)
    if st == 200: return body
    try:   # 备用: 打开购买页，截取页面自己发出的数据请求
        with page.expect_response(lambda x: "productdetail" in x.url and slug in x.url, timeout=20000) as ri:
            page.goto(f"https://www.mi.com/pl/product/{slug}/buy/", wait_until="domcontentloaded", timeout=45000)
        return ri.value.text()
    except Exception: return None

def resolve(page, name, ref):
    """ref 以 search: 开头 -> 打开搜索页，找到商品标识；返回 (slug, 说明)"""
    if not ref.startswith("search:"): return ref, ""
    page.goto(ref[7:], wait_until="domcontentloaded", timeout=45000); page.wait_for_timeout(6000)
    for _ in range(3): page.mouse.wheel(0, 2000); page.wait_for_timeout(700)
    hrefs = page.evaluate("() => [...document.querySelectorAll('a[href]')].map(a => a.href)")
    slugs = []
    for h in hrefs:
        mm = re.search(r"/pl/product/([a-z0-9\-]+)/?(?:buy/?)?(?:[?#].*)?$", h)
        if mm and mm[1] not in slugs: slugs.append(mm[1])
    want = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if want in slugs: return want, ""
    return None, f"搜索结果里没有找到该型号 [候选: {', '.join(slugs[:6]) or '无'}]"

def evaluate(its, mem, promo):
    """某个型号的全部 SKU + 表里的内存和促销价 -> (格子文字, [(颜色, 价格, 状态)])"""
    if not its: return "mi.com 未上架", []
    want = mem_key(mem); sel = [x for x in its if x[1] == want]
    if not sel: return "未找到该内存版本", []
    live = [x for x in sel if x[5] != "unavailable"]
    diff = [f"{c} {p:g}" for _, _, c, p, _, st in live if abs(p - float(promo)) > 0.005]
    okc = [c for _, _, c, p, _, st in live if abs(p - float(promo)) <= 0.005]
    unav = [c for _, _, c, p, _, st in sel if st == "unavailable"]
    return ("unavailable" if not live else cell.build(okc, diff, [("unavailable", unav)])), [(c, p, st) for _, _, c, p, _, st in sel]

def main(xlsx, resume=False):
    if (OUT / "~$price_log.xlsx").exists(): sys.exit("price_log.xlsx 正在被 Excel 打开。请先关闭 Excel(提示保存时选\"不保存\")，再重新运行。")
    ws_in = openpyxl.load_workbook(xlsx, data_only=True).worksheets[0]
    hdr = {str(c.value).split("\n")[0].strip().lower(): c.column for c in ws_in[1] if c.value}
    today = dt.date.today(); mp = OUT / "price_log.xlsx"; master = openpyxl.load_workbook(mp)
    if today.isoformat() not in master.sheetnames: sys.exit("请先运行 check_mistore.py 生成今天的 sheet")
    ws = master[today.isoformat()]; mc = next(c for k, c in hdr.items() if k.startswith("micom"))
    cache, log, blocked = {}, [], 0
    with sync_playwright() as p:
        try: page = p.chromium.connect_over_cdp("http://localhost:9222").contexts[0].new_page()
        except Exception: sys.exit("连不上专用 Chrome。请先双击「打开专用Chrome.command」打开它(不要关)，再运行。")
        try:
            for _try in (1, 2):                        # Chrome 刚启动时第一次常超时，重试一次(更长超时)
                try: page.goto("https://www.mi.com/pl/", wait_until="domcontentloaded", timeout=90000); break
                except Exception:
                    if _try == 2: raise
                    page.wait_for_timeout(20000)
            page.wait_for_timeout(4000)
            for r in range(2, ws_in.max_row + 1):
                name, mem, promo = (ws_in.cell(r, hdr[k]).value for k in ("product name", "memory", "rrp after promotion"))
                if not (name and mem and promo): continue
                name = str(name).strip(); cur = ws.cell(r, mc).value
                if resume and cur and not str(cur).lstrip("[促销期外] ").startswith(FAIL): print(f"行{r} 已有结果，跳过"); continue
                slug = config.MICOM.get(name); err = None
                if not slug: txt = "未配置"
                elif blocked >= 2: txt = "被网站拦截"
                else:
                    try:
                        if slug not in cache:
                            real, why = resolve(page, name, slug)
                            if real is None:   # 搜索页没有可点击的链接 -> 先直接试商品标识；仍没有数据 = 页面上变灰(缺货)，按 unavailable 记
                                guess = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"); b0 = fetch(page, guess)
                                cache[slug] = b0 if b0 and micom.items(b0) else "GREY"
                            else: cache[slug] = fetch(page, real)
                            time.sleep(random.uniform(1.5, 3.0))
                        body = cache[slug]
                        if body == "GREY": txt = "unavailable"
                        elif body is None: txt = "读取失败(没有取到数据)"
                        else:
                            txt, rows = evaluate(micom.items(body), mem, promo)
                            log += [[today.isoformat(), "mi.com", name, mem, c, p_, promo, st] for c, p_, st in rows]
                        blocked = 0
                    except Blocked: txt = "被网站拦截"; blocked += 1
                    except Exception as ex:
                        if type(ex).__name__ == "TargetClosedError" or "has been closed" in str(ex): master.save(mp); sys.exit("专用 Chrome 被关闭或崩溃了，已停止。请双击「打开专用Chrome.command」重新打开它(不要关)，然后双击「继续运行.command」。")
                        txt = f"读取失败({type(ex).__name__}: {str(ex)[:50]})"
                s, e = ws_in.cell(r, hdr["offer start date"]).value, ws_in.cell(r, hdr["offer end date"]).value
                s = s.date() if isinstance(s, dt.datetime) else s; e = e.date() if isinstance(e, dt.datetime) else e
                if isinstance(s, dt.date) and isinstance(e, dt.date) and not (s <= today <= e) and txt not in ("未配置",): txt = "[促销期外] " + txt
                if txt.startswith(FAIL) and cur and not str(cur).startswith(FAIL): txt = str(cur) + " [未刷新]"
                ws.cell(r, mc).value = txt; print(f"行{r} {name} {mem}: {txt}"); master.save(mp)
        finally: page.close()
    hist.append_rows(OUT / "data" / "history.csv", log); print(f"完成，已写入 price_log.xlsx [{today.isoformat()}] 的 micom 列")

if __name__ == "__main__":
    a = sys.argv[1:]; main(a[0], "--resume" in a)
