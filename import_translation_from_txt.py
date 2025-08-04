#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import os
import os.path as osp
import argparse
import re
from pathlib import Path

# 定義解析TXT譯文的正規表達式模式
page_start_pattern = re.compile(r'^###\s+', re.MULTILINE)
text_blkid_start_pattern = re.compile(r'^\d+\.', re.MULTILINE)


def parse_txt_translation(file_path: str):
    """解析TXT譯文文件，返回頁面和文本塊列表"""
    with open(file_path, 'r', encoding='utf8') as f:
        content = f.read()
    
    page_start = None
    page_list = []
    
    # 找到所有頁面開始位置
    for matched in page_start_pattern.finditer(content):
        start, end = matched.span()
        if page_start is not None:
            page_list.append({'page_content': content[page_start: start]})
        page_start = start
    
    if page_start is not None:
        page_list.append({'page_content': content[page_start:]})

    # 解析每個頁面的內容
    for page_dict in page_list:
        page_content = page_dict['page_content']
        page_dict['page_name'] = page_start_pattern.sub('', page_content.split('\n')[0]).strip()
        
        blkid_start = blkid_end = None
        blk_list = []
        
        # 找到所有文本塊
        for matched in text_blkid_start_pattern.finditer(page_content):
            start, end = matched.span()
            if blkid_start is not None:
                blk_list.append(page_content[blkid_end: start].strip())
            blkid_start = start
            blkid_end = end
        
        if blkid_start is not None:
            blk_list.append(page_content[blkid_end:].strip())
        
        page_dict['blk_list'] = blk_list

    return page_list


def load_translation_from_txt(proj_data: dict, file_path: str):
    """從TXT文件載入譯文到項目數據中"""
    page_list = parse_txt_translation(file_path)
    missing_pages = []
    unmatched_pages = []
    unexpected_pages = []
    matched_pages = []
    
    pages = proj_data.get('pages', {})
    
    for page_dict in page_list:
        page_name = page_dict['page_name']
        if page_name in pages:
            matched_pages.append(page_name)
        else:
            unexpected_pages.append(page_name)
            print(f"警告：在項目中找不到頁面 '{page_name}'")
            continue
        
        blklist = pages[page_name]
        n_blk = len(blklist)
        src_blk_list = page_dict['blk_list']
        n_src_blk = len(src_blk_list)
        
        if n_src_blk != n_blk:
            print(f"警告：頁面 '{page_name}' 的文本塊數量不匹配 - 項目中有{n_blk}個，TXT文件中有{n_src_blk}個")
            unmatched_pages.append(page_name)
        
        # 將譯文應用到文本塊
        for blkid in range(min(n_blk, n_src_blk)):
            blk = blklist[blkid]
            blk['rich_text'] = ''  # 清空富文本
            blk['translation'] = src_blk_list[blkid]
    
    matched_pages = set(matched_pages)
    if len(matched_pages) != len(pages):
        for page_name in pages:
            if page_name not in matched_pages:
                missing_pages.append(page_name)
    
    all_matched = len(missing_pages) == 0 and len(unmatched_pages) == 0 and len(unexpected_pages) == 0
    return all_matched, {
        'missing_pages': missing_pages, 
        'unmatched_pages': unmatched_pages, 
        'unexpected_pages': unexpected_pages, 
        'matched_pages': matched_pages
    }


def main():
    parser = argparse.ArgumentParser(description='從TXT文件導入譯文到JSON項目文件')
    parser.add_argument('json_file', help='輸入的JSON項目文件路徑 (例如: xx.json)')
    parser.add_argument('txt_file', nargs='?', help='包含譯文的TXT文件路徑 (可選，默認根據JSON文件名自動生成)')
    parser.add_argument('--output', '-o', help='輸出JSON文件名（可選，默認為zs_imported_translate_原文件名.json）')
    
    args = parser.parse_args()
    
    json_file = args.json_file
    txt_file = args.txt_file
    
    # 檢查JSON文件是否存在
    if not osp.exists(json_file):
        print(f"錯誤：JSON文件 '{json_file}' 不存在")
        sys.exit(1)
    
    # 如果沒有指定TXT文件，根據JSON文件名自動生成
    if txt_file is None:
        json_path = Path(json_file)
        json_dir = json_path.parent
        json_stem = json_path.stem  # 例如: imgtrans_41
        # 根據規律生成: deepseek_imgtrans_41_source.txt
        txt_file = json_dir / f"deepseek_{json_stem}_source.txt"
        print(f"自動生成TXT文件路徑：{txt_file}")
    
    # 檢查TXT文件是否存在
    if not osp.exists(str(txt_file)):
        print(f"錯誤：TXT文件 '{txt_file}' 不存在")
        sys.exit(1)
    
    # 生成輸出文件名
    if args.output:
        output_file = args.output
    else:
        json_path = Path(json_file)
        json_dir = json_path.parent
        json_basename = json_path.stem
        output_file = json_dir / f"zs_imported_translate_{json_basename}.json"
    
    try:
        # 載入JSON項目文件
        print(f"正在載入項目文件：{json_file}")
        with open(json_file, 'r', encoding='utf8') as f:
            proj_data = json.load(f)
        
        # 從TXT文件導入譯文
        print(f"正在從TXT文件導入譯文：{txt_file}")
        all_matched, match_rst = load_translation_from_txt(proj_data, str(txt_file))
        
        # 保存新的JSON文件
        print(f"正在保存到：{output_file}")
        with open(str(output_file), 'w', encoding='utf8') as f:
            json.dump(proj_data, f, ensure_ascii=False, indent=2)
        
        # 顯示導入結果
        if all_matched:
            print("✓ 譯文導入並匹配成功")
        else:
            print("⚠ 譯文導入完成，但存在部分不匹配：")
            if match_rst['missing_pages']:
                print(f"  缺失的頁面：{', '.join(match_rst['missing_pages'])}")
            if match_rst['unexpected_pages']:
                print(f"  意外的頁面：{', '.join(match_rst['unexpected_pages'])}")
            if match_rst['unmatched_pages']:
                print(f"  不匹配的頁面：{', '.join(match_rst['unmatched_pages'])}")
        
        print(f"✓ 成功生成：{output_file}")
        
    except json.JSONDecodeError as e:
        print(f"錯誤：JSON文件格式不正確 - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"錯誤：{e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 