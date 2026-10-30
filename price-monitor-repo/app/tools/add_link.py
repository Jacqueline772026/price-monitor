"""给链接库 config/links.json 添加或更新一条链接(会校验网址域名，保持文件格式)。
用法: python app/tools/add_link.py SKU 内存 渠道 网址 [--cover]
  渠道: EURO / OleOle / Allegro ；--cover 表示这是"带保护壳"的商品(键后面加 |cover)
例:   python app/tools/add_link.py DEMO-A 12+512 EURO https://www.euro.com.pl/telefony-komorkowe/xxx.bhtml"""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
DOM = {"EURO": "euro.com.pl", "OleOle": "oleole.pl", "Allegro": "allegro.pl"}
a = [x for x in sys.argv[1:] if x != "--cover"]; cover = "--cover" in sys.argv
if len(a) != 4: sys.exit(__doc__)
sku, mem, ch, url = a
ch = next((k for k in DOM if k.lower() == ch.lower()), None) or sys.exit(f"渠道必须是 {', '.join(DOM)}")
if not url.startswith("https://") or DOM[ch] not in url.split("/")[2]: sys.exit(f"网址必须是 https://...{DOM[ch]}/...")
p = ROOT / "config" / "links.json"; p.parent.mkdir(exist_ok=True)
d = json.load(open(p, encoding="utf-8")) if p.exists() else {}
key = f"{sku}|{mem}" + ("|cover" if cover else ""); old = d.setdefault(key, {}).get(ch)
d[key][ch] = url
json.dump(dict(sorted(d.items())), open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(("更新" if old else "新增"), key, ch, "->", url, ("(原: " + old + ")") if old and old != url else "")
