import os
import sys
import asyncio
import logging
from pathlib import Path
import httpx

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_upload_pdf(pdf_path: str, extractor_type: str = "pymupdf"):
    """
    Test uploading a PDF file to the API
    
    Args:
        pdf_path: Path to the PDF file
        extractor_type: Type of extractor to use (pymupdf or mistral_ocr)
    """
    if not os.path.exists(pdf_path):
        logger.error(f"File doesn't exist: {pdf_path}")
        return

    logger.info(f"Uploading PDF file: {pdf_path} with extractor: {extractor_type}")
    
    # Upload the file to the API
    async with httpx.AsyncClient() as client:
        with open(pdf_path, "rb") as f:
            files = {"file": (os.path.basename(pdf_path), f, "application/pdf")}
            data = {"extractor_type": extractor_type}
            
            try:
                response = await client.post(
                    "http://localhost:8000/api/papers/upload",
                    files=files,
                    data=data,
                    timeout=30.0  # Increased timeout for potential Mistral OCR processing
                )
                
                if response.status_code == 200:
                    logger.info(f"Upload successful: {response.json()}")
                    paper_id = response.json().get("paper_id")
                    
                    if paper_id:
                        # Wait a bit for processing to complete
                        logger.info("Waiting for processing to complete...")
                        await asyncio.sleep(2)
                        
                        # Check paper status
                        status_response = await client.get(
                            f"http://localhost:8000/api/papers/{paper_id}/status"
                        )
                        logger.info(f"Paper status: {status_response.json()}")
                else:
                    logger.error(f"Upload failed: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"Error during API request: {e}")

async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        logger.error("Please provide a path to a PDF file")
        return
    
    pdf_path = sys.argv[1]
    extractor_type = sys.argv[2] if len(sys.argv) > 2 else "pymupdf"
    
    await test_upload_pdf(pdf_path, extractor_type)

if __name__ == "__main__":
    asyncio.run(main()) 