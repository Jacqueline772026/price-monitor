# Agent 说明 / Instructions for coding agents (Codex, Claude Code, etc.)

这是一个竞品价格监控工具。请先阅读 `skills/price-monitor-operator/SKILL.md`，按其中流程操作（每日运行、处理报错、增减机型补链接、Allegro 手动导入）。
This is a competitor price-monitoring tool; follow `skills/price-monitor-operator/SKILL.md`.

- 入口: `python app/run_all.py`；体检: `python app/check_setup.py`；加链接: `python app/tools/add_link.py`；导入手查价格: `python app/import_manual.py`。
- 不要绕过验证码/反爬；低频访问；不要提交真实价格数据、`config/links.json`、`data/`。
- 改完代码跑 `python tests/run_tests.py`。
