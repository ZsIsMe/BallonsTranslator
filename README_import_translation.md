# TXT 譯文導入腳本使用說明

## 功能描述

這個腳本可以從命令行將 TXT 格式的譯文文件導入到 BallonTranslator 的 JSON 項目文件中，生成一個新的 JSON 文件而不修改原始文件。

## 使用方法

### 基本語法
```bash
python import_translation_from_txt.py <json_file> [txt_file] [--output OUTPUT_FILE]
```

### 參數說明
- `json_file`: 輸入的 JSON 項目文件路徑（必需）
- `txt_file`: 包含譯文的 TXT 文件路徑（可選，默認根據JSON文件名自動生成）
- `--output` 或 `-o`: 指定輸出 JSON 文件名（可選）

### 自動生成TXT文件名規律
當不提供 `txt_file` 參數時，腳本會根據以下規律自動生成TXT文件路徑：
- JSON文件：`imgtrans_41.json`
- 自動生成：`deepseek_imgtrans_41_source.txt`
- 規律：`deepseek_` + JSON文件名（去掉.json） + `_source.txt`

### 使用示例

#### 1. 自動生成TXT文件名（推薦）
```bash
python import_translation_from_txt.py imgtrans_41.json
```
這會自動尋找 `deepseek_imgtrans_41_source.txt` 並生成 `zs_imported_translate_imgtrans_41.json`

#### 2. 手動指定TXT文件
```bash
python import_translation_from_txt.py project.json translated.txt
```
這會在JSON文件同目錄下生成 `zs_imported_translate_project.json` 文件

#### 3. 指定輸出文件名
```bash
python import_translation_from_txt.py project.json translated.txt --output my_project.json
```
這會生成 `my_project.json` 文件

#### 4. 完整路徑示例
```bash
python import_translation_from_txt.py /path/to/imgtrans_41.json
```
這會自動尋找 `/path/to/deepseek_imgtrans_41_source.txt` 並生成 `/path/to/zs_imported_translate_imgtrans_41.json`

## TXT 文件格式要求

TXT 文件必須遵循以下格式（這是從 BallonTranslator 導出的標準格式）：

```
### 頁面名稱1

1. 第一個文本塊的譯文

2. 第二個文本塊的譯文

3. 第三個文本塊的譯文


### 頁面名稱2

1. 另一頁的第一個文本塊譯文

2. 另一頁的第二個文本塊譯文
```

### 格式說明
- 每個頁面以 `### 頁面名稱` 開始
- 文本塊以數字序號開始（如 `1.`, `2.`, `3.`）
- 頁面之間用空行分隔
- 文本塊之間用空行分隔

## 執行結果

腳本執行後會顯示以下信息：

### 成功情況
```
正在載入項目文件：project.json
正在從TXT文件導入譯文：translated.txt
✓ 譯文導入並匹配成功
✓ 成功生成：/path/to/zs_imported_translate_project.json
```

### 部分匹配情況
```
正在載入項目文件：project.json
正在從TXT文件導入譯文：translated.txt
警告：頁面 'page1.jpg' 的文本塊數量不匹配 - 項目中有5個，TXT文件中有4個
⚠ 譯文導入完成，但存在部分不匹配：
  不匹配的頁面：page1.jpg
✓ 成功生成：/path/to/zs_imported_translate_project.json
```

## 錯誤處理

### 常見錯誤及解決方法

1. **文件不存在**
   ```
   錯誤：JSON文件 'project.json' 不存在
   ```
   解決：檢查文件路徑是否正確

2. **JSON 格式錯誤**
   ```
   錯誤：JSON文件格式不正確 - ...
   ```
   解決：確認 JSON 文件是有效的 BallonTranslator 項目文件

3. **頁面不匹配**
   ```
   警告：在項目中找不到頁面 'unknown_page.jpg'
   ```
   解決：檢查 TXT 文件中的頁面名稱是否與項目中的圖片文件名一致

## 注意事項

1. **原文件安全**：腳本不會修改原始的 JSON 項目文件
2. **編碼格式**：確保 TXT 文件使用 UTF-8 編碼
3. **文件名匹配**：TXT 文件中的頁面名稱必須與項目中的圖片文件名完全一致
4. **文本塊順序**：TXT 文件中的文本塊順序必須與項目中的順序一致

## 依賴要求

- Python 3.6 或更高版本
- 標準庫：`sys`, `json`, `os`, `argparse`, `re`, `pathlib`

不需要額外安裝其他第三方庫。

## 故障排除

如果遇到問題，請檢查：

1. Python 版本是否符合要求
2. 文件路徑是否正確
3. TXT 文件格式是否符合要求
4. JSON 項目文件是否完整有效
5. 文件是否有讀寫權限 