from app.services.paper_parser import PaperParser
from app.services.ai_extraction_service import AIExtractionService
from app.services.visualization_generator import VisualizationGenerator
from app.core.models import Paper, PaperStatus, PaperDatabase, Visualization, Section, ComponentType
from fastapi import UploadFile
import os
import aiofiles
import tempfile
import requests
import logging
from typing import Optional, Tuple, Dict, Any, List
from app.utils.pdf_extractors import PDFExtractor, PyMuPDFExtractor, MistralOCRExtractor

logger = logging.getLogger(__name__)

async def process_paper_file(paper: Paper, file: UploadFile):
    """
    Process an uploaded paper file
    
    This function:
    1. Saves the uploaded file to a temporary location
    2. Extracts text and structure from the PDF
    3. Updates the paper record with metadata
    4. Triggers the ML workflow extraction process
    5. Generates visualization
    
    Note: This method is kept for backwards compatibility.
    The preferred method is now process_paper_path which avoids file handling issues.
    """
    temp_path = None
    try:
        # Update status to processing
        paper.status = PaperStatus.PROCESSING
        PaperDatabase.update_paper(paper)
        
        # Create a temporary file to store the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_path = temp_file.name
            
            # Save the uploaded file to the temporary location
            async with aiofiles.open(temp_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
        
        # Process the paper
        result = await process_paper(paper, temp_path)
        
        if result:
            paper.status = PaperStatus.COMPLETED
        else:
            paper.status = PaperStatus.FAILED
        
        # Update the paper in database
        PaperDatabase.update_paper(paper)
        
    except Exception as e:
        logger.error(f"Error processing paper file: {str(e)}")
        paper.status = PaperStatus.FAILED
        PaperDatabase.update_paper(paper)
        
    finally:
        # Clean up the temporary file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

async def process_paper_path(paper: Paper, file_path: str):
    """
    Process a paper file from a path
    
    This function:
    1. Uses the file at the given path (which should already exist)
    2. Extracts text and structure from the PDF
    3. Updates the paper record with metadata
    4. Triggers the ML workflow extraction process
    5. Generates visualization
    6. Cleans up the temporary file
    """
    try:
        # Update status to processing
        paper.status = PaperStatus.PROCESSING
        PaperDatabase.update_paper(paper)
        
        # Process the paper
        result = await process_paper(paper, file_path)
        
        if result:
            paper.status = PaperStatus.COMPLETED
        else:
            paper.status = PaperStatus.FAILED
        
        # Update the paper in database
        PaperDatabase.update_paper(paper)
        
    except Exception as e:
        logger.error(f"Error processing paper file: {str(e)}")
        paper.status = PaperStatus.FAILED
        PaperDatabase.update_paper(paper)
        
    finally:
        # Clean up the temporary file
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)

async def process_paper_url(paper: Paper, url: str):
    """
    Process a paper from a URL
    
    This function:
    1. Downloads the paper from the URL
    2. Saves it to a temporary location
    3. Extracts text and structure from the PDF
    4. Updates the paper record with metadata
    5. Triggers the ML workflow extraction process
    6. Generates visualization
    """
    temp_path = None
    try:
        # Update status to processing
        paper.status = PaperStatus.PROCESSING
        PaperDatabase.update_paper(paper)
        
        # Download the paper from the URL
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Create a temporary file to store the downloaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_path = temp_file.name
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
        
        # Process the paper
        result = await process_paper(paper, temp_path)
        
        if result:
            paper.status = PaperStatus.COMPLETED
        else:
            paper.status = PaperStatus.FAILED
        
        # Update the paper in database
        PaperDatabase.update_paper(paper)
        
    except Exception as e:
        logger.error(f"Error processing paper URL: {str(e)}")
        paper.status = PaperStatus.FAILED
        PaperDatabase.update_paper(paper)
        
    finally:
        # Clean up the temporary file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

async def process_paper(paper: Paper, file_path: str) -> bool:
    """
    Process a paper file to extract ML workflow and generate visualization
    
    Args:
        paper: Paper record
        file_path: Path to the PDF file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Initialize the multi-stage extraction service and visualization generator
        extraction_service = AIExtractionService()
        viz_generator = VisualizationGenerator()
        
        # Process the paper with multi-stage extraction, specifying the parser
        parser_choice = "pymupdf" # Defaulting to PyMuPDF for now
        extraction_result = await extraction_service.process_paper(
            paper_path=file_path, 
            paper_id=paper.id,
            parser_type=parser_choice
        )
        
        if not extraction_result.get("success", False):
            # Error is already logged within AIExtractionService
            # Store the error and diagnostics if available
            paper.error = extraction_result.get("error", "Unknown extraction error")
            paper.diagnostics = extraction_result.get("diagnostics")
            PaperDatabase.update_paper(paper)
            return False

        # Update paper with extracted data
        paper.paper_type = extraction_result.get("paper_type")
        paper.sections = extraction_result.get("sections", {})
        paper.components = extraction_result.get("components", [])
        paper.relationships = extraction_result.get("relationships", [])
        paper.diagnostics = extraction_result.get("diagnostics")
        
        # Check if components were successfully extracted
        if not paper.components or len(paper.components) == 0:
            logger.error(f"Paper {paper.id} processing failed: No components were extracted")
            paper.error = "Component extraction failed: No components were extracted after all attempts."
            paper.status = PaperStatus.FAILED
            PaperDatabase.update_paper(paper)
            return False
        
        # Store relationship analysis in paper details (if attribute exists)
        if hasattr(paper, "details") and paper.details is not None:
            paper.details["relationship_analysis"] = extraction_result.get("relationship_analysis", {})
        elif not hasattr(paper, "details"):
             paper.details = {"relationship_analysis": extraction_result.get("relationship_analysis", {})}

        # Generate visualization
        viz_data = await viz_generator.create_visualization(
            components=paper.components if paper.components else [],
            relationships=paper.relationships if paper.relationships else []
        )
        
        if "error" in viz_data:
            logger.error(f"Error generating visualization: {viz_data['error']}")
            paper.error = f"Visualization error: {viz_data['error']}"
            PaperDatabase.update_paper(paper)
            return False
        
        # Create visualization model and save it to paper
        visualization = Visualization(
            paper_id=paper.id,
            diagram_type=viz_data.get("diagram_type", "mermaid"),
            diagram_data=viz_data.get("diagram_data", ""),
            component_mapping=viz_data.get("component_mapping", {})
        )
        
        paper.visualization = visualization
        
        # Update the paper in the database
        PaperDatabase.update_paper(paper)
        
        return True
        
    except Exception as e:
        logger.exception(f"Critical error in process_paper for {paper.id}: {e}") # Log traceback
        paper.error = f"Unexpected error during processing: {e}"
        PaperDatabase.update_paper(paper)
        return False

class PaperService:
    """Service for processing papers and extracting ML workflows"""

    @staticmethod
    def get_extractor(extractor_type: str = "pymupdf", file_path: str = None) -> PDFExtractor:
        """
        Factory method to get the appropriate PDF extractor
        
        Args:
            extractor_type: The type of extractor to use ('pymupdf' or 'mistral_ocr')
            file_path: Path to the PDF file to extract
            
        Returns:
            A PDFExtractor instance
        """
        if file_path is None:
            raise ValueError("file_path is required for PDFExtractor initialization")
            
        if extractor_type == "mistral_ocr":
            return MistralOCRExtractor(file_path=file_path)
        else:
            return PyMuPDFExtractor(file_path=file_path)  # Default to PyMuPDF
    
    @staticmethod
    async def process_paper(file_path: str, paper_id: str, extractor_type: str = "pymupdf") -> Paper:
        """
        Processes a paper by extracting text and then calling the main AI pipeline.
        This method now primarily handles PDF extraction and delegates AI processing.
        
        Args:
            file_path: Path to the uploaded PDF file
            paper_id: Unique ID for the paper
            extractor_type: The type of extractor to use
            
        Returns:
            Paper object with processing results (status, components, errors, etc.)
        """
        # Initialize paper object
        paper = Paper(
            id=paper_id,
            status=PaperStatus.PROCESSING,
            title=os.path.basename(file_path)
        )
        PaperDatabase.add_paper(paper) # Add paper early so status can be tracked
        
        try:
            # 1. Extract Text using selected extractor
            extractor = PaperService.get_extractor(extractor_type, file_path)
            logging.info(f"Using {extractor.get_name()} extractor for paper {paper_id}")
            
            try:
                paper_text, metadata = await extractor.extract_text()
                if metadata and metadata.get("title"):
                    paper.title = metadata["title"] # Update title if found
                logging.info(f"Extracted {len(paper_text)} characters from paper {paper_id}")

                if not paper_text or len(paper_text.strip()) < 100:
                    logging.warning(f"Extracted text too short for paper {paper_id}")
                    paper.status = PaperStatus.ERROR
                    paper.error = "Extracted text too short to process"
                    paper.error_details = {"type": "EXTRACTION_CONTENT_TOO_SHORT"}
                    return PaperDatabase.update_paper(paper)
                    
            except Exception as e:
                logging.error(f"Error extracting text from paper {paper_id}: {str(e)}", exc_info=True)
                paper.status = PaperStatus.ERROR
                paper.error = f"Failed to extract text: {str(e)}"
                paper.error_details = {"type": "EXTRACTION_FAILED"}
                return PaperDatabase.update_paper(paper)

            # 2. Delegate AI Processing and Visualization to the main process_paper function
            # Ensure the global process_paper function uses AIExtractionService correctly
            # We pass the *already existing* paper object to be updated by process_paper
            logging.info(f"Delegating AI processing for paper {paper_id} to main process_paper function.")
            success = await process_paper(paper, file_path) # Call the global function

            # 3. Check the success flag and update status if necessary
            # The global process_paper function updates errors/diagnostics, but we set final status here.
            if not success:
                if paper.status != PaperStatus.ERROR: # Avoid overwriting specific error status from extraction
                    logger.warning(f"Main processing function returned failure for paper {paper_id}. Setting status to FAILED.")
                    paper.status = PaperStatus.FAILED
                    # Update the DB one last time with the FAILED status if needed
                    PaperDatabase.update_paper(paper)
            else:
                 # Ensure status is COMPLETED on success if not already set
                 # (process_paper should ideally set this, but as a safeguard) 
                 if paper.status != PaperStatus.COMPLETED:
                      logger.info(f"Main processing function success for paper {paper_id}. Ensuring status is COMPLETED.")
                      paper.status = PaperStatus.COMPLETED
                      PaperDatabase.update_paper(paper)
            
            # The global process_paper function now handles updating paper status, 
            # components, relationships, errors, and saving to DB.
            # We just return the final paper object.
            
            # Note: The original file_path used for extraction might be deleted by the global
            # process_paper function's finally block. This is expected.
            
            return PaperDatabase.get_paper(paper_id) # Return the final paper object

        except Exception as e:
            logging.error(f"Unexpected error in PaperService.process_paper for {paper_id}: {str(e)}", exc_info=True)
            paper.status = PaperStatus.ERROR
            paper.error = f"Unexpected outer error: {str(e)}"
            paper.error_details = {"type": "SERVICE_UNEXPECTED_ERROR"}
            return PaperDatabase.update_paper(paper)
