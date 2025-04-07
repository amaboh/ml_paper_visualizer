import os
import logging
from typing import Tuple, Optional, Dict, Any
import asyncio
import json

logger = logging.getLogger(__name__)

async def extract_text_with_mistral_ocr(pdf_path: str) -> Tuple[str, Optional[str]]:
    """
    Extracts text content from a PDF file using Mistral OCR API.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        A tuple containing the extracted text (str) in Markdown format and an error message (Optional[str]).
        If successful, the error message is None.
    """
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        logger.error("MISTRAL_API_KEY environment variable not set.")
        return "", "Configuration error: MISTRAL_API_KEY is not set."
    
    # Import here to avoid errors if Mistral isn't installed
    try:
        from mistralai import Mistral
    except ImportError:
        logger.error("Failed to import Mistral. Is the mistralai package installed?")
        return "", "Import error: mistralai package is not installed or version is incompatible."
    
    markdown_text = ""
    error_message = None
    uploaded_file_id = None
    client = None
    
    try:
        # Create Mistral client
        client = Mistral(api_key=api_key)
        
        # 1. Upload the file to Mistral
        logger.info(f"Uploading {pdf_path} to Mistral...")
        with open(pdf_path, "rb") as f:
            # Run in executor using basic approach
            loop = asyncio.get_running_loop()
            
            # More robust approach with direct argument passing
            def upload_file():
                try:
                    # Try new API format first
                    return client.files.create(("temp_upload.pdf", f))
                except Exception as e1:
                    logger.warning(f"First upload method failed: {e1}, trying alternative...")
                    try:
                        # Try alternative API format
                        return client.files.create(file=("temp_upload.pdf", f))
                    except Exception as e2:
                        logger.warning(f"Second upload method failed: {e2}, trying fallback...")
                        try:
                            # Final fallback if needed
                            return client.files.create(file_name="temp_upload.pdf", file_content=f.read())
                        except Exception as e3:
                            logger.error(f"All upload methods failed. Last error: {e3}")
                            raise e3
            
            # Attempt file upload
            upload_result = await loop.run_in_executor(None, upload_file)
            
            # Different versions of the API might return different structures
            # Try to extract file ID from whatever we got back
            if hasattr(upload_result, 'id'):
                uploaded_file_id = upload_result.id
            elif isinstance(upload_result, dict) and 'id' in upload_result:
                uploaded_file_id = upload_result['id']
            else:
                # Last resort - try to find any ID-like field
                if isinstance(upload_result, dict):
                    for key in ['id', 'file_id', 'fileId']:
                        if key in upload_result:
                            uploaded_file_id = upload_result[key]
                            break
            
            if not uploaded_file_id:
                raise ValueError(f"Could not determine file ID from upload response: {upload_result}")
        
        logger.info(f"File uploaded successfully. File ID: {uploaded_file_id}")

        # 2. Process the uploaded file with OCR
        logger.info(f"Starting Mistral OCR processing for file ID: {uploaded_file_id}")
        
        def process_ocr():
            try:
                # Try new API format first
                return client.ocr.process(
                    model="mistral-ocr-latest",
                    document={
                        "type": "document_id",
                        "document_id": uploaded_file_id
                    }
                )
            except Exception as e1:
                logger.warning(f"First OCR method failed: {e1}, trying alternative...")
                try:
                    # Try alternative format
                    return client.ocr.process(
                        model="mistral-ocr-latest",
                        document_id=uploaded_file_id
                    )
                except Exception as e2:
                    logger.error(f"All OCR methods failed. Last error: {e2}")
                    raise e2
        
        ocr_response = await loop.run_in_executor(None, process_ocr)
        logger.info(f"Mistral OCR processing completed with response type: {type(ocr_response)}")

        # 3. Extract Markdown from the response - very defensive approach
        if ocr_response:
            logger.debug(f"OCR response structure: {type(ocr_response)}")
            
            # Try different ways of accessing pages
            pages = None
            if hasattr(ocr_response, 'pages'):
                pages = ocr_response.pages
            elif isinstance(ocr_response, dict) and 'pages' in ocr_response:
                pages = ocr_response['pages']
            
            if pages:
                # Handle different ways pages might be structured
                for page in pages:
                    page_markdown = None
                    
                    # Try to get markdown content in different ways
                    if hasattr(page, 'markdown'):
                        page_markdown = page.markdown
                    elif isinstance(page, dict) and 'markdown' in page:
                        page_markdown = page['markdown']
                    
                    if page_markdown:
                        markdown_text += page_markdown + "\n\n---\n\n"  # Add page separator
                
                logger.info(f"Successfully extracted text from {len(pages)} pages using Mistral OCR.")
            else:
                logger.warning("No pages found in OCR response.")
        else:
            logger.warning(f"Mistral OCR returned empty response for file {pdf_path}.")
        
        # If we didn't extract anything but didn't have an error, log this
        if not markdown_text:
            logger.warning("No text was extracted from the OCR response.")
            # Try to show the response for debugging
            response_debug = str(ocr_response)[:500] + "..." if len(str(ocr_response)) > 500 else str(ocr_response)
            logger.debug(f"OCR response preview: {response_debug}")

    except FileNotFoundError:
        logger.error(f"File not found at path: '{pdf_path}'")
        error_message = "File not found."
    except Exception as e:
        logger.exception(f"Unexpected error extracting text from '{pdf_path}' with Mistral OCR: {e}")
        error_message = f"An unexpected error occurred during Mistral OCR processing: {e}"
    finally:
        # 4. Clean up the uploaded file on Mistral if possible
        if client and uploaded_file_id:
            try:
                logger.info(f"Attempting to delete temporary Mistral file: {uploaded_file_id}")
                
                def delete_file():
                    try:
                        # Try standard method
                        return client.files.delete(uploaded_file_id)
                    except Exception as e1:
                        logger.warning(f"First delete method failed: {e1}, trying alternative...")
                        try:
                            # Try alternative
                            return client.files.delete(file_id=uploaded_file_id)
                        except Exception as e2:
                            logger.warning(f"Second delete method failed: {e2}")
                            raise e2
                
                await loop.run_in_executor(None, delete_file)
                logger.info(f"Successfully deleted temporary Mistral file: {uploaded_file_id}")
            except Exception as e:
                 logger.warning(f"Could not delete temporary Mistral file {uploaded_file_id}: {e}")

    return markdown_text, error_message 