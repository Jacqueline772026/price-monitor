"""自动清理(每次运行结束后自动执行)。要改保留期，只改下面四个数字。"""
import csv, datetime as dt, pathlib, time
import openpyxl
ROOT = pathlib.Path(__file__).resolve().parent.parent
KEEP_RAW_DAYS = 7        # data/raw 里保存的网页快照
KEEP_LOG_DAYS = 30       # data/logs 运行日志
KEEP_HISTORY_DAYS = 90   # data/history.csv 历史明细
KEEP_SHEETS = 60         # price_log.xlsx 里最多保留多少天的 sheet

def prune_files(folder, days):
    n = 0; cut = time.time() - days * 86400
    if folder.exists():
        for f in folder.iterdir():
            if f.is_file() and f.stat().st_mtime < cut: f.unlink(); n += 1
    return n

def prune_history(days):
    p = ROOT / "data" / "history.csv"
    if not p.exists(): return 0
    with open(p, encoding="utf-8-sig", newline="") as f: rows = list(csv.reader(f))
    cut = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    keep = [r for r in rows[1:] if r and r[0] >= cut]
    if len(keep) < len(rows) - 1:
        with open(p, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f); w.writerow(rows[0]); w.writerows(keep)
    return len(rows) - 1 - len(keep)

def prune_sheets(keep):
    p = ROOT / "price_log.xlsx"
    if not p.exists(): return 0
    if (ROOT / "~$price_log.xlsx").exists(): print("  price_log.xlsx 正在被 Excel 打开，跳过 sheet 清理"); return 0
    wb = openpyxl.load_workbook(p)
    dated = sorted(n for n in wb.sheetnames if len(n) == 10 and n[4] == "-" and n[7] == "-")
    old = dated[:-keep] if len(dated) > keep else []
    for n in old: del wb[n]
    if old: wb.save(p)
    return len(old)

def folder_mb():
    return sum(f.stat().st_size for f in ROOT.rglob("*") if f.is_file() and ".venv" not in f.parts) / 1e6

if __name__ == "__main__":
    print("自动清理:")
    print(f"  网页快照删除 {prune_files(ROOT/'data'/'raw', KEEP_RAW_DAYS)} 个 (保留 {KEEP_RAW_DAYS} 天)")
    print(f"  运行日志删除 {prune_files(ROOT/'data'/'logs', KEEP_LOG_DAYS)} 个 (保留 {KEEP_LOG_DAYS} 天)")
    print(f"  历史明细删除 {prune_history(KEEP_HISTORY_DAYS)} 行 (保留 {KEEP_HISTORY_DAYS} 天)")
    print(f"  旧 sheet 删除 {prune_sheets(KEEP_SHEETS)} 张 (保留最近 {KEEP_SHEETS} 天)")
    print(f"  文件夹现在 {folder_mb():.1f} MB (不含 .venv)")
