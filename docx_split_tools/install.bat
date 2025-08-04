@echo off
REM Word文檔分割與合併工具安裝腳本 (Windows版本)

echo 🔧 正在安裝Word文檔分割與合併工具...

REM 檢查Python是否安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤：未找到Python，請先安裝Python
    pause
    exit /b 1
)

echo ✅ Python 已安裝

REM 安裝依賴
echo 📦 正在安裝依賴 (python-docx, docxcompose)...
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ 依賴安裝失敗
    pause
    exit /b 1
)

echo ✅ 依賴安裝成功
echo.
echo ✅ 安裝完成！
echo.
echo 📖 使用方法：
echo   分割: python split_ballontranslator_docx.py your_document.docx
echo   合併: python merge_docx.py your_split_folder
echo.
echo 🧪 測試功能：
echo   python test_split_script.py
echo.
echo 📚 詳細說明請查看 README_split_docx.md 和 README_format_guide.md
echo.
pause 