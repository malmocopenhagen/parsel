import cv2
import numpy as np
from PIL import Image
import logging
from typing import List, Dict, Any, Tuple
import json

logger = logging.getLogger(__name__)

class TableDetector:
    def __init__(self):
        """Initialize table detection with multiple algorithms."""
        self.min_table_area = 1000  # Minimum area for table detection
        self.line_threshold = 0.1   # Threshold for line detection
        self.cell_threshold = 50    # Minimum cell size
        
        # Table detection parameters
        self.horizontal_kernel_length = 40
        self.vertical_kernel_length = 40
        self.kernel_iterations = 2
        
    def detect_tables(self, filepath: str, ocr_results: Dict) -> List[Dict]:
        """Detect tables in document using multiple methods."""
        try:
            # Load image
            if filepath.lower().endswith('.pdf'):
                # For PDFs, we'll use OCR results to infer table regions
                return self._detect_tables_from_ocr(ocr_results)
            else:
                image = cv2.imread(filepath)
                if image is None:
                    raise ValueError("Could not load image")
                
                return self._detect_tables_from_image(image, ocr_results)
        
        except Exception as e:
            logger.error(f"Table detection error: {e}")
            return []
    
    def _detect_tables_from_image(self, image: np.ndarray, ocr_results: Dict) -> List[Dict]:
        """Detect tables using computer vision techniques."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Method 1: Line-based detection
        line_tables = self._detect_tables_by_lines(gray)
        
        # Method 2: Contour-based detection
        contour_tables = self._detect_tables_by_contours(gray)
        
        # Method 3: OCR-based detection
        ocr_tables = self._detect_tables_from_ocr(ocr_results)
        
        # Combine and validate results
        all_tables = line_tables + contour_tables + ocr_tables
        validated_tables = self._validate_and_merge_tables(all_tables, image.shape)
        
        return validated_tables
    
    def _detect_tables_by_lines(self, gray: np.ndarray) -> List[Dict]:
        """Detect tables by finding horizontal and vertical lines."""
        tables = []
        
        try:
            # Create horizontal and vertical kernels
            horizontal_kernel = cv2.getStructuringElement(
                cv2.MORPH_RECT, (self.horizontal_kernel_length, 1)
            )
            vertical_kernel = cv2.getStructuringElement(
                cv2.MORPH_RECT, (1, self.vertical_kernel_length)
            )
            
            # Detect horizontal lines
            horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
            horizontal_lines = cv2.morphologyEx(horizontal_lines, cv2.MORPH_CLOSE, horizontal_kernel)
            
            # Detect vertical lines
            vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
            vertical_lines = cv2.morphologyEx(vertical_lines, cv2.MORPH_CLOSE, vertical_kernel)
            
            # Combine lines
            table_mask = cv2.add(horizontal_lines, vertical_lines)
            
            # Find contours
            contours, _ = cv2.findContours(
                table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            # Filter and process contours
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > self.min_table_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    tables.append({
                        'bbox': [[x, y], [x + w, y], [x + w, y + h], [x, y + h]],
                        'area': area,
                        'method': 'line_detection',
                        'confidence': min(area / 10000, 1.0)  # Normalize confidence
                    })
        
        except Exception as e:
            logger.error(f"Line-based table detection error: {e}")
        
        return tables
    
    def _detect_tables_by_contours(self, gray: np.ndarray) -> List[Dict]:
        """Detect tables by analyzing contours and their properties."""
        tables = []
        
        try:
            # Apply threshold
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < self.min_table_area:
                    continue
                
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check aspect ratio (tables are usually rectangular)
                aspect_ratio = w / h if h > 0 else 0
                if 0.2 < aspect_ratio < 5.0:  # Reasonable table aspect ratio
                    
                    # Check if contour has table-like properties
                    if self._has_table_properties(contour, gray):
                        tables.append({
                            'bbox': [[x, y], [x + w, y], [x + w, y + h], [x, y + h]],
                            'area': area,
                            'method': 'contour_detection',
                            'confidence': min(area / 10000, 1.0)
                        })
        
        except Exception as e:
            logger.error(f"Contour-based table detection error: {e}")
        
        return tables
    
    def _has_table_properties(self, contour: np.ndarray, gray: np.ndarray) -> bool:
        """Check if contour has properties typical of a table."""
        try:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Extract region
            region = gray[y:y+h, x:x+w]
            
            # Check for regular patterns (lines, grids)
            # Apply edge detection
            edges = cv2.Canny(region, 50, 150)
            
            # Count edge pixels
            edge_density = np.sum(edges > 0) / (w * h)
            
            # Check for horizontal and vertical lines
            horizontal_lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=50)
            vertical_lines = cv2.HoughLines(edges, 1, np.pi/2, threshold=50)
            
            # Table should have some structure
            has_structure = (horizontal_lines is not None and len(horizontal_lines) > 1) or \
                          (vertical_lines is not None and len(vertical_lines) > 1)
            
            return edge_density > 0.01 and has_structure
        
        except Exception as e:
            logger.error(f"Table property check error: {e}")
            return False
    
    def _detect_tables_from_ocr(self, ocr_results: Dict) -> List[Dict]:
        """Detect tables based on OCR text layout and patterns."""
        tables = []
        
        try:
            for page in ocr_results.get('pages', []):
                page_tables = self._detect_tables_in_page(page)
                tables.extend(page_tables)
        
        except Exception as e:
            logger.error(f"OCR-based table detection error: {e}")
        
        return tables
    
    def _detect_tables_in_page(self, page_data: Dict) -> List[Dict]:
        """Detect tables in a single page based on text layout."""
        tables = []
        
        try:
            results = page_data.get('results', [])
            if not results:
                return tables
            
            # Group text by spatial proximity
            text_groups = self._group_text_by_proximity(results)
            
            # Analyze each group for table-like patterns
            for group in text_groups:
                if self._is_table_like_group(group):
                    bbox = self._calculate_group_bbox(group)
                    tables.append({
                        'bbox': bbox,
                        'area': self._calculate_bbox_area(bbox),
                        'method': 'ocr_pattern',
                        'confidence': 0.8,
                        'text_count': len(group)
                    })
        
        except Exception as e:
            logger.error(f"Page table detection error: {e}")
        
        return tables
    
    def _group_text_by_proximity(self, results: List[Dict], threshold: int = 100) -> List[List[Dict]]:
        """Group text elements by spatial proximity."""
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
                
                if self._are_texts_close(result1, result2, threshold):
                    group.append(result2)
                    used.add(j)
            
            groups.append(group)
        
        return groups
    
    def _are_texts_close(self, text1: Dict, text2: Dict, threshold: int) -> bool:
        """Check if two text elements are close to each other."""
        try:
            bbox1 = text1['bbox']
            bbox2 = text2['bbox']
            
            # Calculate centers
            center1 = np.mean(bbox1, axis=0)
            center2 = np.mean(bbox2, axis=0)
            
            # Calculate distance
            distance = np.linalg.norm(center1 - center2)
            
            return distance < threshold
        except:
            return False
    
    def _is_table_like_group(self, group: List[Dict]) -> bool:
        """Check if a group of text elements forms a table-like pattern."""
        if len(group) < 4:  # Need at least 4 elements for a table
            return False
        
        try:
            # Check for regular spacing
            x_coords = [np.mean(text['bbox'], axis=0)[0] for text in group]
            y_coords = [np.mean(text['bbox'], axis=0)[1] for text in group]
            
            # Check for multiple rows and columns
            unique_x = len(set(round(x/10) for x in x_coords))  # Group by proximity
            unique_y = len(set(round(y/10) for y in y_coords))
            
            # Table should have multiple rows and columns
            return unique_x >= 2 and unique_y >= 2
        
        except Exception as e:
            logger.error(f"Table-like group check error: {e}")
            return False
    
    def _calculate_group_bbox(self, group: List[Dict]) -> List[List[float]]:
        """Calculate bounding box for a group of text elements."""
        if not group:
            return [[0, 0], [0, 0], [0, 0], [0, 0]]
        
        all_x = []
        all_y = []
        
        for text in group:
            bbox = text['bbox']
            for point in bbox:
                all_x.append(point[0])
                all_y.append(point[1])
        
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        return [[min_x, min_y], [max_x, min_y], [max_x, max_y], [min_x, max_y]]
    
    def _calculate_bbox_area(self, bbox: List[List[float]]) -> float:
        """Calculate area of bounding box."""
        try:
            width = bbox[1][0] - bbox[0][0]
            height = bbox[2][1] - bbox[1][1]
            return width * height
        except:
            return 0
    
    def _validate_and_merge_tables(self, tables: List[Dict], image_shape: Tuple) -> List[Dict]:
        """Validate and merge overlapping table detections."""
        if not tables:
            return []
        
        # Sort by confidence
        tables.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        validated_tables = []
        
        for table in tables:
            # Check if table overlaps significantly with already accepted tables
            is_unique = True
            for accepted_table in validated_tables:
                if self._calculate_overlap(table['bbox'], accepted_table['bbox']) > 0.5:
                    is_unique = False
                    break
            
            if is_unique:
                # Additional validation
                if self._validate_table(table, image_shape):
                    validated_tables.append(table)
        
        return validated_tables
    
    def _calculate_overlap(self, bbox1: List[List[float]], bbox2: List[List[float]]) -> float:
        """Calculate overlap ratio between two bounding boxes."""
        try:
            # Convert to rectangle format
            x1_1, y1_1 = bbox1[0]
            x2_1, y2_1 = bbox1[2]
            x1_2, y1_2 = bbox2[0]
            x2_2, y2_2 = bbox2[2]
            
            # Calculate intersection
            x_left = max(x1_1, x1_2)
            y_top = max(y1_1, y1_2)
            x_right = min(x2_1, x2_2)
            y_bottom = min(y2_1, y2_2)
            
            if x_right < x_left or y_bottom < y_top:
                return 0.0
            
            intersection_area = (x_right - x_left) * (y_bottom - y_top)
            area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
            area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
            
            union_area = area1 + area2 - intersection_area
            return intersection_area / union_area if union_area > 0 else 0.0
        
        except:
            return 0.0
    
    def _validate_table(self, table: Dict, image_shape: Tuple) -> bool:
        """Validate if detected region is actually a table."""
        try:
            # Check minimum size
            if table['area'] < self.min_table_area:
                return False
            
            # Check if table is within image bounds
            bbox = table['bbox']
            height, width = image_shape[:2]
            
            for point in bbox:
                if point[0] < 0 or point[0] > width or point[1] < 0 or point[1] > height:
                    return False
            
            # Check aspect ratio
            width = bbox[1][0] - bbox[0][0]
            height = bbox[2][1] - bbox[1][1]
            aspect_ratio = width / height if height > 0 else 0
            
            if aspect_ratio < 0.1 or aspect_ratio > 10:
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Table validation error: {e}")
            return False 