#!/bin/bash
cd "$(dirname "$0")"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
.venv/bin/pip install -r requirements.txt && echo "安装完成 / Setup done. 请把价格表命名为 price_table.xlsx 放在本文件夹。"
echo; read -n 1 -s -r -p "按任意键关闭 / Press any key to close..."
