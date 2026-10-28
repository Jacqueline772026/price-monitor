"""离线自检(不联网、不需要真实数据): python tests/run_tests.py"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "app"))
import cell

def eq(got, want):
    assert got == want, f"期望 {want!r}，实际 {got!r}"; print("ok", want)

P = 1799
eq(cell.summarize([("Black", 1799, ""), ("Blue", 1799, "")], P), "OK")
eq(cell.summarize([("Black", 1799, ""), ("Blue", 1899, "")], P), "OK: Black | Blue 1899")
eq(cell.summarize([("Black", 1999, ""), ("Blue", 1999, "")], P), "1999")
eq(cell.summarize([("Black", None, "unavailable"), ("Blue", None, "unavailable")], P), "unavailable")
eq(cell.summarize([("", 1799, "")], P), "OK")
print("全部通过")
