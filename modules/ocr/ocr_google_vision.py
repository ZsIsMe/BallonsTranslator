import re
import time
import base64
import json
import cv2
import numpy as np
from typing import List
import httpx

from .base import register_OCR, OCRBase, TextBlock

import logging
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)


@register_OCR('google_vision')
class OCRGoogleVisionAPI(OCRBase):
    params = {
        'api_key': '',
        'language_hints': {
            'value': '',
            'description': 'Language codes separated by commas (BCP-47)'
        },
        'proxy': {
            'value': '',
            'description': 'Proxy address (e.g., http(s)://user:password@host:port or socks4/5://user:password@host:port)'
        },
        'delay': 0.0,
        'newline_handling': {
            'type': 'selector',
            'options': [
                'preserve',
                'remove'
            ],
            'value': 'preserve',
            'description': 'Choose how to handle newline characters in OCR results'
        },
        'no_uppercase': {
            'type': 'checkbox',
            'value': False,
            'description': 'Convert text to lowercase except the first letter of each sentence'
        },
        'description': 'OCR using Google Vision API'
    }

    @property
    def request_delay(self):
        try:
            return float(self.get_param_value('delay'))
        except (ValueError, TypeError):
            return 1.0

    @property
    def language_hints(self):
        hints = self.get_param_value('language_hints')
        return [hint.strip() for hint in hints.split(",")] if hints else None

    @property
    def api_key(self):
        return self.get_param_value('api_key')

    @property
    def proxy(self):
        return self.get_param_value('proxy')

    @property
    def newline_handling(self):
        return self.get_param_value('newline_handling')

    @property
    def no_uppercase(self):
        return self.get_param_value('no_uppercase')

    def __init__(self, **params) -> None:
        if 'delay' in params:
            try:
                params['delay'] = float(params['delay'])
            except (ValueError, TypeError):
                params['delay'] = 1.0  
        super().__init__(**params)
        self.proxy_url = self.proxy  
        self.last_request_time = 0

    def send_to_google_vision(self, image_buffer: bytes):
        VISION_API_URL = f"https://vision.googleapis.com/v1/images:annotate?key={self.api_key}"

        image_content = base64.b64encode(image_buffer).decode("utf-8")

        request_body = {
            "requests": [
                {
                    "image": {
                        "content": image_content
                    },
                    "features": [
                        {
                            "type": "DOCUMENT_TEXT_DETECTION"
                        }
                    ]
                }
            ]
        }

        if self.language_hints:
            request_body["requests"][0]["imageContext"] = {
                "languageHints": self.language_hints
            }

        headers = {
            "Content-Type": "application/json"
        }

        client_kwargs = {'headers': headers} 
        # 只有當 proxy_url 是有效的非空字符串時才使用代理
        proxy_url = self.proxy_url.strip() if self.proxy_url else ''
        if proxy_url: 
            mounts = {}
            if proxy_url.startswith(('http://', 'https://', 'socks4://', 'socks5://')): 
                mounts["all://"] = httpx.HTTPTransport(proxy=proxy_url) 
                client_kwargs['mounts'] = mounts
            else:
                self.logger.warning("The proxy URL does not contain a schema (http://, https://, socks4://, socks5://). Proxy will be ignored.") 

        with httpx.Client(**client_kwargs) as client: 
            try:
                if self.debug_mode:
                    proxy_info = self.proxy_url if self.proxy_url else "No proxy"
                    self.logger.debug(f"Sending request to Google Vision API with proxy: {proxy_info}")

                response = client.post(VISION_API_URL, headers=headers, json=request_body)
                response.raise_for_status() 

                return response.json()
            except httpx.HTTPError as e:
                raise Exception(f"Error during request to Google Vision API: {e}")

    def extract_text_and_coordinates(self, annotations):
        text_with_coords = []
        for annotation in annotations:
            if 'description' in annotation:
                words = annotation.get('description', '').split()
                vertices = annotation.get('boundingPoly', {}).get('vertices', [])
                text_with_coords.append({
                    "text": annotation['description'],
                    "coordinates": [(v.get("x", 0), v.get("y", 0)) for v in vertices]
                })
        return text_with_coords

    def extract_full_text(self, response_json):
        try:
            return response_json['responses'][0]['fullTextAnnotation']['text']
        except (IndexError, KeyError, TypeError):
            return "Full text not found or not recognized"

    def calculate_font_size(self, response_json, is_vertical: bool = False) -> float:
        """
        從 DOCUMENT_TEXT_DETECTION 結果計算字體大小
        
        通過提取每個字符的邊界框，計算字符高度（或垂直文本的寬度）的中位數
        
        Args:
            response_json: Google Vision API 返回的 JSON
            is_vertical: 是否為垂直文本
            
        Returns:
            float: 估算的字體大小（像素），失敗返回 -1
        """
        try:
            full_text_annotation = response_json['responses'][0].get('fullTextAnnotation')
            if not full_text_annotation:
                if self.debug_mode:
                    self.logger.debug('No fullTextAnnotation in response, cannot calculate font size')
                return -1
            pages = full_text_annotation.get('pages', [])
            if not pages:
                if self.debug_mode:
                    self.logger.debug('No pages in fullTextAnnotation')
                return -1
        except (KeyError, IndexError, TypeError) as e:
            if self.debug_mode:
                self.logger.debug(f'Error accessing response structure: {e}')
            return -1
        
        char_sizes = []
        char_count = 0
        # 需要過濾的標點符號（這些字符通常較小，會影響估算）
        punctuation = set('。、！？…「」『』（）【】〈〉《》,.!?\'"()[]{}<>·-—')
        
        for page in pages:
            for block in page.get('blocks', []):
                for paragraph in block.get('paragraphs', []):
                    for word in paragraph.get('words', []):
                        for symbol in word.get('symbols', []):
                            char_count += 1
                            text = symbol.get('text', '')
                            
                            # 跳過標點符號
                            if text in punctuation or not text.strip():
                                continue
                            
                            bbox = symbol.get('boundingBox', {})
                            vertices = bbox.get('vertices', [])
                            
                            if len(vertices) < 4:
                                continue
                            
                            # 計算字符尺寸
                            xs = [v.get('x', 0) for v in vertices]
                            ys = [v.get('y', 0) for v in vertices]
                            
                            width = max(xs) - min(xs)
                            height = max(ys) - min(ys)
                            
                            # 根據文字方向選擇尺寸
                            # 垂直文本：用寬度；水平文本：用高度
                            char_size = width if is_vertical else height
                            
                            # 過濾不合理的尺寸（太小可能是噪點，太大可能是錯誤）
                            if 8 < char_size < 500:
                                char_sizes.append(char_size)
        
        if self.debug_mode:
            self.logger.debug(f'Font size calculation: {char_count} total chars, {len(char_sizes)} valid chars')
        
        if not char_sizes:
            return -1
        
        # 使用中位數更穩定，避免極端值影響
        return float(np.median(char_sizes))

    def process_image(self, image_buffer: bytes):
        response = self.send_to_google_vision(image_buffer)
        full_text = self.extract_full_text(response)

        return {
            'full_text': full_text,
            'language': response['responses'][0].get('language', 'und'),
            'text_with_coordinates': self.extract_text_and_coordinates(response.get("responses", [{}])[0].get("textAnnotations", []))
        }

    def format_ocr_result(self, result):
        formatted_result = {
            "language": result.get("language", ""),
            "full_text": result.get("full_text", ""),
            "text_with_coordinates": [
                f"{item['text']}: {item['coordinates']}"
                for item in result.get("text_with_coordinates", [])
            ]
        }
        return json.dumps(formatted_result, indent=4, ensure_ascii=False)

    def _ocr_blk_list(self, img: np.ndarray, blk_list: List[TextBlock], *args, **kwargs):
        im_h, im_w = img.shape[:2]
        if self.debug_mode:
            self.logger.debug(f'Image dimensions: {im_h}x{im_w}')
        for blk in blk_list:
            x1, y1, x2, y2 = blk.xyxy
            if self.debug_mode:
                self.logger.debug(f'Processing block: ({x1}, {y1}, {x2}, {y2})')
            if y2 < im_h and x2 < im_w and x1 >= 0 and y1 >= 0 and x1 < x2 and y1 < y2:
                cropped_img = img[y1:y2, x1:x2]
                if self.debug_mode:
                    self.logger.debug(f'Cropped image dimensions: {cropped_img.shape}')
                
                # 調用 OCR 並同時計算字體大小
                # 注意：blk.vertical 可能是 None，需要轉換為 bool
                is_vertical = bool(blk.vertical) if blk.vertical is not None else False
                text, font_size = self.ocr_with_font_size(cropped_img, is_vertical=is_vertical)
                blk.text = text
                
                # 如果成功計算出字體大小，設置到 TextBlock
                if font_size > 0:
                    blk._detected_font_size = font_size
                    blk.font_size = font_size
                    if self.debug_mode:
                        self.logger.debug(f'Detected font size: {font_size:.1f}px')
            else:
                if self.debug_mode:
                    self.logger.warning('Invalid text block coordinates')
                blk.text = ''

    def ocr_with_font_size(self, img: np.ndarray, is_vertical: bool = False) -> tuple:
        """
        執行 OCR 並同時計算字體大小
        
        Args:
            img: 輸入圖片
            is_vertical: 是否為垂直文本
            
        Returns:
            tuple: (識別的文本, 字體大小)，字體大小失敗時為 -1
        """
        if self.debug_mode:
            self.logger.debug(f'Starting OCR with font size detection on image of shape: {img.shape}')
        
        self._respect_delay()
        
        try:
            if img.size == 0:
                if self.debug_mode:
                    self.logger.warning('Empty image for OCR')
                return '', -1
            
            _, buffer = cv2.imencode('.jpg', img)
            response = self.send_to_google_vision(buffer.tobytes())
            
            # 提取文本
            full_text = self.extract_full_text(response)
            
            ignore_texts = ['Full text not found or not recognized']
            if full_text in ignore_texts:
                return '', -1
            
            # 處理文本
            if self.newline_handling == 'remove':
                full_text = full_text.replace('\n', ' ')
            full_text = self._apply_punctuation_and_spacing(full_text)
            if self.no_uppercase:
                full_text = self._apply_no_uppercase(full_text)
            
            # 計算字體大小
            font_size = self.calculate_font_size(response, is_vertical=is_vertical)
            
            if self.debug_mode:
                self.logger.debug(f'OCR result: {full_text[:100]}..., font_size: {font_size}')
            
            return full_text, font_size
            
        except Exception as e:
            if self.debug_mode:
                self.logger.error(f"OCR error: {str(e)}")
            return '', -1

    def ocr_img(self, img: np.ndarray) -> str:
        return self.ocr(img)

    def ocr(self, img: np.ndarray) -> str:
        if self.debug_mode:
            self.logger.debug(f'Starting OCR on image of shape: {img.shape}')
        self._respect_delay()
        try:
            if img.size > 0:
                if self.debug_mode:
                    self.logger.debug(f'Input image size: {img.shape}')
                _, buffer = cv2.imencode('.jpg', img)
                result = self.process_image(buffer.tobytes())
                if self.debug_mode:
                    formatted_result = self.format_ocr_result(result)
                    self.logger.debug(f'OCR result: {formatted_result}')

                ignore_texts = [
                    'Full text not found or not recognized'
                ]
                if result['full_text'] in ignore_texts:
                    return ''
                full_text = result['full_text']
                if self.newline_handling == 'remove':
                    full_text = full_text.replace('\n', ' ')

                full_text = self._apply_punctuation_and_spacing(full_text)

                if self.no_uppercase:
                    full_text = self._apply_no_uppercase(full_text)

                return full_text
            else:
                if self.debug_mode:
                    self.logger.warning('Empty image for OCR')
                return ''
        except Exception as e:
            if self.debug_mode:
                self.logger.error(f"OCR error: {str(e)}")
            return ''

    def _apply_no_uppercase(self, text: str) -> str:
        def process_sentence(sentence):
            words = sentence.split()
            if not words:
                return ''
            processed = [words[0].capitalize()] + [word.lower() for word in words[1:]]
            return ' '.join(processed)

        sentences = re.split(r'(?<=[.!?…])\s+', text)
        processed_sentences = [process_sentence(sentence) for sentence in sentences]

        return ' '.join(processed_sentences)

    def _apply_punctuation_and_spacing(self, text: str) -> str:
        text = re.sub(r'\s+([,.!?…])', r'\1', text)
        text = re.sub(r'([,.!?…])(?!\s)(?![,.!?…])', r'\1 ', text)
        text = re.sub(r'([,.!?…])\s+([,.!?…])', r'\1\2', text)
        return text.strip()

    def _respect_delay(self):
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if self.debug_mode:
            self.logger.info(f'Time since last request: {time_since_last_request} seconds')

        if time_since_last_request < self.request_delay:
            sleep_time = self.request_delay - time_since_last_request
            if self.debug_mode:
                self.logger.info(f'Waiting {sleep_time} seconds before next request')
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def updateParam(self, param_key: str, param_content):
        if param_key == 'delay':
            try:
                param_content = float(param_content)
            except (ValueError, TypeError):
                param_content = 1.0
        super().updateParam(param_key, param_content)
        if param_key == 'proxy':
            self.proxy_url = param_content 