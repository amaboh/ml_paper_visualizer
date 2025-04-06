from app.services.paper_parser import PaperParser
from app.services.visualization_generator import VisualizationGenerator
from app.core.models import Paper, PaperStatus, PaperDatabase, Visualization
from fastapi import UploadFile
import os
import aiofiles
import tempfile
import requests
import logging
from typing import Optional, Tuple, Dict, Any

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
        # Initialize parser and visualization generator
        parser = PaperParser()
        viz_generator = VisualizationGenerator()
        
        # Parse the paper to extract components and relationships
        components, relationships = await parser.parse_paper(file_path, paper.id)
        
        if not components:
            logger.error("No components extracted from paper")
            return False
        
        # Save components and relationships to paper record
        paper.components = components
        paper.relationships = relationships
        
        # Generate visualization - both use the same AIProcessor singleton
        viz_data = await viz_generator.create_visualization(
            components=components,
            relationships=relationships
        )
        
        if "error" in viz_data:
            logger.error(f"Error generating visualization: {viz_data['error']}")
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
        
        logger.info(f"Successfully processed paper {paper.id}")
        return True
        
    except Exception as e:
        logger.error(f"Error in paper processing pipeline: {str(e)}")
        return False
