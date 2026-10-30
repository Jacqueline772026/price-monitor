"""跑完后自检: 扫描今天 sheet 里 GG/EURO/Oleole 三列，列出有问题的格子 -> check_report.txt；有问题时自动打包 debug_bundle.zip。
用法: python app/health_check.py [日志文件]"""
import datetime as dt, pathlib, sys, zipfile
import openpyxl
ROOT = pathlib.Path(__file__).resolve().parent.parent
RULES = [  # (格子里出现的文字, 含义, 你该怎么做)
    ("[未刷新]", "这次没读到，格子里保留的是更早读到的结果(可能不是最新)", "明天正常运行会自动刷新；今天要用的话，该结果仅供参考。"),
    ("被网站拦截", "网站拦截了访问", "今天不要再跑。明天再运行；如果连续两天都出现，把 debug_bundle.zip 交给维护者或 agent。"),
    ("读取失败", "网络或加载超时", "再运行一次 run_daily 或 resume(只会重试失败的格子)。第二次还失败就发 debug_bundle.zip。"),
    ("页面无价格数据", "页面打开了但读不到价格(链接失效、商品下架或网站改版)", "先在浏览器手动打开该链接确认；确认有价格就把 debug_bundle.zip 交给维护者或 agent。"),
    ("链接商品与表不符", "表里的链接指向的不是这个型号/内存", "把正确的商品链接交给维护者或 agent，用 add_link.py 更新链接库。"),
    ("搜索结果里没有找到", "站内搜索没找到该型号/内存", "手动搜一下确认是否下架；有的话用 add_link.py 补上商品链接。"),
    ("状态未知", "页面出现了脚本不认识的库存状态词", "把 debug_bundle.zip 交给维护者或 agent，补充识别规则。"),
    ("无价格", "某个颜色没读到价格", "把 debug_bundle.zip 交给维护者或 agent。"),
]
INFO = ("无链接", "未找到该内存版本", "未配置", "mi.com 未上架")  # 不是错误: 表里没给链接 / Mi-Store 没上架或未配置
CH = {"gg": "Mi-Store", "euro": "EURO", "oleole": "OleOle", "micom": "mi.com"}

def main(log=None):
    today = dt.date.today().isoformat()
    wb = openpyxl.load_workbook(ROOT / "price_log.xlsx", data_only=True)
    if today not in wb.sheetnames: sys.exit("price_log.xlsx 里没有今天的 sheet，说明今天的运行没有成功，请把终端输出和 data/logs 里最新的日志交给维护者或 agent。")
    ws = wb[today]
    hdr = {str(c.value).split("\n")[0].strip().lower(): c.column for c in ws[1] if c.value}
    name = hdr.get("product name", 3)
    probs, nolink, total, empty = [], 0, 0, 0
    for r in range(2, ws.max_row + 1):
        if not ws.cell(r, 1).value: continue
        for key, ch in CH.items():
            if key not in hdr: continue
            v = ws.cell(r, hdr[key]).value; total += 1
            if v in (None, ""): empty += 1; probs.append((r, ch, "(空白，没有运行)", "这一格没有结果", "再运行一次 resume；仍为空把 debug_bundle.zip 交给维护者或 agent。")); continue
            v = str(v)
            if any(i in v for i in INFO): nolink += 1; continue
            for pat, why, todo in RULES:
                if pat in v: probs.append((r, ch, v, why, todo)); break
    lines = [f"价格检查报告 {today}  (生成于 {dt.datetime.now():%H:%M})", f"检查格子 {total} 个；有问题 {len(probs)} 个；缺链接/Mi-Store 未上架(正常，不算错误) {nolink} 个", ""]
    if not probs: lines.append("✔ 没有发现需要处理的问题。")
    for r, ch, v, why, todo in probs:
        lines += [f"行{r} {ws.cell(r,1).value} {ws.cell(r,name).value} {ws.cell(r,2).value} | {ch}", f"   格子内容: {v}", f"   原因: {why}", f"   怎么办: {todo}", ""]
    (ROOT / "check_report.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:2]))
    zp = ROOT / "debug_bundle.zip"
    if probs:
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            z.write(ROOT / "check_report.txt", "check_report.txt")
            z.write(ROOT / "price_log.xlsx", "price_log.xlsx")
            if log and pathlib.Path(log).exists(): z.write(log, "运行日志.log")
            for f in (ROOT / "data" / "raw").glob("fail_*.html"):
                if dt.date.fromtimestamp(f.stat().st_mtime) == dt.date.today(): z.write(f, "失败页面/" + f.name)
        print(f"⚠ 有 {len(probs)} 个问题，详情见 check_report.txt；已生成 debug_bundle.zip，交给维护者或 agent 即可。")
    elif zp.exists(): zp.unlink()

if __name__ == "__main__": main(sys.argv[1] if len(sys.argv) > 1 else None)
