from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import json
import pandas as pd
from werkzeug.utils import secure_filename
import logging
from datetime import datetime

from ocr_engine import OCREngine
from table_detector import TableDetector
from data_validator import DataValidator
from csv_generator import CSVGenerator

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
ocr_engine = OCREngine()
table_detector = TableDetector()
data_validator = DataValidator()
csv_generator = CSVGenerator()

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/upload', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        logger.info(f"File uploaded: {filename}")
        
        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'filepath': filepath
        })
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/extract', methods=['POST'])
def extract_data():
    try:
        data = request.get_json()
        filepath = data.get('filepath')
        extraction_options = data.get('options', {})
        
        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        logger.info(f"Starting extraction for: {filepath}")
        
        # Step 1: OCR Processing
        logger.info("Step 1: Running OCR...")
        ocr_results = ocr_engine.process_document(filepath, extraction_options)
        
        # Step 2: Table Detection
        logger.info("Step 2: Detecting tables...")
        table_regions = table_detector.detect_tables(filepath, ocr_results)
        
        # Step 3: Data Extraction and Validation
        logger.info("Step 3: Extracting and validating data...")
        extracted_data = []
        validation_results = []
        
        for i, table_region in enumerate(table_regions):
            table_data = ocr_engine.extract_table_data(ocr_results, table_region)
            validated_data = data_validator.validate_table(table_data, i)
            extracted_data.append(validated_data['data'])
            validation_results.append(validated_data['validation'])
        
        # Step 4: Generate CSV
        logger.info("Step 4: Generating CSV...")
        csv_data = csv_generator.generate_csv(extracted_data, validation_results)
        
        # Calculate accuracy metrics
        total_cells = sum(len(table) * len(table[0]) if table else 0 for table in extracted_data)
        validation_errors = sum(len(result['errors']) for result in validation_results)
        accuracy_rate = (total_cells - validation_errors) / total_cells if total_cells > 0 else 1.0
        
        logger.info(f"Extraction completed. Accuracy: {accuracy_rate:.4f}")
        
        return jsonify({
            'success': True,
            'accuracy_rate': accuracy_rate,
            'total_tables': len(extracted_data),
            'total_cells': total_cells,
            'validation_errors': validation_errors,
            'csv_data': csv_data,
            'validation_results': validation_results
        })
    
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_csv(filename):
    try:
        csv_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(csv_path):
            return jsonify({'error': 'CSV file not found'}), 404
        
        return send_file(csv_path, as_attachment=True, download_name=filename)
    
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/preview', methods=['POST'])
def preview_extraction():
    try:
        data = request.get_json()
        filepath = data.get('filepath')
        page_number = data.get('page', 1)
        
        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Generate preview with OCR results
        preview_data = ocr_engine.generate_preview(filepath, page_number)
        
        return jsonify({
            'success': True,
            'preview': preview_data
        })
    
    except Exception as e:
        logger.error(f"Preview error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Get port from environment variable (for Railway) or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(debug=False, host='0.0.0.0', port=port) 