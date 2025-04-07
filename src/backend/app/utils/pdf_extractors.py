"""
PDF extractor classes for different extraction methods.
This file provides a common interface for different PDF extraction methods.
"""
import os
import logging
from typing import Dict, Any, Optional, List, Tuple
from abc import ABC, abstractmethod
import asyncio

logger = logging.getLogger(__name__)

class PDFExtractor(ABC):
    """Base class for PDF extractors with a common interface"""
    
    def __init__(self, file_path: str):
        """Initialize the extractor with a file path
        
        Args:
            file_path: Path to the PDF file to extract
        """
        self.file_path = file_path
        
    def get_name(self) -> str:
        """Get the name of the extractor
        
        Returns:
            str: The name of the extractor
        """
        return "Base PDFExtractor"
        
    @abstractmethod
    async def extract_text(self) -> Tuple[str, Optional[str]]:
        """Extract text from the PDF file
        
        Returns:
            Tuple[str, Optional[str]]: The extracted text and an optional error message
        """
        pass
    
    def extract_all(self) -> Dict[str, Any]:
        """Extract all content and metadata from the PDF
        
        This method should be overridden by subclasses that can extract
        more structured information from PDFs.
        
        Returns:
            Dict[str, Any]: A dictionary containing the extracted content
                text: List of pages of text content
                sections: List of sections detected in the document
                structured_text: Structured representation of the document
                If there's an error, the dict will contain an 'error' key
        """
        # Default implementation extracts plain text and returns a basic structure
        try:
            # This will be replaced by the actual async extraction in an async context
            text, error = "", None
            
            if error:
                return {"error": error}
            
            # Convert single text string to list of pages (simple split by double newlines)
            # This is a very basic approach, subclasses should do better
            pages = [p for p in text.split('\n\n\n') if p.strip()]
            
            return {
                "text": pages,
                "sections": [],  # No sections by default
                "structured_text": {"type": "text", "content": text}
            }
        except Exception as e:
            logger.exception(f"Error in extract_all: {e}")
            return {"error": str(e)}

    def extract_section_text(self, structured_text: Dict[str, Any], 
                           start_location: Dict[str, Any], 
                           end_location: Dict[str, Any]) -> str:
        """Extract text for a specific section
        
        Args:
            structured_text: Structured text data from extract_all
            start_location: Information about section start location
            end_location: Information about section end location
            
        Returns:
            str: Text content of the section
        """
        # Default implementation - just return the full text 
        # Subclasses should override with more precise extraction
        if isinstance(structured_text, dict) and "content" in structured_text:
            return structured_text["content"]
        return ""


class PyMuPDFExtractor(PDFExtractor):
    """PDF text extractor using PyMuPDF (fitz)"""
    
    def get_name(self) -> str:
        """Get the name of the extractor
        
        Returns:
            str: The name of the extractor
        """
        return "PyMuPDF"
    
    async def extract_text(self) -> Tuple[str, Optional[str]]:
        """Extract text using PyMuPDF
        
        Returns:
            Tuple[str, Optional[str]]: The extracted text and an optional error message
        """
        text = ""
        error_message = None
        try:
            # Import here to avoid errors if PyMuPDF isn't installed
            import fitz
            
            loop = asyncio.get_running_loop()
            
            def extract_with_pymupdf():
                try:
                    doc = fitz.open(self.file_path)
                    text = ""
                    for page_num in range(len(doc)):
                        page = doc.load_page(page_num)
                        text += page.get_text()
                    doc.close()
                    return text
                except fitz.fitz.FileDataError as e:
                    raise ValueError(f"PyMuPDF file error: {e}")
            
            text = await loop.run_in_executor(None, extract_with_pymupdf)
            logger.info(f"Successfully extracted text from '{self.file_path}' using PyMuPDF.")
        except ImportError:
            error_message = "PyMuPDF (fitz) is not installed"
            logger.error(error_message)
        except FileNotFoundError:
            error_message = f"File not found at path: '{self.file_path}'"
            logger.error(error_message)
        except Exception as e:
            error_message = f"An unexpected error occurred during PDF processing: {e}"
            logger.exception(f"Unexpected error extracting text from '{self.file_path}' with PyMuPDF: {e}")
            
        return text, error_message
    
    def extract_all(self) -> Dict[str, Any]:
        """Extract all content from PDF using PyMuPDF
        
        Returns:
            Dict[str, Any]: Dictionary with extracted content
        """
        try:
            # Import fitz here to avoid import errors if PyMuPDF isn't installed
            import fitz
            
            text_by_page = []
            
            try:
                doc = fitz.open(self.file_path)
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text_by_page.append(page.get_text())
                
                # Very basic section detection based on font size
                # A more sophisticated implementation would use layout analysis
                sections = []
                
                # Return structured results
                return {
                    "text": text_by_page,
                    "sections": sections,
                    "structured_text": {"type": "text", "content": "\n\n\n".join(text_by_page)}
                }
            except Exception as e:
                logger.error(f"PyMuPDF extraction error: {e}")
                return {"error": f"PyMuPDF extraction error: {e}"}
        except ImportError:
            logger.error("PyMuPDF (fitz) is not installed")
            return {"error": "PyMuPDF (fitz) is not installed"}


class MistralOCRExtractor(PDFExtractor):
    """PDF text extractor using Mistral AI OCR API"""
    
    def get_name(self) -> str:
        """Get the name of the extractor
        
        Returns:
            str: The name of the extractor
        """
        return "Mistral OCR"
    
    async def extract_text(self) -> Tuple[str, Optional[str]]:
        """Extract text using Mistral OCR
        
        Returns:
            Tuple[str, Optional[str]]: The extracted markdown text and an optional error message
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
            logger.info(f"Uploading {self.file_path} to Mistral...")
            with open(self.file_path, "rb") as f:
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
                logger.warning(f"Mistral OCR returned empty response for file {self.file_path}.")
            
            # If we didn't extract anything but didn't have an error, log this
            if not markdown_text:
                logger.warning("No text was extracted from the OCR response.")
                # Try to show the response for debugging
                response_debug = str(ocr_response)[:500] + "..." if len(str(ocr_response)) > 500 else str(ocr_response)
                logger.debug(f"OCR response preview: {response_debug}")

        except FileNotFoundError:
            logger.error(f"File not found at path: '{self.file_path}'")
            error_message = "File not found."
        except Exception as e:
            logger.exception(f"Unexpected error extracting text from '{self.file_path}' with Mistral OCR: {e}")
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
    
    def extract_all(self) -> Dict[str, Any]:
        """Extract all content from PDF using Mistral OCR
        
        Note: This will run the extraction synchronously, which is not ideal.
        It's better to use the async extract_text method in an async context.
        
        Returns:
            Dict[str, Any]: Dictionary with extracted content
        """
        try:
            # We can't run async code directly in a sync method,
            # so we'll have to use a workaround to get the result
            import asyncio
            
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the async extraction and get the result
            text, error = loop.run_until_complete(self.extract_text())
            loop.close()
            
            if error:
                return {"error": error}
            
            # Mistral OCR returns markdown with page separators "---"
            # Split the markdown by these separators to get pages
            pages = []
            for page in text.split("\n\n---\n\n"):
                if page.strip():
                    pages.append(page)
            
            # Return structured results
            return {
                "text": pages,
                "sections": [],  # Future enhancement: extract sections from markdown structure
                "structured_text": {"type": "markdown", "content": text}
            }
        except Exception as e:
            logger.exception(f"Mistral OCR extraction error in extract_all: {e}")
            return {"error": f"Mistral OCR extraction error: {e}"} 