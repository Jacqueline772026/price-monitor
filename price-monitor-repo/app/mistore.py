"""Mi-Store (IdoSell) 解析：从型号分类页提取 每个商品的 名称/内存/颜色/现价/原价。"""
import re
from bs4 import BeautifulSoup

def _num(s):
    m = re.search(r"(\d[\d\s]*)[,.](\d{2})", s or "")
    return float(m.group(1).replace(" ", "") + "." + m.group(2)) if m else None

UNAVAIL = re.compile(r"powiadom|niedost|brak|wyprzeda|zapytaj|wkr[oó]tce|notify|sold", re.I)
AVAIL = re.compile(r"kup|dodaj do koszyka|do koszyka|zam[oó]w|przedsprzeda", re.I)

def classify(text, cls=""):
    """按钮文字 -> available / unavailable / unknown (unknown 时调用方会把原文写出来)"""
    t = text or ""
    if UNAVAIL.search(t) or "notify" in (cls or "").lower(): return "unavailable"
    if AVAIL.search(t): return "available"
    return "unknown"

def parse_category(html):
    out = []
    for w in BeautifulSoup(html, "html.parser").select("div.product_wrapper"):
        a = w.select_one("h3 a, .product__name") or w.select_one("a[title]")
        name = (a.get("title") or a.get_text(" ", strip=True)) if a else None
        price = w.get("data-price")
        price = float(price) if price else _num((w.select_one("strong.price") or w).get_text(" ", strip=True))
        old = w.select_one("span.price.--max del")
        av = w.select_one(".availability_info") or w.select_one(".buy_section")
        atxt = re.sub(r"\s+", " ", av.get_text(" ", strip=True)) if av else ""
        status = classify(atxt, " ".join(av.get("class", [])) if av else "")
        # 保险: 整个商品块里只要出现"到货通知"文字(波兰语 Powiadom o dostępności)，无论在哪个元素里，都算缺货
        if status != "unavailable" and re.search(r"powiadom\s+o\s+dost", w.get_text(" ", strip=True), re.I):
            status, atxt = "unavailable", atxt or "Powiadom o dostępności"
        mem = re.search(r"(\d+\+\d+(?:GB|TB)?)", name or "")
        color = None
        if name and mem:
            color = name.split(mem.group(1), 1)[1].strip()
            color = re.sub(r"^(GB|TB)\s*", "", color)
        out.append({"name": name, "memory": mem.group(1) if mem else None, "color": color,
                    "price": price, "status": status, "status_text": atxt, "regular": _num(old.get_text()) if old else None,
                    "url": (a.get("href") if a and a.has_attr("href") else None)})
    return [o for o in out if o["name"] and o["price"]]


def stock_status(html):
    """商品详情页 -> (status, 依据)。分类页的 'Kup Teraz' 不可靠(缺货商品也显示)，库存以详情页为准。
    优先级: 结构化数据 availability > 有加入购物车按钮 > 到货通知(Powiadom o dostępności / Notify about availability)"""
    h = html or ""
    m = re.search(r'"availability"\s*:\s*"[^"]*?(InStock|OutOfStock|SoldOut|PreOrder|BackOrder|LimitedAvailability|Discontinued|InStoreOnly|OnlineOnly)', h)
    if m: return ("unavailable" if m[1] in ("OutOfStock", "SoldOut", "Discontinued") else "available"), "结构化:" + m[1]
    notify = re.search(r"powiadom\s+o\s+dost|notify\s+about\s+availability", h, re.I)
    basket = re.search(r"dodaj\s+do\s+koszyka|add\s+to\s+(?:basket|cart)|projector_button_basket", h, re.I)
    if notify and not basket: return "unavailable", "到货通知"
    if basket and not notify: return "available", "购物车按钮"
    if notify and basket: return "unknown", "购物车和到货通知同时出现"
    return "unknown", "无库存标记"
