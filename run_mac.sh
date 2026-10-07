#!/bin/bash
# 桌面助手 (Desktop Assistant) - macOS 快速啟動腳本
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ ! -d ".venv" ]; then
    echo "[DesktopAssistant] 首次執行，建立虛擬環境..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo "[DesktopAssistant] 啟動桌面助手 (macOS)..."
python3 main.py
