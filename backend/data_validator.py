import re
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class DataValidator:
    def __init__(self):
        """Initialize data validator with multiple validation strategies."""
        self.validation_rules = {
            'numeric': r'^[\d\.,\-\(\)\s]+$',
            'currency': r'^[\$\€\£\¥]?[\d\.,\s]+$',
            'percentage': r'^[\d\.,\s]*%?$',
            'date': r'^\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}$|^\d{4}[/\-]\d{1,2}[/\-]\d{1,2}$',
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^[\d\s\(\)\-\+\.]+$',
            'url': r'^https?://[^\s/$.?#].[^\s]*$'
        }
        
        # Common data patterns
        self.data_patterns = {
            'empty_cells': r'^\s*$',
            'whitespace_only': r'^\s+$',
            'single_char': r'^.$',
            'likely_header': r'^[A-Z][a-z\s]+$'
        }
        
        # Validation thresholds
        self.min_row_length = 2
        self.max_empty_ratio = 0.3
        self.min_confidence = 0.6
        
    def validate_table(self, table_data: List[List[str]], table_index: int) -> Dict[str, Any]:
        """Validate table data and return validation results."""
        try:
            if not table_data or not table_data[0]:
                return {
                    'data': [],
                    'validation': {
                        'table_index': table_index,
                        'is_valid': False,
                        'errors': ['Empty table data'],
                        'warnings': [],
                        'confidence': 0.0
                    }
                }
            
            # Step 1: Basic structure validation
            structure_validation = self._validate_structure(table_data)
            
            # Step 2: Content validation
            content_validation = self._validate_content(table_data)
            
            # Step 3: Data type validation
            type_validation = self._validate_data_types(table_data)
            
            # Step 4: Consistency validation
            consistency_validation = self._validate_consistency(table_data)
            
            # Step 5: Clean and correct data
            cleaned_data = self._clean_table_data(table_data)
            
            # Combine validation results
            all_errors = (structure_validation['errors'] + 
                         content_validation['errors'] + 
                         type_validation['errors'] + 
                         consistency_validation['errors'])
            
            all_warnings = (structure_validation['warnings'] + 
                           content_validation['warnings'] + 
                           type_validation['warnings'] + 
                           consistency_validation['warnings'])
            
            # Calculate overall confidence
            confidence = self._calculate_confidence(
                structure_validation, content_validation, 
                type_validation, consistency_validation
            )
            
            return {
                'data': cleaned_data,
                'validation': {
                    'table_index': table_index,
                    'is_valid': len(all_errors) == 0,
                    'errors': all_errors,
                    'warnings': all_warnings,
                    'confidence': confidence,
                    'structure_score': structure_validation['score'],
                    'content_score': content_validation['score'],
                    'type_score': type_validation['score'],
                    'consistency_score': consistency_validation['score']
                }
            }
        
        except Exception as e:
            logger.error(f"Table validation error: {e}")
            return {
                'data': table_data,
                'validation': {
                    'table_index': table_index,
                    'is_valid': False,
                    'errors': [f'Validation error: {str(e)}'],
                    'warnings': [],
                    'confidence': 0.0
                }
            }
    
    def _validate_structure(self, table_data: List[List[str]]) -> Dict[str, Any]:
        """Validate table structure and layout."""
        errors = []
        warnings = []
        score = 1.0
        
        try:
            if not table_data:
                return {'errors': ['Empty table'], 'warnings': [], 'score': 0.0}
            
            # Check for minimum rows
            if len(table_data) < 2:
                errors.append('Table has fewer than 2 rows')
                score -= 0.3
            
            # Check for minimum columns
            min_cols = min(len(row) for row in table_data if row)
            if min_cols < self.min_row_length:
                errors.append(f'Table has fewer than {self.min_row_length} columns')
                score -= 0.3
            
            # Check for consistent column count
            col_counts = [len(row) for row in table_data if row]
            if len(set(col_counts)) > 1:
                warnings.append('Inconsistent number of columns across rows')
                score -= 0.1
            
            # Check for empty rows
            empty_rows = sum(1 for row in table_data if not row or all(not cell.strip() for cell in row))
            if empty_rows > 0:
                warnings.append(f'Found {empty_rows} empty rows')
                score -= 0.1 * empty_rows / len(table_data)
            
            return {
                'errors': errors,
                'warnings': warnings,
                'score': max(0.0, score)
            }
        
        except Exception as e:
            logger.error(f"Structure validation error: {e}")
            return {'errors': [f'Structure validation error: {str(e)}'], 'warnings': [], 'score': 0.0}
    
    def _validate_content(self, table_data: List[List[str]]) -> Dict[str, Any]:
        """Validate table content quality."""
        errors = []
        warnings = []
        score = 1.0
        
        try:
            total_cells = 0
            empty_cells = 0
            problematic_cells = 0
            
            for row in table_data:
                for cell in row:
                    total_cells += 1
                    cell = str(cell).strip()
                    
                    # Check for empty cells
                    if not cell or re.match(self.data_patterns['empty_cells'], cell):
                        empty_cells += 1
                    
                    # Check for problematic content
                    elif re.match(self.data_patterns['whitespace_only'], cell):
                        problematic_cells += 1
                    elif re.match(self.data_patterns['single_char'], cell):
                        problematic_cells += 1
            
            # Check empty cell ratio
            if total_cells > 0:
                empty_ratio = empty_cells / total_cells
                if empty_ratio > self.max_empty_ratio:
                    errors.append(f'Too many empty cells: {empty_ratio:.1%}')
                    score -= 0.3
                elif empty_ratio > 0.1:
                    warnings.append(f'High empty cell ratio: {empty_ratio:.1%}')
                    score -= 0.1
            
            # Check for problematic content
            if problematic_cells > 0:
                warnings.append(f'Found {problematic_cells} problematic cells')
                score -= 0.1 * problematic_cells / total_cells
            
            return {
                'errors': errors,
                'warnings': warnings,
                'score': max(0.0, score)
            }
        
        except Exception as e:
            logger.error(f"Content validation error: {e}")
            return {'errors': [f'Content validation error: {str(e)}'], 'warnings': [], 'score': 0.0}
    
    def _validate_data_types(self, table_data: List[List[str]]) -> Dict[str, Any]:
        """Validate data types and patterns."""
        errors = []
        warnings = []
        score = 1.0
        
        try:
            if not table_data or len(table_data) < 2:
                return {'errors': errors, 'warnings': warnings, 'score': score}
            
            # Analyze data types in each column
            num_cols = max(len(row) for row in table_data)
            column_types = []
            
            for col in range(num_cols):
                col_data = []
                for row in table_data:
                    if col < len(row):
                        col_data.append(str(row[col]).strip())
                
                col_type = self._infer_column_type(col_data)
                column_types.append(col_type)
            
            # Check for mixed data types in columns
            for i, col_type in enumerate(column_types):
                if col_type == 'mixed':
                    warnings.append(f'Column {i+1} has mixed data types')
                    score -= 0.05
            
            # Check for consistent data patterns
            pattern_consistency = self._check_pattern_consistency(table_data)
            if not pattern_consistency['consistent']:
                warnings.append('Inconsistent data patterns detected')
                score -= 0.1
            
            return {
                'errors': errors,
                'warnings': warnings,
                'score': max(0.0, score)
            }
        
        except Exception as e:
            logger.error(f"Data type validation error: {e}")
            return {'errors': [f'Data type validation error: {str(e)}'], 'warnings': [], 'score': 0.0}
    
    def _validate_consistency(self, table_data: List[List[str]]) -> Dict[str, Any]:
        """Validate data consistency across the table."""
        errors = []
        warnings = []
        score = 1.0
        
        try:
            if not table_data or len(table_data) < 3:
                return {'errors': errors, 'warnings': warnings, 'score': score}
            
            # Check for duplicate rows
            unique_rows = set()
            duplicate_count = 0
            
            for row in table_data:
                row_str = '|'.join(str(cell).strip() for cell in row)
                if row_str in unique_rows:
                    duplicate_count += 1
                else:
                    unique_rows.add(row_str)
            
            if duplicate_count > 0:
                warnings.append(f'Found {duplicate_count} duplicate rows')
                score -= 0.1 * duplicate_count / len(table_data)
            
            # Check for data outliers
            outliers = self._detect_outliers(table_data)
            if outliers:
                warnings.append(f'Detected {len(outliers)} potential data outliers')
                score -= 0.05
            
            # Check for missing values patterns
            missing_patterns = self._analyze_missing_values(table_data)
            if missing_patterns['suspicious']:
                warnings.append('Suspicious missing value patterns detected')
                score -= 0.1
            
            return {
                'errors': errors,
                'warnings': warnings,
                'score': max(0.0, score)
            }
        
        except Exception as e:
            logger.error(f"Consistency validation error: {e}")
            return {'errors': [f'Consistency validation error: {str(e)}'], 'warnings': [], 'score': 0.0}
    
    def _infer_column_type(self, column_data: List[str]) -> str:
        """Infer the data type of a column."""
        if not column_data:
            return 'empty'
        
        # Remove empty values
        non_empty = [cell for cell in column_data if cell.strip()]
        if not non_empty:
            return 'empty'
        
        # Count matches for each type
        type_counts = {
            'numeric': 0,
            'currency': 0,
            'percentage': 0,
            'date': 0,
            'email': 0,
            'phone': 0,
            'url': 0,
            'text': 0
        }
        
        for cell in non_empty:
            matched = False
            for data_type, pattern in self.validation_rules.items():
                if re.match(pattern, cell, re.IGNORECASE):
                    type_counts[data_type] += 1
                    matched = True
                    break
            
            if not matched:
                type_counts['text'] += 1
        
        # Find dominant type
        dominant_type = max(type_counts, key=type_counts.get)
        dominant_count = type_counts[dominant_type]
        
        # Check if type is consistent
        if dominant_count / len(non_empty) >= 0.8:
            return dominant_type
        else:
            return 'mixed'
    
    def _check_pattern_consistency(self, table_data: List[List[str]]) -> Dict[str, Any]:
        """Check for consistent patterns in the data."""
        try:
            if not table_data or len(table_data) < 2:
                return {'consistent': True, 'issues': []}
            
            issues = []
            
            # Check for consistent formatting
            for col in range(max(len(row) for row in table_data)):
                col_data = []
                for row in table_data:
                    if col < len(row):
                        col_data.append(str(row[col]).strip())
                
                # Check for consistent case
                cases = [cell.isupper() for cell in col_data if cell]
                if len(set(cases)) > 1 and len(cases) > 3:
                    issues.append(f'Inconsistent case in column {col+1}')
                
                # Check for consistent length
                lengths = [len(cell) for cell in col_data if cell]
                if lengths:
                    length_std = np.std(lengths)
                    length_mean = np.mean(lengths)
                    if length_std > length_mean * 0.5:
                        issues.append(f'Inconsistent length in column {col+1}')
            
            return {
                'consistent': len(issues) == 0,
                'issues': issues
            }
        
        except Exception as e:
            logger.error(f"Pattern consistency check error: {e}")
            return {'consistent': False, 'issues': [str(e)]}
    
    def _detect_outliers(self, table_data: List[List[str]]) -> List[Tuple[int, int]]:
        """Detect potential outliers in numeric data."""
        outliers = []
        
        try:
            for col in range(max(len(row) for row in table_data)):
                numeric_values = []
                numeric_indices = []
                
                for row_idx, row in enumerate(table_data):
                    if col < len(row):
                        cell = str(row[col]).strip()
                        # Try to convert to numeric
                        try:
                            # Remove common non-numeric characters
                            clean_cell = re.sub(r'[^\d\.\-]', '', cell)
                            if clean_cell:
                                value = float(clean_cell)
                                numeric_values.append(value)
                                numeric_indices.append((row_idx, col))
                        except:
                            continue
                
                if len(numeric_values) > 5:
                    # Use IQR method to detect outliers
                    q1 = np.percentile(numeric_values, 25)
                    q3 = np.percentile(numeric_values, 75)
                    iqr = q3 - q1
                    
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    
                    for i, value in enumerate(numeric_values):
                        if value < lower_bound or value > upper_bound:
                            outliers.append(numeric_indices[i])
        
        except Exception as e:
            logger.error(f"Outlier detection error: {e}")
        
        return outliers
    
    def _analyze_missing_values(self, table_data: List[List[str]]) -> Dict[str, Any]:
        """Analyze patterns in missing values."""
        try:
            missing_positions = []
            
            for row_idx, row in enumerate(table_data):
                for col_idx, cell in enumerate(row):
                    if not str(cell).strip():
                        missing_positions.append((row_idx, col_idx))
            
            if not missing_positions:
                return {'suspicious': False, 'pattern': 'none'}
            
            # Check for systematic patterns
            rows_with_missing = set(pos[0] for pos in missing_positions)
            cols_with_missing = set(pos[1] for pos in missing_positions)
            
            # If missing values are concentrated in specific rows or columns
            if len(rows_with_missing) <= len(table_data) * 0.3 or len(cols_with_missing) <= max(len(row) for row in table_data) * 0.3:
                return {'suspicious': True, 'pattern': 'systematic'}
            
            return {'suspicious': False, 'pattern': 'random'}
        
        except Exception as e:
            logger.error(f"Missing value analysis error: {e}")
            return {'suspicious': False, 'pattern': 'unknown'}
    
    def _clean_table_data(self, table_data: List[List[str]]) -> List[List[str]]:
        """Clean and normalize table data."""
        cleaned_data = []
        
        try:
            for row in table_data:
                cleaned_row = []
                for cell in row:
                    cleaned_cell = self._clean_cell(str(cell))
                    cleaned_row.append(cleaned_cell)
                cleaned_data.append(cleaned_row)
        
        except Exception as e:
            logger.error(f"Data cleaning error: {e}")
            return table_data
        
        return cleaned_data
    
    def _clean_cell(self, cell: str) -> str:
        """Clean individual cell data."""
        if not cell:
            return ""
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cell.strip())
        
        # Remove common OCR artifacts
        cleaned = re.sub(r'[|]{2,}', '|', cleaned)  # Multiple pipes
        cleaned = re.sub(r'[l]{2,}', 'll', cleaned)  # Multiple l's
        cleaned = re.sub(r'[1]{2,}', '11', cleaned)  # Multiple 1's
        
        # Fix common OCR mistakes
        replacements = {
            '0': 'O',  # Common OCR mistake
            'l': '1',  # Common OCR mistake
            '|': 'I',  # Common OCR mistake
        }
        
        # Only apply replacements if they make sense in context
        for wrong, correct in replacements.items():
            if len(cleaned) == 1 and cleaned == wrong:
                cleaned = correct
        
        return cleaned
    
    def _calculate_confidence(self, structure_validation: Dict, content_validation: Dict,
                            type_validation: Dict, consistency_validation: Dict) -> float:
        """Calculate overall confidence score."""
        try:
            # Weighted average of validation scores
            weights = {
                'structure': 0.3,
                'content': 0.3,
                'type': 0.2,
                'consistency': 0.2
            }
            
            confidence = (
                structure_validation['score'] * weights['structure'] +
                content_validation['score'] * weights['content'] +
                type_validation['score'] * weights['type'] +
                consistency_validation['score'] * weights['consistency']
            )
            
            # Penalize for errors
            total_errors = (len(structure_validation['errors']) + 
                           len(content_validation['errors']) + 
                           len(type_validation['errors']) + 
                           len(consistency_validation['errors']))
            
            if total_errors > 0:
                confidence *= (0.9 ** total_errors)  # Reduce confidence for each error
            
            return max(0.0, min(1.0, confidence))
        
        except Exception as e:
            logger.error(f"Confidence calculation error: {e}")
            return 0.0 