"""mi.com/pl 解析: productdetail 接口数据 -> 每个 SKU 的 内存/颜色/现价/原价/库存。"""
import json, re
MEM = re.compile(r"(\d+)\s*GB\s*\+\s*(\d+)\s*(GB|TB)", re.I)

def items(data):
    """-> [(型号名, (RAM, ROM_GB), 颜色, 现价, 原价, 'available'/'unavailable')]"""
    d = json.loads(data) if isinstance(data, str) else data
    out = []
    for spu in ((d.get("data") or {}).get("item_detail") or {}).get("spu_list") or []:
        sn = re.sub(r"\s+", " ", spu.get("spu_name", "")).strip()
        for it in spu.get("item_list") or []:
            name = re.sub(r"\s+", " ", it.get("item_name", "")).strip()
            m = MEM.search(name)
            if not m or it.get("price") is None: continue
            mem = (int(m[1]), int(m[2]) * (1024 if m[3].upper() == "TB" else 1))
            col = re.sub(re.escape(sn), " ", name.replace(m.group(0), " "), flags=re.I)
            col = re.sub(r"\s+", " ", col).strip()
            unav = it.get("is_out_of_stock") or it.get("is_not_for_sale") or it.get("is_sale") is False
            out.append((sn, mem, col, float(it["price"]), float(it.get("market_price") or 0), "unavailable" if unav else "available"))
    return out
