"""mi.com/pl 探测: 打开 2 个购买页，记录页面渲染后的文字 + 页面后台请求的数据接口(价格/库存通常在这里)，保存到 data/raw/micom_probe/。
用法: .venv/bin/python app/tools/probe_micom.py     (需先开专用 Chrome)。只访问 2 个页面，每页等 8 秒。"""
import json, pathlib, re
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parents[2]; OUT = ROOT / "data" / "raw" / "micom_probe"; OUT.mkdir(parents=True, exist_ok=True)
URLS = ["https://www.mi.com/pl/product/xiaomi-17t-pro/buy/", "https://www.mi.com/pl/product/xiaomi-17t/buy/"]
KEY = re.compile(r"price|stock|sku|inventory|avail|salable|soldout|sold_out|cash|market", re.I)
with sync_playwright() as p:
    pg = p.chromium.connect_over_cdp("http://localhost:9222").contexts[0].new_page(); hits = []
    def on_resp(r):
        try:
            if "json" in (r.headers.get("content-type", "")) and r.status == 200:
                body = r.text()
                if len(body) < 3_000_000 and KEY.search(body): hits.append((r.url, body))
        except Exception: pass
    pg.on("response", on_resp)
    for i, u in enumerate(URLS):
        hits.clear(); pg.goto(u, wait_until="domcontentloaded", timeout=45000); pg.wait_for_timeout(8000)
        txt = pg.inner_text("body"); (OUT / f"page{i}_text.txt").write_text(txt, encoding="utf-8")
        (OUT / f"page{i}.html").write_text(pg.content(), encoding="utf-8")
        print(f"\n== {u}\n页面可见文字(前 600 字):\n{txt[:600]}\n后台数据接口(含价格/库存关键字) {len(hits)} 个:")
        for j, (ru, body) in enumerate(hits):
            (OUT / f"page{i}_api{j}.json").write_text(body, encoding="utf-8"); print(f"  [{j}] {len(body)//1000}KB {ru[:150]}")
    pg.close()
print("\n已保存到 data/raw/micom_probe/")
