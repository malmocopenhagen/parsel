#!/usr/bin/env python3
"""
Simple test script to verify all dependencies work correctly.
Run this locally before deploying to catch any issues.
"""

import sys
import os

def test_imports():
    """Test that all required packages can be imported."""
    print("Testing imports...")
    
    try:
        import cv2
        print("✅ OpenCV imported successfully")
    except ImportError as e:
        print(f"❌ OpenCV import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ NumPy imported successfully")
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ Pandas imported successfully")
    except ImportError as e:
        print(f"❌ Pandas import failed: {e}")
        return False
    
    try:
        import pytesseract
        print("✅ PyTesseract imported successfully")
    except ImportError as e:
        print(f"❌ PyTesseract import failed: {e}")
        return False
    
    try:
        import easyocr
        print("✅ EasyOCR imported successfully")
    except ImportError as e:
        print(f"❌ EasyOCR import failed: {e}")
        return False
    
    try:
        import fitz
        print("✅ PyMuPDF imported successfully")
    except ImportError as e:
        print(f"❌ PyMuPDF import failed: {e}")
        return False
    
    try:
        from flask import Flask
        print("✅ Flask imported successfully")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    return True

def test_tesseract():
    """Test that Tesseract is available."""
    print("\nTesting Tesseract...")
    
    try:
        import pytesseract
        # Try to get version
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract version: {version}")
        return True
    except Exception as e:
        print(f"❌ Tesseract test failed: {e}")
        return False

def test_easyocr():
    """Test that EasyOCR can initialize."""
    print("\nTesting EasyOCR...")
    
    try:
        import easyocr
        reader = easyocr.Reader(['en'])
        print("✅ EasyOCR initialized successfully")
        return True
    except Exception as e:
        print(f"❌ EasyOCR test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Running deployment tests...\n")
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test Tesseract
    if not test_tesseract():
        all_passed = False
    
    # Test EasyOCR
    if not test_easyocr():
        all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 All tests passed! Deployment should work.")
        return 0
    else:
        print("❌ Some tests failed. Please fix issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 