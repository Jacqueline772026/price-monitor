import re
def build(ok, diff, groups=(), unknown=()):
    """单元格文字: 先写 OK 的颜色，再写价格不同的'颜色 价格'，再写 unavailable 类，最后是状态未知。各段用 ' | ' 分隔。
    全部正常只写 'OK'；有异常时才列颜色。例: 'OK: Blue, Green | Black 789 | unavailable: Ice Blue'"""
    parts = []
    # 所有在售颜色价格都对，且没有任何缺货/异常/状态未知 -> 只写 OK，不列颜色
    if ok and not diff and not any(cs for _, cs in groups) and not unknown: return "OK"
    if ok: parts.append("OK: " + ", ".join(ok))
    if diff:
        prices = [d.rsplit(" ", 1)[-1] for d in diff]
        same = not ok and len(set(prices)) == 1 and re.fullmatch(r"\d+(?:\.\d+)?", prices[0])
        parts.append(prices[0] if same else "; ".join(diff))   # 所有在售颜色同一个价格 -> 只写数字
    for label, cs in groups:
        if cs: parts.append(f"{label}: " + ", ".join(cs))
    if unknown: parts.append("状态未知: " + ", ".join(unknown))
    return " | ".join(parts)

def summarize(items, promo, tol=0.005):
    """通用比价: items = [(颜色, 价格, 状态)]，状态 'available'/'unavailable'(空=available)；promo = 表里的促销价。
    -> 格子文字(规则同所有渠道: 全对写 OK；颜色价格各异列出；同价写数字；缺货单独列出；整款缺货写 unavailable)。"""
    items = [(c or "", float(p) if p not in (None, "") else None, (s or "available").strip().lower()) for c, p, s in items]
    live = [x for x in items if x[2] != "unavailable"]
    if not live: return "unavailable"
    diff = [f"{c} {p:g}".strip() for c, p, s in live if p is None or abs(p - float(promo)) > tol]
    okc = [c for c, p, s in live if p is not None and abs(p - float(promo)) <= tol and c]
    unav = [c for c, p, s in items if s == "unavailable" and c]
    if not diff and not unav and not okc and live: return "OK"      # 没写颜色但价格都对
    return build(okc, diff, [("unavailable", unav)])
