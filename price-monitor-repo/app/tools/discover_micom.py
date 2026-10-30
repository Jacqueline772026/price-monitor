"""发现 mi.com/pl 上所有手机/平板型号的链接标识(slug)。只打开商品列表页(约 6–10 页，每页等 7 秒)，结果存 data/raw/micom_probe/catalog.json 并打印。
用法: .venv/bin/python app/tools/discover_micom.py     (需先开专用 Chrome)"""
import json, pathlib, re
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parents[2]; OUT = ROOT / "data" / "raw" / "micom_probe"; OUT.mkdir(parents=True, exist_ok=True)
START = "https://www.mi.com/pl/product-list/phone/xiaomi/"
JS = """() => [...document.querySelectorAll('a[href]')].map(a => [a.href, (a.innerText||'').trim().replace(/\\s+/g,' ').slice(0,60)])"""
cat, seen = {}, set()
with sync_playwright() as p:
    pg = p.chromium.connect_over_cdp("http://localhost:9222").contexts[0].new_page()
    def visit(u):
        pg.goto(u, wait_until="domcontentloaded", timeout=45000); pg.wait_for_timeout(5000)
        for _ in range(4): pg.mouse.wheel(0, 2500); pg.wait_for_timeout(800)
        pg.wait_for_timeout(1500); return pg.evaluate(JS)
    links = visit(START); seen.add(START)
    lists = []
    for h, t in links:
        h = h.split("?")[0].split("#")[0]
        if "/pl/product-list/" in h and h not in lists and h not in seen: lists.append(h)
    print("发现商品列表页:", *lists, sep="\n  ")
    pages = [START] + [u for u in lists if re.search(r"/(phone|tablet|pad|smartphone|redmi|poco|xiaomi)", u)][:9]
    for i, u in enumerate(pages):
        ls = links if u == START else visit(u)
        for h, t in ls:
            m = re.search(r"/pl/product/([a-z0-9\-]+)/?$", h.split("?")[0])
            if m: cat.setdefault(m[1], t)
        print(f"[{i}] {u}  累计型号 {len(cat)}")
    pg.close()
json.dump(cat, open(OUT / "catalog.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nmi.com/pl 型号标识:"); [print(" ", k, "|", v) for k, v in sorted(cat.items())]
