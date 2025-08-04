# Word文檔分割工具集

這個文件夾包含了用於分割BallonTranslator導出的Word文檔的工具集合。

## 📁 文件說明

### 核心工具
- **`split_ballontranslator_docx.py`** - 主要分割腳本（推薦使用）
- **`split_docx_by_pages.py`** - 通用分割腳本

### 文檔和測試
- **`README_split_docx.md`** - 詳細使用說明
- **`test_split_script.py`** - 功能測試腳本

## 🚀 快速開始

### 1. 安裝依賴
```bash
pip install python-docx
```

### 2. 基本使用
```bash
python split_ballontranslator_docx.py your_document.docx
```

### 3. 測試功能
```bash
python test_split_script.py
```

## 📖 詳細說明

請查看 `README_split_docx.md` 文件獲取完整的使用說明和技術細節。

## 🎯 功能特點

- ✅ 按頁面分割Word文檔
- ✅ 保持原始格式和圖片
- ✅ 智能文件命名
- ✅ 生成分割摘要
- ✅ 完善的錯誤處理

## 📞 支持

如果您在使用過程中遇到問題，請：
1. 查看 `README_split_docx.md` 中的常見問題
2. 運行 `test_split_script.py` 進行功能測試
3. 檢查輸入文件格式是否正確

---
*此工具集專為BallonTranslator項目設計* 