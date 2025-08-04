#!/bin/bash
# Word文檔分割工具安裝腳本

echo "🔧 正在安裝Word文檔分割與合併工具..."

# 檢查Python是否安裝
if ! command -v python3 &> /dev/null; then
    echo "❌ 錯誤：未找到Python3，請先安裝Python3"
    exit 1
fi

echo "✅ Python3 已安裝"

# 安裝依賴
echo "📦 正在安裝依賴 (python-docx, docxcompose)..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ 依賴安裝成功"
else
    echo "❌ 依賴安裝失敗"
    exit 1
fi

# 設置執行權限
echo "🔐 設置執行權限..."
chmod +x split_ballontranslator_docx.py
chmod +x split_docx_by_pages.py
chmod +x merge_docx.py
chmod +x test_split_script.py

echo "✅ 安裝完成！"
echo ""
echo "📖 使用方法："
echo "   分割: python3 split_ballontranslator_docx.py your_document.docx"
echo "   合併: python3 merge_docx.py your_split_folder"
echo ""
echo "🧪 測試功能："
echo "  python3 test_split_script.py"
echo ""
echo "📚 詳細說明請查看 README_split_docx.md 和 README_format_guide.md" 