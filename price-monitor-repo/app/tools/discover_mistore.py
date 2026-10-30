"""盘点 Mi-Store 上与你表格型号相关的所有商品(型号/内存/颜色/价格/页面)，输出 mistore_catalog.csv，
用来核对 '表里的型号 <-> Mi-Store 页面型号' 的对应关系。只读、不改表。用法: python app/tools/discover_mistore.py price_table.xlsx"""
import csv, re, sys, time, pathlib
from urllib.parse import quote_plus, urljoin
import openpyxl, requests
from bs4 import BeautifulSoup
import sys as _s, pathlib as _p; _s.path.insert(0, str(_p.Path(__file__).resolve().parents[1]))
import mistore

OUT = pathlib.Path(__file__).resolve().parents[2] / "data"; OUT.mkdir(exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
     "Accept-Language": "pl-PL,pl;q=0.9"}
BASE = "https://mi-store.pl/"

def get(url):
    r = requests.get(url, headers=H, timeout=25); time.sleep(1.5)
    print(f"[{r.status_code}] {url}")
    return r.text if r.status_code == 200 else ""

ws = openpyxl.load_workbook(sys.argv[1], data_only=True).worksheets[0]
names = sorted({str(r[2]).strip() for r in ws.iter_rows(min_row=2, values_only=True) if r[2]})
queries = set()
for n in names:
    queries.add(n); queries.add(re.sub(r"\s*5G\b", "", n).strip()); queries.add(re.sub(r"\s*\(?with cover\)?|\"", "", n).strip())
pages = {}
for q in sorted(queries):
    html = get(BASE + "search.php?text=" + quote_plus(q))
    for a in BeautifulSoup(html, "html.parser").find_all("a", href=True):
        if re.search(r"pol_m_(Smartfony|Tablety)_", a["href"]):
            pages.setdefault(urljoin(BASE, a["href"].split("#")[0]), q)
print(f"共找到 {len(pages)} 个型号分类页")
rows = []
for url in pages:
    html = get(url)
    for it in mistore.parse_category(html):
        rows.append([url.replace(BASE, ""), it["name"], it["memory"], it["color"], it["price"], it["regular"]])
with open(OUT / "mistore_catalog.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["page", "name", "memory", "color", "price", "regular"]); w.writerows(rows)
print(f"共 {len(rows)} 个商品 -> mistore_catalog.csv")
