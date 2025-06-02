#!/bin/bash
cd "$(dirname "$0")"

# 啟動虛擬環境
source venv/bin/activate

# 檢查並安裝必要的依賴
pip install setuptools
pip install -r requirements.txt

# 啟動程式
python launch.py 