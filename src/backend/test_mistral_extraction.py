#!/usr/bin/env python
"""
Test the Mistral OCR extraction functionality.
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.mistral_ocr_extractor import extract_text_with_mistral_ocr

async def test_mistral_extraction():
    # Check if API key is set
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("ERROR: MISTRAL_API_KEY environment variable is not set.")
        print("Please set it in a .env file or directly in your environment.")
        return
    
    # Test with a sample PDF
    test_pdf_path = input("Enter path to a test PDF file: ")
    if not os.path.exists(test_pdf_path):
        print(f"ERROR: File not found: {test_pdf_path}")
        return
    
    print(f"Starting extraction from {test_pdf_path}...")
    markdown_text, error = await extract_text_with_mistral_ocr(test_pdf_path)
    
    if error:
        print(f"ERROR during extraction: {error}")
    else:
        print(f"Extraction successful! Got {len(markdown_text)} characters of Markdown.")
        print("\nFirst 500 characters of extracted text:")
        print("----------------------------------------")
        print(markdown_text[:500] + "...")

if __name__ == "__main__":
    asyncio.run(test_mistral_extraction()) 