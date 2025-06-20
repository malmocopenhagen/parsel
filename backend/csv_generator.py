import pandas as pd
import csv
import os
import logging
import re
from typing import List, Dict, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class CSVGenerator:
    def __init__(self):
        """Initialize CSV generator with formatting options."""
        self.default_encoding = 'utf-8'
        self.default_delimiter = ','
        self.quote_char = '"'
        self.escape_char = '\\'
        
        # CSV formatting options
        self.include_headers = True
        self.auto_detect_headers = True
        self.clean_headers = True
        self.fill_missing_values = True
        
    def generate_csv(self, extracted_data: List[List[List[str]]], 
                    validation_results: List[Dict]) -> Dict[str, Any]:
        """Generate CSV data from extracted table data."""
        try:
            if not extracted_data:
                return {
                    'csv_content': '',
                    'filename': '',
                    'total_rows': 0,
                    'total_columns': 0,
                    'tables_processed': 0
                }
            
            # Process each table
            all_csv_data = []
            table_info = []
            
            for i, table_data in enumerate(extracted_data):
                if not table_data:
                    continue
                
                # Generate CSV for this table
                table_csv = self._generate_table_csv(table_data, i, validation_results[i] if i < len(validation_results) else {})
                
                if table_csv:
                    all_csv_data.append(table_csv)
                    table_info.append({
                        'table_index': i,
                        'rows': len(table_csv['data']),
                        'columns': len(table_csv['data'][0]) if table_csv['data'] else 0,
                        'headers': table_csv['headers'],
                        'filename': table_csv['filename']
                    })
            
            # Combine all tables if multiple
            if len(all_csv_data) == 1:
                final_csv = all_csv_data[0]
            else:
                final_csv = self._combine_tables(all_csv_data)
            
            return {
                'csv_content': final_csv['content'],
                'filename': final_csv['filename'],
                'total_rows': final_csv['total_rows'],
                'total_columns': final_csv['total_columns'],
                'tables_processed': len(table_info),
                'table_info': table_info,
                'generation_timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"CSV generation error: {e}")
            return {
                'csv_content': '',
                'filename': '',
                'total_rows': 0,
                'total_columns': 0,
                'tables_processed': 0,
                'error': str(e)
            }
    
    def _generate_table_csv(self, table_data: List[List[str]], table_index: int, 
                           validation_result: Dict) -> Dict[str, Any]:
        """Generate CSV for a single table."""
        try:
            if not table_data:
                return None
            
            # Clean and normalize data
            cleaned_data = self._clean_table_data(table_data)
            
            # Detect and process headers
            headers = self._detect_headers(cleaned_data)
            
            # Separate headers from data
            if headers and self.include_headers:
                data_rows = cleaned_data[1:] if len(cleaned_data) > 1 else []
            else:
                data_rows = cleaned_data
                headers = [f'Column_{i+1}' for i in range(len(data_rows[0]) if data_rows else 0)]
            
            # Clean headers
            if self.clean_headers:
                headers = self._clean_headers(headers)
            
            # Ensure consistent column count
            data_rows = self._normalize_column_count(data_rows, len(headers))
            
            # Fill missing values
            if self.fill_missing_values:
                data_rows = self._fill_missing_values(data_rows)
            
            # Generate CSV content
            csv_content = self._create_csv_content(headers, data_rows)
            
            # Generate filename
            filename = self._generate_filename(table_index, validation_result)
            
            return {
                'content': csv_content,
                'filename': filename,
                'headers': headers,
                'data': data_rows,
                'total_rows': len(data_rows),
                'total_columns': len(headers)
            }
        
        except Exception as e:
            logger.error(f"Table CSV generation error: {e}")
            return None
    
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
        cleaned = cell.strip()
        
        # Remove common OCR artifacts
        cleaned = cleaned.replace('\n', ' ').replace('\r', ' ')
        cleaned = ' '.join(cleaned.split())  # Normalize whitespace
        
        # Remove control characters
        cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in '\t\n\r')
        
        return cleaned
    
    def _detect_headers(self, table_data: List[List[str]]) -> List[str]:
        """Detect if the first row contains headers."""
        if not table_data or not self.auto_detect_headers:
            return []
        
        first_row = table_data[0]
        if not first_row:
            return []
        
        # Check if first row looks like headers
        header_indicators = 0
        total_cells = len(first_row)
        
        for cell in first_row:
            cell_str = str(cell).strip()
            
            # Check for header-like characteristics
            if self._is_likely_header(cell_str):
                header_indicators += 1
        
        # If more than 60% of cells look like headers, treat as header row
        if total_cells > 0 and header_indicators / total_cells > 0.6:
            return first_row
        
        return []
    
    def _is_likely_header(self, cell: str) -> bool:
        """Check if a cell is likely to be a header."""
        if not cell:
            return False
        
        # Check for common header patterns
        header_patterns = [
            r'^[A-Z][a-z\s]+$',  # Title case
            r'^[A-Z\s]+$',       # All caps
            r'^[a-z\s]+$',       # All lowercase
            r'.*[A-Z].*[a-z].*', # Mixed case
        ]
        
        for pattern in header_patterns:
            if re.match(pattern, cell):
                return True
        
        # Check for common header words
        header_words = [
            'name', 'id', 'date', 'time', 'amount', 'price', 'quantity',
            'total', 'sum', 'average', 'count', 'number', 'code', 'type',
            'category', 'status', 'description', 'notes', 'comments'
        ]
        
        cell_lower = cell.lower()
        for word in header_words:
            if word in cell_lower:
                return True
        
        return False
    
    def _clean_headers(self, headers: List[str]) -> List[str]:
        """Clean and normalize headers."""
        cleaned_headers = []
        
        for header in headers:
            # Remove special characters and normalize
            cleaned = re.sub(r'[^\w\s]', '', str(header))
            cleaned = re.sub(r'\s+', '_', cleaned.strip())
            cleaned = cleaned.lower()
            
            # Ensure unique headers
            base_header = cleaned
            counter = 1
            while cleaned in cleaned_headers:
                cleaned = f"{base_header}_{counter}"
                counter += 1
            
            cleaned_headers.append(cleaned)
        
        return cleaned_headers
    
    def _normalize_column_count(self, data_rows: List[List[str]], target_columns: int) -> List[List[str]]:
        """Ensure all rows have the same number of columns."""
        normalized_rows = []
        
        for row in data_rows:
            normalized_row = row.copy()
            
            # Add missing columns
            while len(normalized_row) < target_columns:
                normalized_row.append("")
            
            # Truncate extra columns
            if len(normalized_row) > target_columns:
                normalized_row = normalized_row[:target_columns]
            
            normalized_rows.append(normalized_row)
        
        return normalized_rows
    
    def _fill_missing_values(self, data_rows: List[List[str]]) -> List[List[str]]:
        """Fill missing values with appropriate defaults."""
        if not data_rows:
            return data_rows
        
        filled_rows = []
        num_columns = len(data_rows[0])
        
        for row in data_rows:
            filled_row = []
            for i, cell in enumerate(row):
                if not cell or cell.strip() == "":
                    # Try to infer appropriate default based on column position and data
                    default_value = self._infer_default_value(data_rows, i)
                    filled_row.append(default_value)
                else:
                    filled_row.append(cell)
            filled_rows.append(filled_row)
        
        return filled_rows
    
    def _infer_default_value(self, data_rows: List[List[str]], column_index: int) -> str:
        """Infer appropriate default value for a column based on existing data."""
        try:
            # Get all non-empty values in this column
            column_values = []
            for row in data_rows:
                if column_index < len(row) and row[column_index].strip():
                    column_values.append(row[column_index].strip())
            
            if not column_values:
                return ""
            
            # Analyze data type
            data_type = self._analyze_column_type(column_values)
            
            # Return appropriate default
            if data_type == 'numeric':
                return "0"
            elif data_type == 'date':
                return ""
            elif data_type == 'boolean':
                return "False"
            else:
                return ""
        
        except Exception as e:
            logger.error(f"Default value inference error: {e}")
            return ""
    
    def _analyze_column_type(self, values: List[str]) -> str:
        """Analyze the data type of a column."""
        if not values:
            return 'text'
        
        numeric_count = 0
        date_count = 0
        boolean_count = 0
        
        for value in values:
            # Check if numeric
            try:
                float(re.sub(r'[^\d\.\-]', '', value))
                numeric_count += 1
            except:
                pass
            
            # Check if date
            if re.match(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}[/\-]\d{1,2}[/\-]\d{1,2}', value):
                date_count += 1
            
            # Check if boolean
            if value.lower() in ['true', 'false', 'yes', 'no', '1', '0']:
                boolean_count += 1
        
        total = len(values)
        
        if numeric_count / total > 0.7:
            return 'numeric'
        elif date_count / total > 0.7:
            return 'date'
        elif boolean_count / total > 0.7:
            return 'boolean'
        else:
            return 'text'
    
    def _create_csv_content(self, headers: List[str], data_rows: List[List[str]]) -> str:
        """Create CSV content as string."""
        try:
            output = []
            
            # Write headers
            if headers:
                header_row = self._format_csv_row(headers)
                output.append(header_row)
            
            # Write data rows
            for row in data_rows:
                formatted_row = self._format_csv_row(row)
                output.append(formatted_row)
            
            return '\n'.join(output)
        
        except Exception as e:
            logger.error(f"CSV content creation error: {e}")
            return ""
    
    def _format_csv_row(self, row: List[str]) -> str:
        """Format a row for CSV output."""
        formatted_cells = []
        
        for cell in row:
            cell_str = str(cell)
            
            # Escape quotes and wrap in quotes if needed
            if self.quote_char in cell_str or self.default_delimiter in cell_str or '\n' in cell_str:
                escaped_cell = cell_str.replace(self.quote_char, f'{self.quote_char}{self.quote_char}')
                formatted_cells.append(f'{self.quote_char}{escaped_cell}{self.quote_char}')
            else:
                formatted_cells.append(cell_str)
        
        return self.default_delimiter.join(formatted_cells)
    
    def _generate_filename(self, table_index: int, validation_result: Dict) -> str:
        """Generate filename for the CSV file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            confidence = validation_result.get('confidence', 0.0)
            
            # Create descriptive filename
            if confidence > 0.9:
                quality = "high"
            elif confidence > 0.7:
                quality = "medium"
            else:
                quality = "low"
            
            filename = f"table_{table_index+1}_{quality}_confidence_{confidence:.2f}_{timestamp}.csv"
            return filename
        
        except Exception as e:
            logger.error(f"Filename generation error: {e}")
            return f"table_{table_index+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    def _combine_tables(self, table_csvs: List[Dict]) -> Dict[str, Any]:
        """Combine multiple tables into a single CSV."""
        try:
            if not table_csvs:
                return {
                    'content': '',
                    'filename': '',
                    'total_rows': 0,
                    'total_columns': 0
                }
            
            # If only one table, return it as is
            if len(table_csvs) == 1:
                return table_csvs[0]
            
            # Combine multiple tables
            all_content = []
            total_rows = 0
            max_columns = 0
            
            for i, table_csv in enumerate(table_csvs):
                # Add table separator
                if i > 0:
                    all_content.append("")  # Empty line between tables
                
                # Add table content
                all_content.append(table_csv['content'])
                total_rows += table_csv['total_rows']
                max_columns = max(max_columns, table_csv['total_columns'])
            
            combined_content = '\n'.join(all_content)
            
            # Generate combined filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"combined_tables_{len(table_csvs)}_tables_{timestamp}.csv"
            
            return {
                'content': combined_content,
                'filename': filename,
                'total_rows': total_rows,
                'total_columns': max_columns
            }
        
        except Exception as e:
            logger.error(f"Table combination error: {e}")
            return {
                'content': '',
                'filename': '',
                'total_rows': 0,
                'total_columns': 0
            }
    
    def save_csv_file(self, csv_content: str, filename: str, output_dir: str = "outputs") -> str:
        """Save CSV content to file."""
        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate full file path
            filepath = os.path.join(output_dir, filename)
            
            # Write CSV file
            with open(filepath, 'w', newline='', encoding=self.default_encoding) as csvfile:
                csvfile.write(csv_content)
            
            logger.info(f"CSV file saved: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"CSV file save error: {e}")
            return "" 