import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.pdf_extractors import PyMuPDFExtractor, MistralOCRExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Test the PDF extractors"""
    if len(sys.argv) < 2:
        logger.error("Please provide a path to a PDF file")
        return
    
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        logger.error(f"File doesn't exist: {pdf_path}")
        return
    
    logger.info(f"Testing PDF extraction on file: {pdf_path}")
    
    # Test PyMuPDF extractor
    try:
        pymupdf_extractor = PyMuPDFExtractor(file_path=pdf_path)
        logger.info("Extracting text with PyMuPDF...")
        pymupdf_text, pymupdf_error = await pymupdf_extractor.extract_text()
        
        if pymupdf_error:
            logger.error(f"PyMuPDF extraction error: {pymupdf_error}")
        else:
            logger.info(f"PyMuPDF extraction succeeded. Text length: {len(pymupdf_text)}")
            logger.info(f"Sample text: {pymupdf_text[:200]}...")
            
            # Try extract_all as well
            logger.info("Testing extract_all with PyMuPDF...")
            all_content = pymupdf_extractor.extract_all()
            if 'error' in all_content:
                logger.error(f"PyMuPDF extract_all error: {all_content['error']}")
            else:
                logger.info(f"PyMuPDF extract_all succeeded. Extracted {len(all_content['text'])} pages.")
    except Exception as e:
        logger.error(f"PyMuPDF extraction failed: {e}")
    
    # Test Mistral OCR extractor if MISTRAL_API_KEY is set
    mistral_api_key = os.environ.get("MISTRAL_API_KEY")
    if mistral_api_key:
        try:
            mistral_extractor = MistralOCRExtractor(file_path=pdf_path)
            logger.info("Extracting text with Mistral OCR...")
            mistral_text, mistral_error = await mistral_extractor.extract_text()
            
            if mistral_error:
                logger.error(f"Mistral OCR extraction error: {mistral_error}")
            else:
                logger.info(f"Mistral OCR extraction succeeded. Text length: {len(mistral_text)}")
                logger.info(f"Sample text: {mistral_text[:200]}...")
                
                # Try extract_all as well
                logger.info("Testing extract_all with Mistral OCR...")
                all_content = mistral_extractor.extract_all()
                if 'error' in all_content:
                    logger.error(f"Mistral OCR extract_all error: {all_content['error']}")
                else:
                    logger.info(f"Mistral OCR extract_all succeeded. Extracted {len(all_content['text'])} pages.")
        except Exception as e:
            logger.error(f"Mistral OCR extraction failed: {e}")
    else:
        logger.warning("MISTRAL_API_KEY not set. Skipping Mistral OCR test.")

if __name__ == "__main__":
    asyncio.run(main()) 