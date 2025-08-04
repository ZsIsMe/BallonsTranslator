#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BallonTranslator Word文檔合併腳本
使用 docxcompose 庫實現無損合併，確保圖片和格式被完整保留。
"""

import os
import sys
import argparse
from pathlib import Path
from docx import Document
from docxcompose.composer import Composer

def merge_docx_files(input_dir, output_file=None):
    """
    使用 docxcompose 合併指定文件夾中的所有 .docx 文件。

    Args:
        input_dir (str): 包含分割後 .docx 文件的文件夾路徑。
        output_file (str, optional): 合併後的輸出文件路徑。如果未提供，將自動生成。
    """
    # 驗證輸入文件夾是否存在
    if not os.path.isdir(input_dir):
        print(f"❌ 錯誤：輸入的文件夾不存在 -> {input_dir}")
        return False

    # 查找並排序所有 .docx 文件
    input_path = Path(input_dir)
    docx_files = sorted(list(input_path.glob("*.docx")))

    # 過濾掉Word臨時文件（以'~$'開頭）
    docx_files = [f for f in docx_files if not f.name.startswith('~')]

    if not docx_files:
        print(f"⚠️ 警告：在文件夾 '{input_dir}' 中未找到任何 .docx 文件。")
        return False
        
    print(f"🔍 找到 {len(docx_files)} 個待合併的 .docx 文件。")
    print("文件順序:")
    for i, f in enumerate(docx_files):
        print(f"  {i+1}. {f.name}")

    try:
        # 使用第一個文件作為主文檔
        master_doc = Document(docx_files[0])
        composer = Composer(master_doc)

        # 從第二個文件開始，將其內容追加到主文檔
        for i, file_path in enumerate(docx_files[1:]):
            print(f"  📄 正在追加: {file_path.name}")
            
            # 在追加下一個文檔內容前，先插入一個分頁符
            # 注意：docxcompose的append會保留源文檔的末尾分節符，
            # 這通常表現為分頁。如果需要強制分頁，可以手動添加。
            if i > 0: # 實際上，Composer會處理好分節
                pass
            
            sub_doc = Document(file_path)
            composer.append(sub_doc)

        # 確定輸出文件名
        if output_file is None:
            output_file = input_path.parent / f"{input_path.name}_merged.docx"
        
        # 保存合併後的文檔
        composer.save(output_file)
        print(f"\n✅ 合併成功！文件已保存至 -> {os.path.abspath(output_file)}")
        return True

    except ImportError:
        print("\n❌ 錯誤：缺少 'docxcompose' 庫。")
        print("   請運行安裝腳本 install.sh 或 install.bat, 或手動執行:")
        print("   pip install docxcompose")
        return False
    except Exception as e:
        print(f"\n❌ 合併過程中出錯: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="將文件夾中的多個 .docx 文件合併成一個單一文件。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 將 'my_project_split' 文件夾中的所有docx合併
  python merge_docx.py my_project_split

  # 合併並指定輸出文件名
  python merge_docx.py my_project_split -o final_document.docx
        """
    )
    
    parser.add_argument(
        'input_dir',
        help='包含待合併 .docx 文件的文件夾路徑。'
    )
    
    parser.add_argument(
        '-o', '--output-file',
        help='輸出文件的路徑（可選，默認在輸入文件夾的同級目錄生成 [文件夾名]_merged.docx）。'
    )
    
    args = parser.parse_args()
    
    merge_docx_files(args.input_dir, args.output_file)


if __name__ == "__main__":
    main() 