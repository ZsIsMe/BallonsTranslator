#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BallonTranslator Word文檔分割腳本
專門用於分割BallonTranslator導出的Word文檔，每個圖片頁面生成一個獨立的docx文件
"""

import os
import sys
import re
import argparse
import shutil
import docx2txt
from pathlib import Path
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH


def split_ballontranslator_docx(input_docx, output_dir=None):
    """
    分割BallonTranslator導出的Word文檔
    
    Args:
        input_docx: 輸入的Word文檔路徑
        output_dir: 輸出目錄（可選）
    """
    # 檢查輸入文件
    if not os.path.exists(input_docx):
        print(f"錯誤：找不到文件 {input_docx}")
        return False
    
    # 設置輸出目錄
    if output_dir is None:
        input_path = Path(input_docx)
        output_dir = input_path.parent / f"{input_path.stem}_split"
    
    # 創建輸出目錄
    os.makedirs(output_dir, exist_ok=True)
    
    # 創建臨時圖片目錄
    image_temp_dir = Path(output_dir) / "temp_images"
    if image_temp_dir.exists():
        shutil.rmtree(image_temp_dir)
    os.makedirs(image_temp_dir, exist_ok=True)
    
    print(f"正在處理BallonTranslator文檔: {input_docx}")
    print(f"輸出目錄: {output_dir}")
    
    try:
        # 步驟1: 提取所有圖片到臨時文件夾
        print(f"🖼️ 正在提取圖片至: {image_temp_dir}")
        docx2txt.process(input_docx, image_temp_dir)
        
        # 讀取Word文檔
        doc = Document(input_docx)
        
        pages = []
        current_page = None
        table_index = 0
        
        # 解析文檔內容
        for element in doc.element.body:
            if element.tag.endswith('p'):  # 段落
                text = ''.join(run.text for run in element.findall('.//w:t', {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})).strip()
                
                # 檢查是否為頁面標題（通常是圖片文件名）
                if text and not current_page:
                    current_page = {'title': text, 'table_index': -1}
                    print(f"發現頁面: {text}")
                
            elif element.tag.endswith('tbl'):  # 表格
                if current_page:
                    current_page['table_index'] = table_index
                    pages.append(current_page)
                    current_page = None
                    table_index += 1
        
        if not pages:
            print("警告：未找到任何可分割的頁面內容")
            return False
        
        print(f"找到 {len(pages)} 個頁面")
        
        # 步驟2: 為每個頁面創建獨立文檔並插入圖片
        generated_files = []
        image_counter = 1  # docx2txt提取的圖片從 image1.jpeg 開始
        for i, page_info in enumerate(pages):
            source_table = doc.tables[page_info['table_index']]
            output_path, num_images_in_table = create_page_docx(
                page_info, output_dir, i + 1, source_table, image_temp_dir, image_counter
            )
            image_counter += num_images_in_table
            generated_files.append(output_path)
        
        # 生成摘要信息
        create_summary(input_docx, output_dir, pages, generated_files)
        
        print(f"\n✅ 分割完成！共生成 {len(generated_files)} 個文件")
        print(f"📁 輸出目錄: {output_dir}")
        
        return True
        
    except Exception as e:
        print(f"處理過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理臨時文件夾
        if image_temp_dir.exists():
            print(f"🗑️ 正在清理臨時文件: {image_temp_dir}")
            shutil.rmtree(image_temp_dir)


def create_page_docx(page_info, output_dir, page_index, source_table, image_dir, image_start_index):
    """
    為單個頁面創建獨立的Word文檔，並盡力保持原始格式
    """
    doc = Document()
    
    # 步驟1: 嚴格遵循 dump_doc 的樣式設置
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Arial'

    # 步驟2: 添加頁面標題，格式與 dump_doc 保持一致
    paragraph = doc.add_paragraph(page_info['title'])
    paragraph.style = doc.styles['Normal']
    
    # 步驟3: 重建表格
    new_table = doc.add_table(rows=len(source_table.rows), cols=len(source_table.columns), style='Table Grid')
    images_processed = 0
    
    for i, row in enumerate(source_table.rows):
        for j, cell in enumerate(row.cells):
            new_cell = new_table.cell(i, j)
            # 檢查單元格中是否有圖片
            if len(cell._element.findall('.//pic:pic', {'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture'})) > 0:
                img_path_found = None
                img_idx = image_start_index + images_processed
                for ext in ['.jpeg', '.jpg', '.png', '.gif', '.bmp']:
                    p = Path(image_dir) / f"image{img_idx}{ext}"
                    if p.exists():
                        img_path_found = p
                        break
                
                if img_path_found:
                    # 清空單元格默認段落並插入圖片
                    new_cell.text = ''
                    run = new_cell.paragraphs[0].add_run()
                    try:
                        # 使用與原始dump_doc相近的默認寬度
                        run.add_picture(str(img_path_found), width=Inches(2.5))
                    except Exception as e:
                        new_cell.text = f"[圖片插入失敗: {e}]"
                    images_processed += 1
                else:
                    new_cell.text = f"[圖片 image{img_idx} 未找到]"
            else:
                # 複製文字內容
                new_cell.text = cell.text

    # 從頁面標題（通常是圖片文件名）中提取基本名稱
    base_filename, _ = os.path.splitext(page_info['title'])
    safe_title = re.sub(r'[<>:"/\\|?*]', '_', base_filename)
    
    if len(safe_title) > 50:
        safe_title = safe_title[:47] + "..."
    
    # 使用處理後的圖片名作為文件名，不再添加數字前綴
    output_filename = f"{safe_title}.docx"
    output_path = os.path.join(output_dir, output_filename)
    
    doc.save(output_path)
    print(f"  📄 已生成: {output_filename} (包含 {images_processed} 張圖片)")
    
    return output_path, images_processed


def create_summary(input_docx, output_dir, pages, generated_files):
    """
    創建分割摘要文件
    """
    summary_file = os.path.join(output_dir, "分割摘要.txt")
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("BallonTranslator Word文檔分割摘要\n")
        f.write("=" * 60 + "\n")
        f.write(f"原始文件: {os.path.basename(input_docx)}\n")
        f.write(f"原始路徑: {os.path.abspath(input_docx)}\n")
        f.write(f"分割時間: {Path(__file__).stat().st_mtime}\n")
        f.write(f"總頁面數: {len(pages)}\n\n")
        
        f.write("頁面列表:\n")
        f.write("-" * 40 + "\n")
        for i, page_info in enumerate(pages):
            f.write(f"{i+1:2d}. {page_info['title']}\n")
        
        f.write("\n生成的文件:\n")
        f.write("-" * 40 + "\n")
        for i, file_path in enumerate(generated_files):
            f.write(f"{i+1:2d}. {os.path.basename(file_path)}\n")
    
    print(f"  📋 摘要文件: 分割摘要.txt")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="將BallonTranslator導出的Word文檔按頁面分割成多個獨立文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python split_ballontranslator_docx.py your_document.docx
  python split_ballontranslator_docx.py your_document.docx -o output_folder

注意:
  - 此腳本專門針對BallonTranslator導出的Word文檔結構
  - 每個頁面會生成一個獨立的docx文件
  - 文件名格式: 001_頁面名稱.docx, 002_頁面名稱.docx, ...
        """
    )
    
    parser.add_argument(
        'input_docx',
        help='輸入的BallonTranslator Word文檔路徑'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        help='輸出目錄（可選，默認為原文件同目錄下的 [文件名]_split 文件夾）'
    )
    
    args = parser.parse_args()
    
    # 執行分割
    success = split_ballontranslator_docx(args.input_docx, args.output_dir)
    
    if success:
        print("\n🎉 分割操作成功完成！")
        sys.exit(0)
    else:
        print("\n💥 分割操作失敗！")
        sys.exit(1)


if __name__ == "__main__":
    main() 