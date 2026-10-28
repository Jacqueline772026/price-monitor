"""一键运行入口(Windows / Mac / Linux 通用)。
用法:
  python app/run_all.py                      # 每日完整流程
  python app/run_all.py --mode continue      # 跳过 Mi-Store，只补跑 mi.com 和 EURO/OleOle 没读到的格子
  python app/run_all.py --steps mistore,micom   # 只跑指定步骤: mistore, micom, retail, check, clean
  python app/run_all.py --table my_table.xlsx
流程: mistore -> (自动打开专用 Chrome) -> micom -> retail -> check(自检) -> clean(清理旧文件)。全程输出同时写入 data/logs/。"""
import argparse, datetime as dt, os, pathlib, platform, shutil, subprocess, sys, time, urllib.request
import paths

PORT = 9222
def chrome_up():
    try: urllib.request.urlopen(f"http://localhost:{PORT}/json/version", timeout=2); return True
    except Exception: return False

def chrome_exe():
    s = platform.system()
    cands = []
    if s == "Darwin": cands = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Chromium.app/Contents/MacOS/Chromium"]
    elif s == "Windows":
        for env in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            base = os.environ.get(env)
            if base: cands.append(os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"))
        cands.append(os.path.join(os.environ.get("PROGRAMFILES", ""), "Microsoft", "Edge", "Application", "msedge.exe"))
    else: cands = [shutil.which(x) or "" for x in ("google-chrome", "chromium", "chromium-browser")]
    return next((c for c in cands if c and os.path.exists(c)), None)

def start_chrome():
    """打开专用 Chrome(独立资料夹，不影响平时的 Chrome)，开放本机调试端口。已经开着就什么也不做。"""
    if chrome_up(): return True
    exe = chrome_exe()
    if not exe: print("找不到 Chrome。请安装 Google Chrome，或手动用 --remote-debugging-port=9222 启动它。"); return False
    profile = pathlib.Path.home() / "chrome-price-profile"
    print("正在打开专用 Chrome(请保持它开着，不要关)...")
    subprocess.Popen([exe, f"--remote-debugging-port={PORT}", f"--user-data-dir={profile}", "--no-first-run", "https://www.euro.com.pl/"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        if chrome_up(): return True
        time.sleep(2)
    print("专用 Chrome 没有在 60 秒内准备好。"); return False

def run(cmd, log):
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    p = subprocess.Popen([sys.executable, "-u", *cmd], cwd=paths.ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", env=env)
    for line in p.stdout:
        print(line, end=""); log.write(line); log.flush()
    return p.wait()

def main():
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(); ap.add_argument("--table", default=str(paths.PRICE_TABLE)); ap.add_argument("--mode", choices=["daily", "continue"], default="daily")
    ap.add_argument("--steps", default=""); a = ap.parse_args()
    table = pathlib.Path(a.table)
    if not table.exists(): sys.exit(f"找不到价格表 {table}。请把本周更新好的价格表放在项目根目录，命名为 price_table.xlsx (模板见 templates/)。")
    steps = [s for s in a.steps.split(",") if s] or (["micom", "retail", "check", "clean"] if a.mode == "continue" else ["mistore", "micom", "retail", "check", "clean"])
    paths.LOGS.mkdir(parents=True, exist_ok=True)
    logp = paths.LOGS / f"{dt.datetime.now():%Y-%m-%d_%H%M}{'_continue' if a.mode == 'continue' else ''}.log"
    print(f"使用表格: {table.name} | 步骤: {' -> '.join(steps)} | 日志: {logp.name}")
    with open(logp, "w", encoding="utf-8") as log:
        t = str(table)
        if "mistore" in steps and run(["app/check_mistore.py", t], log) != 0: print("Mi-Store 步骤出错，已停止"); steps = [s for s in steps if s in ("check", "clean")]
        if "micom" in steps or "retail" in steps:
            if not start_chrome(): print("无法使用专用 Chrome，跳过 micom 和 retail"); steps = [s for s in steps if s in ("check", "clean")]
        if "micom" in steps and run(["app/check_micom.py", t, "--resume"], log) != 0: print("mi.com 步骤出错，继续后面的步骤")
        if "retail" in steps: run(["app/check_retail.py", t, "--resume"], log)
        if "check" in steps: run(["app/health_check.py", str(logp)], log)
        if "clean" in steps: run(["app/maintenance.py"], log)
    print(f"\n结果: {paths.PRICE_LOG.name} 最前面那张 sheet；检查报告: {paths.REPORT.name}")

if __name__ == "__main__": main()
