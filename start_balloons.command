#!/bin/bash
cd "$(dirname "$0")" || exit 1

wait_for_error() {
  echo
  read -r -p "按 Enter 關閉..."
}

close_current_terminal_window() {
  local current_tty
  current_tty="$(tty)"
  osascript -e "delay 0.4" \
    -e "tell application \"Terminal\"" \
    -e "repeat with w in windows" \
    -e "repeat with t in tabs of w" \
    -e "if tty of t is \"$current_tty\" then" \
    -e "close w" \
    -e "return" \
    -e "end if" \
    -e "end repeat" \
    -e "end repeat" \
    -e "end tell" >/dev/null 2>&1 </dev/null &
}

# 啟動虛擬環境
source venv/bin/activate
STATUS=$?

if [ "$STATUS" -eq 0 ]; then
  # 檢查並安裝必要的依賴
  pip install setuptools
  STATUS=$?
fi

if [ "$STATUS" -eq 0 ]; then
  pip install -r requirements.txt
  STATUS=$?
fi

if [ "$STATUS" -eq 0 ]; then
  # 啟動程式
  python launch.py
  STATUS=$?
fi

if [ "$STATUS" -ne 0 ]; then
  wait_for_error
else
  close_current_terminal_window
fi

exit "$STATUS"
