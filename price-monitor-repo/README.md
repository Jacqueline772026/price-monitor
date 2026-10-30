# Price Monitor · 竞品价格监控

> 每天自动核对手机/平板在波兰各零售渠道的价格与库存，对照你的促销价表，结果记录到 Excel（每天一个 sheet）。
> Daily competitor price & stock check for Poland retail channels, compared against your promo-price table and logged to Excel (one sheet per day).

| 渠道 Channel | 方式 How | 状态 Status |
|---|---|---|
| Mi-Store (mi-store.pl) | HTTP 抓取类目页 + 商品页 JSON-LD 库存 | 自动 auto |
| mi.com/pl | 页面使用的 `productdetail` 接口 | 自动 auto |
| EURO (euro.com.pl) | 专用 Chrome + Playwright | 自动 auto（慢速、礼貌） |
| OleOle (oleole.pl) | 专用 Chrome + Playwright | 自动 auto（慢速、礼貌） |
| Allegro | 人或 AI agent 用浏览器读取 → `import_manual.py` 导入 | 辅助 assisted |

---

## 1. 它做什么 / What it does
- 读取你的**价格表**（`price_table.xlsx`，每周更新促销价与促销起止日），逐行逐颜色对比各渠道价格。
- 结果写入 **`price_log.xlsx`**：每天一个 sheet，最新在前；价格表本身**永远不会被修改**。
- 自动生成 **`check_report.txt`**（今天有没有问题）和 `debug_bundle.zip`（出错时发给维护者）。
- 自动清理旧文件（原始页面 7 天、日志 30 天、明细 90 天、sheet 60 张），文件夹不会越滚越大。
- 增减机型后用 `check_setup.py` 一键检查哪里缺配置；`add_link.py` 一行命令补链接；任何 AI agent 读 `AGENTS.md` 就能代你操作。

## 2. 单元格怎么读 / How to read a cell
| 内容 | 含义 |
|---|---|
| `OK` | 所有颜色价格都等于促销价 |
| `OK: Blue, Green \| Black 789` | 部分颜色正确，另一些颜色价格不同 |
| `789` | 所有颜色价格相同但不等于促销价 |
| `unavailable` | 缺货（Mi-Store 显示"通知到货"、mi.com 变灰、零售商缺货） |
| `unavailable: Green` | 仅部分颜色缺货 |
| `unavailable online` | 仅门店有货/无法配送（EURO、OleOle） |
| `无链接` | 价格表里有这款，但没配这个渠道的链接（忽略） |
| `未找到该内存版本` / `未配置` | 渠道没有该配置 / 型号尚未配置 |
| `[未刷新]` | 本次被网站拦截，沿用上一次的值 |
| `[促销期外]` | 今天不在这行的促销起止日期内 |

> 价格可能带小数（如 3044.99）：EURO/OleOle 的颜色或规格有加价，是真实价格。

## 3. 安装 / Install
需要 **Python 3.9+** 和 **Google Chrome**（或 Edge）。不需要下载额外浏览器。

| 系统 | 步骤 |
|---|---|
| macOS | 双击 `setup.command`（首次可能要右键→打开） |
| Windows | 双击 `setup.bat`（先安装 Python 并勾选 *Add to PATH*） |
| 命令行 | `python -m venv .venv` → `.venv/bin/pip install -r requirements.txt` |

然后准备三样东西：
1. **价格表**：放在项目根目录，命名 `price_table.xlsx`。表头见 `templates/price_table_template.xlsx`（SKU, Memory, Product Name, RRP, RRP after Promotion, Offer start/end date, 以及各渠道列 EURO / Oleole / GG / micom / Allegro）。
2. **链接库**：复制 `config/links.example.json` 为 `config/links.json`，填入你自己的 EURO / OleOle / Allegro 商品链接。键 = `SKU|内存`，带保护壳的商品加 `|cover`。
3. **型号对应**：在 `app/config.py` 的 `MISTORE` / `MICOM` 填入你的型号名 → 店内页面/标识（用 `app/tools/discover_mistore.py`、`discover_micom.py` 辅助查找）。

`config/links.json`、价格表、价格记录、`data/` 都已在 `.gitignore` 中，不会被上传。

## 4. 每天怎么用 / Daily use
1. **关闭 Excel 里的 `price_log.xlsx`**（若提示保存，选"不保存"）。否则旧窗口会覆盖脚本结果；脚本发现 `~$price_log.xlsx` 会拒绝运行。
2. 双击 **`run_daily.command`**（Mac）或 **`run_daily.bat`**（Windows）。
   脚本会自动打开一个**专用 Chrome**（独立资料夹，不影响你平时的浏览器），首次启动后多等约 30 秒再开始。运行期间请**不要关闭它**。
3. 被网站拦截或中途出问题 → 过几个小时双击 **`resume.*`**：只补没读到的格子，不重复访问已读到的。
4. 看 **`check_report.txt`**（"有问题 0 个"即正常）和 `price_log.xlsx` 里今天的 sheet。看完关闭 Excel，选"不保存"。

> 完整跑一遍约 30–40 分钟（EURO / OleOle 每页间隔 8–14 秒）。系统弹出密码框时请先输入，否则页面会超时。

命令行等价写法：`python app/run_all.py --mode daily|continue [--steps mistore,micom,retail,check,clean]`

## 5. Allegro 与 AI agent
Allegro 官方 API 读不到他人商品的报价，所以改为"读取 + 导入"：
1. 人或 agent 用浏览器逐个打开 `config/links.json` 里的 Allegro 链接（每批 ≤5 页，遇验证码立即停止），记录各颜色价格与是否可购买。
2. 写成 `data/allegro_input.csv`，表头 `sku,memory,color,price,status`（status 留空=有货；`unavailable`=缺货；`no_offer`=无此商品）。
3. 运行 `python app/import_manual.py --channel Allegro --csv data/allegro_input.csv`。比价规则与其他渠道完全一致；需要今天的 sheet 已存在（先跑过 mistore 步骤）。

**交给 agent（Claude、Codex 等）**：让它读 `AGENTS.md` 和 `skills/price-monitor-operator/SKILL.md`，即可代你每日运行、处理报错、增减机型并补链接、查 Allegro 并写入表格。

## 6. 增减机型 / Adding or removing models
1. 更新价格表（`price_table.xlsx`）。
2. `python app/check_setup.py` → 列出每个型号在各渠道缺的配置（只读，不联网；`--json` 供 agent 使用）。
3. Mi-Store / mi.com：编辑 `app/config.py`。EURO / OleOle / Allegro：
   `python app/tools/add_link.py SKU 内存 EURO <网址>`（渠道 `EURO`/`OleOle`/`Allegro`；保护壳加 `--cover`）。
4. 再跑 `check_setup.py` 直到没有缺项；`python app/tools/dump_url.py <网址>` 可验证一个链接能否被解析。

## 7. 礼貌抓取与限制 / Politeness & limits
- 仅对公开页面做**低频**价格核对：EURO/OleOle 每页 8–14 秒，一天完整跑一次。
- **不绕过**任何反爬或验证码；检测到拦截页（Lockdown / Lock / Blokada / 跳回首页）连续 2 次就自动停止该站，已读到的结果保留，未读到的标 `[未刷新]`。
- 请遵守各网站的服务条款，并只用于合理的内部价格核对。

## 8. 项目结构 / Layout
```
app/            核心脚本（run_all, check_*.py, import_manual, check_setup, tools/）
config/         links.example.json（你的 links.json 不上传）
templates/      价格表模板
skills/         给 AI agent 的操作说明 price-monitor-operator
docs/           ARCHITECTURE.md · TROUBLESHOOTING.md
tests/          python tests/run_tests.py（离线自检）
AGENTS.md       agent 入口说明
CHANGELOG.md    更新记录
```
运行时生成（已被 git 忽略）：`price_log.xlsx`、`data/`、`check_report.txt`、`debug_bundle.zip`。

## 9. 常见问题 / FAQ
见 [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)。最常见的三个：结果被旧 Excel 覆盖、专用 Chrome 被关、OleOle/EURO 被拦截。

## 10. 兼容性 / Compatibility
- macOS：在 Mac 上日常使用并验证。
- Windows：已提供 `.bat` 和 Windows 的 Chrome/Edge 路径查找，**尚未在真实 Windows 电脑上完整测试**；如遇问题欢迎提 issue。
- Python 3.9+。

## 11. 许可证 / License
暂未指定。公开发布前请仓库所有者自行选择（例如 MIT）并添加 `LICENSE` 文件。
