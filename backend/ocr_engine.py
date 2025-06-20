import cv2
import numpy as np
import pandas as pd
from PIL import Image
import pytesseract
from paddleocr import PaddleOCR
import easyocr
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import os
import logging
import re
from typing import List, Dict, Any, Tuple
import json

logger = logging.getLogger(__name__)

class OCREngine:
    def __init__(self):
        """Initialize OCR engines with multiple backends for redundancy and accuracy."""
        self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        self.easy_ocr = easyocr.Reader(['en'])
        
        # Configure Tesseract
        pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
        
        # OCR confidence thresholds
        self.confidence_threshold = 0.7
        self.min_text_length = 2
        
        # Text cleaning patterns
        self.cleaning_patterns = [
            (r'[^\w\s\-\.\,\;\:\!\?\(\)\[\]\{\}\/\+\=\*\&\^\%\$\#\@]', ''),  # Remove special chars
            (r'\s+', ' '),  # Normalize whitespace
            (r'^\s+|\s+$', ''),  # Trim whitespace
        ]
    
    def process_document(self, filepath: str, options: Dict = None) -> Dict[str, Any]:
        """Process document with multiple OCR engines and combine results."""
        options = options or {}
        
        # Convert PDF to images if needed
        if filepath.lower().endswith('.pdf'):
            images = self._pdf_to_images(filepath)
        else:
            images = [cv2.imread(filepath)]
        
        all_results = []
        
        for page_num, image in enumerate(images):
            logger.info(f"Processing page {page_num + 1}")
            
            # Run multiple OCR engines
            paddle_results = self._run_paddle_ocr(image)
            easy_results = self._run_easy_ocr(image)
            tesseract_results = self._run_tesseract(image)
            
            # Combine and validate results
            combined_results = self._combine_ocr_results(
                paddle_results, easy_results, tesseract_results, page_num
            )
            
            # Post-process and clean text
            processed_results = self._post_process_results(combined_results)
            
            all_results.append({
                'page': page_num + 1,
                'results': processed_results,
                'image_shape': image.shape
            })
        
        return {
            'document_path': filepath,
            'total_pages': len(all_results),
            'pages': all_results
        }
    
    def _pdf_to_images(self, pdf_path: str) -> List[np.ndarray]:
        """Convert PDF to list of images."""
        try:
            # Try pdf2image first
            images = convert_from_path(pdf_path, dpi=300)
            return [np.array(img) for img in images]
        except Exception as e:
            logger.warning(f"pdf2image failed: {e}, trying PyMuPDF")
            try:
                # Fallback to PyMuPDF
                doc = fitz.open(pdf_path)
                images = []
                for page in doc:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_data = pix.tobytes("png")
                    img = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
                    images.append(img)
                doc.close()
                return images
            except Exception as e2:
                logger.error(f"PDF conversion failed: {e2}")
                raise
    
    def _run_paddle_ocr(self, image: np.ndarray) -> List[Dict]:
        """Run PaddleOCR on image."""
        try:
            results = self.paddle_ocr.ocr(image, cls=True)
            processed_results = []
            
            if results and results[0]:
                for line in results[0]:
                    if line and len(line) >= 2:
                        bbox, (text, confidence) = line
                        if confidence >= self.confidence_threshold and len(text.strip()) >= self.min_text_length:
                            processed_results.append({
                                'text': text.strip(),
                                'confidence': confidence,
                                'bbox': bbox,
                                'engine': 'paddle'
                            })
            
            return processed_results
        except Exception as e:
            logger.error(f"PaddleOCR error: {e}")
            return []
    
    def _run_easy_ocr(self, image: np.ndarray) -> List[Dict]:
        """Run EasyOCR on image."""
        try:
            results = self.easy_ocr.readtext(image)
            processed_results = []
            
            for (bbox, text, confidence) in results:
                if confidence >= self.confidence_threshold and len(text.strip()) >= self.min_text_length:
                    processed_results.append({
                        'text': text.strip(),
                        'confidence': confidence,
                        'bbox': bbox,
                        'engine': 'easy'
                    })
            
            return processed_results
        except Exception as e:
            logger.error(f"EasyOCR error: {e}")
            return []
    
    def _run_tesseract(self, image: np.ndarray) -> List[Dict]:
        """Run Tesseract OCR on image."""
        try:
            # Preprocess image for better OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Get detailed OCR data
            data = pytesseract.image_to_data(denoised, output_type=pytesseract.Output.DICT)
            
            processed_results = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                conf = int(data['conf'][i])
                
                if conf > 0 and len(text) >= self.min_text_length:
                    # Calculate confidence as percentage
                    confidence = conf / 100.0
                    
                    if confidence >= self.confidence_threshold:
                        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                        bbox = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
                        
                        processed_results.append({
                            'text': text,
                            'confidence': confidence,
                            'bbox': bbox,
                            'engine': 'tesseract'
                        })
            
            return processed_results
        except Exception as e:
            logger.error(f"Tesseract error: {e}")
            return []
    
    def _combine_ocr_results(self, paddle_results: List[Dict], easy_results: List[Dict], 
                           tesseract_results: List[Dict], page_num: int) -> List[Dict]:
        """Combine results from multiple OCR engines with voting mechanism."""
        all_results = paddle_results + easy_results + tesseract_results
        
        # Group results by spatial proximity
        grouped_results = self._group_by_proximity(all_results)
        
        # Vote on text for each group
        final_results = []
        for group in grouped_results:
            if len(group) >= 2:  # At least 2 engines agree
                best_result = self._select_best_result(group)
                if best_result:
                    final_results.append(best_result)
            elif len(group) == 1:  # Single engine result with high confidence
                result = group[0]
                if result['confidence'] > 0.85:
                    final_results.append(result)
        
        return final_results
    
    def _group_by_proximity(self, results: List[Dict], threshold: float = 0.1) -> List[List[Dict]]:
        """Group OCR results by spatial proximity."""
        if not results:
            return []
        
        groups = []
        used = set()
        
        for i, result1 in enumerate(results):
            if i in used:
                continue
            
            group = [result1]
            used.add(i)
            
            for j, result2 in enumerate(results):
                if j in used:
                    continue
                
                if self._are_bboxes_close(result1['bbox'], result2['bbox'], threshold):
                    group.append(result2)
                    used.add(j)
            
            groups.append(group)
        
        return groups
    
    def _are_bboxes_close(self, bbox1: List, bbox2: List, threshold: float) -> bool:
        """Check if two bounding boxes are close to each other."""
        try:
            # Calculate center points
            center1 = np.mean(bbox1, axis=0)
            center2 = np.mean(bbox2, axis=0)
            
            # Calculate distance
            distance = np.linalg.norm(center1 - center2)
            
            # Normalize by image size (approximate)
            max_distance = 1000  # reasonable threshold
            return distance < max_distance * threshold
        except:
            return False
    
    def _select_best_result(self, group: List[Dict]) -> Dict:
        """Select the best result from a group based on confidence and text quality."""
        if not group:
            return None
        
        # Sort by confidence
        sorted_group = sorted(group, key=lambda x: x['confidence'], reverse=True)
        
        # Check for text consistency
        texts = [result['text'] for result in sorted_group]
        if len(set(texts)) == 1:  # All engines agree on text
            return sorted_group[0]
        
        # If texts differ, choose the one with highest confidence
        return sorted_group[0]
    
    def _post_process_results(self, results: List[Dict]) -> List[Dict]:
        """Post-process and clean OCR results."""
        processed_results = []
        
        for result in results:
            cleaned_text = self._clean_text(result['text'])
            if cleaned_text and len(cleaned_text) >= self.min_text_length:
                result['text'] = cleaned_text
                processed_results.append(result)
        
        return processed_results
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        
        # Apply cleaning patterns
        for pattern, replacement in self.cleaning_patterns:
            text = re.sub(pattern, replacement, text)
        
        return text.strip()
    
    def extract_table_data(self, ocr_results: Dict, table_region: Dict) -> List[List[str]]:
        """Extract table data from OCR results within a specific region."""
        table_data = []
        
        # Get all text elements within the table region
        table_texts = []
        for page in ocr_results['pages']:
            for result in page['results']:
                if self._is_text_in_region(result['bbox'], table_region['bbox']):
                    table_texts.append(result)
        
        # Sort texts by position (top to bottom, left to right)
        sorted_texts = sorted(table_texts, key=lambda x: (x['bbox'][0][1], x['bbox'][0][0]))
        
        # Group into rows and columns
        table_data = self._organize_into_table(sorted_texts, table_region)
        
        return table_data
    
    def _is_text_in_region(self, text_bbox: List, region_bbox: List) -> bool:
        """Check if text bounding box is within the specified region."""
        try:
            text_center = np.mean(text_bbox, axis=0)
            region_center = np.mean(region_bbox, axis=0)
            
            # Simple overlap check
            return (text_center[0] >= region_bbox[0][0] and 
                   text_center[0] <= region_bbox[2][0] and
                   text_center[1] >= region_bbox[0][1] and 
                   text_center[1] <= region_bbox[2][1])
        except:
            return False
    
    def _organize_into_table(self, texts: List[Dict], table_region: Dict) -> List[List[str]]:
        """Organize text elements into a table structure."""
        if not texts:
            return []
        
        # Detect rows and columns
        rows = self._detect_rows(texts, table_region)
        
        # Organize into table
        table = []
        for row in rows:
            table_row = []
            for text in row:
                table_row.append(text['text'])
            table.append(table_row)
        
        return table
    
    def _detect_rows(self, texts: List[Dict], table_region: Dict) -> List[List[Dict]]:
        """Detect rows in the table based on vertical alignment."""
        if not texts:
            return []
        
        # Sort by y-coordinate
        sorted_texts = sorted(texts, key=lambda x: x['bbox'][0][1])
        
        rows = []
        current_row = []
        row_threshold = 20  # pixels
        
        for text in sorted_texts:
            if not current_row:
                current_row = [text]
            else:
                # Check if text is in the same row
                y_diff = abs(text['bbox'][0][1] - current_row[0]['bbox'][0][1])
                if y_diff <= row_threshold:
                    current_row.append(text)
                else:
                    # Sort current row by x-coordinate
                    current_row.sort(key=lambda x: x['bbox'][0][0])
                    rows.append(current_row)
                    current_row = [text]
        
        # Add last row
        if current_row:
            current_row.sort(key=lambda x: x['bbox'][0][0])
            rows.append(current_row)
        
        return rows
    
    def generate_preview(self, filepath: str, page_number: int = 1) -> Dict[str, Any]:
        """Generate preview of OCR results for a specific page."""
        try:
            # Convert PDF to image if needed
            if filepath.lower().endswith('.pdf'):
                images = self._pdf_to_images(filepath)
                if page_number <= len(images):
                    image = images[page_number - 1]
                else:
                    return {'error': 'Page number out of range'}
            else:
                image = cv2.imread(filepath)
            
            # Run OCR on the page
            paddle_results = self._run_paddle_ocr(image)
            easy_results = self._run_easy_ocr(image)
            tesseract_results = self._run_tesseract(image)
            
            # Combine results
            combined_results = self._combine_ocr_results(
                paddle_results, easy_results, tesseract_results, page_number - 1
            )
            
            # Post-process
            processed_results = self._post_process_results(combined_results)
            
            return {
                'page': page_number,
                'total_text_elements': len(processed_results),
                'text_elements': processed_results[:50],  # Limit preview
                'image_shape': image.shape
            }
        
        except Exception as e:
            logger.error(f"Preview generation error: {e}")
            return {'error': str(e)} 