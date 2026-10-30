import csv, pathlib
HEAD = ["date", "channel", "product", "memory", "color", "price", "promo_price", "status"]
def append_rows(path, rows):
    path = pathlib.Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    old = []
    if path.exists():
        with open(path, encoding="utf-8-sig", newline="") as f: old = list(csv.reader(f))
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(HEAD)
        for r in old[1:]: w.writerow((r + [""] * 8)[:8])
        w.writerows((list(r) + [""] * 8)[:8] for r in rows)
