"""所有文件位置集中在这里。要改文件名，只改这一个文件。"""
import pathlib
APP = pathlib.Path(__file__).resolve().parent
ROOT = APP.parent
DATA = ROOT / "data"
RAW = DATA / "raw"
LOGS = DATA / "logs"
HISTORY = DATA / "history.csv"
CONFIG = ROOT / "config"
PRICE_TABLE = ROOT / "price_table.xlsx"        # 输入: 你每周更新的价格表(促销价/日期)
PRICE_LOG = ROOT / "price_log.xlsx"            # 输出: 每天一张 sheet
EXCEL_LOCK = ROOT / "~$price_log.xlsx"         # Excel 打开文件时生成的锁文件
REPORT = ROOT / "check_report.txt"             # 每次跑完自动生成的问题清单
BUNDLE = ROOT / "debug_bundle.zip"             # 有问题时自动打包，发给维护者/agent

def links_file():
    """真实链接库 config/links.json(不进 git)；没有就退回示例文件。"""
    p = CONFIG / "links.json"
    return p if p.exists() else CONFIG / "links.example.json"
