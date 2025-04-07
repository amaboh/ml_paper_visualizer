import fitz  # PyMuPDF
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

def extract_text_with_pymupdf(pdf_path: str) -> Tuple[str, Optional[str]]:
    """
    Extracts text content from a PDF file using PyMuPDF.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        A tuple containing the extracted text (str) and an error message (Optional[str]).
        If successful, the error message is None.
    """
    text = ""
    error_message = None
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text()
        doc.close()
        logger.info(f"Successfully extracted text from '{pdf_path}' using PyMuPDF.")
    except fitz.fitz.FitzError as e:
        logger.error(f"PyMuPDF FitzError reading '{pdf_path}': {e}")
        error_message = f"PyMuPDF error: Could not process the PDF file. It might be corrupted or password-protected. Details: {e}"
    except FileNotFoundError:
        logger.error(f"File not found at path: '{pdf_path}'")
        error_message = "File not found."
    except Exception as e:
        logger.exception(f"Unexpected error extracting text from '{pdf_path}' with PyMuPDF: {e}")
        error_message = f"An unexpected error occurred during PDF processing: {e}"
        
    return text, error_message 