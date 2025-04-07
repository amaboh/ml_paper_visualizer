from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, Response, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import uuid
import os
import tempfile
import aiofiles
import logging

from app.core.models import Paper, PaperStatus, PaperResponse, PaperUpload, PaperDatabase, Component, ComponentType, Relationship, Visualization
from app.services.paper_service import PaperService, process_paper as process_paper_pipeline

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Define Background Task Function --- 
# Moved processing logic into a separate function to be run in the background
async def run_paper_processing(temp_file_path: str, paper_id: str, extractor_type: str):
    """Helper function to run the actual paper processing in the background."""
    logger.info(f"Background task started for paper {paper_id} at path {temp_file_path}")
    paper = PaperDatabase.get_paper(paper_id)
    if not paper:
         # This should ideally not happen if called right after creation
         logger.error(f"Background task could not find paper {paper_id} in DB.")
         # How to signal this failure? For now, log it.
         # Consider adding a FAILED state if paper is missing.
         return
         
    # Ensure the paper object is up-to-date before processing
    paper.status = PaperStatus.PROCESSING
    PaperDatabase.update_paper(paper)
    
    try:
        # Call the imported process_paper function from paper_service.py
        success = await process_paper_pipeline(paper, temp_file_path)
        
        # Explicitly update the paper status to COMPLETED if successful
        if success:
            paper.status = PaperStatus.COMPLETED
            PaperDatabase.update_paper(paper)
        else:
            # If process_paper_pipeline returned False, ensure paper status is FAILED
            paper.status = PaperStatus.FAILED
            if not hasattr(paper, 'error') or not paper.error:
                paper.error = "Paper processing failed without specific error"
            PaperDatabase.update_paper(paper)
                
        logger.info(f"Background task finished for paper {paper_id}. Final status: {paper.status}")
    except Exception as e:
         # Log critical errors in the background task itself
         logger.exception(f"Critical error in background task for paper {paper_id}: {e}")
         # Update paper status to reflect the background task failure
         paper.status = PaperStatus.FAILED # Or ERROR
         paper.error = f"Background processing task failed: {str(e)}"
         paper.error_details = {"type": "BACKGROUND_TASK_CRASH"}
         PaperDatabase.update_paper(paper)
    finally:
        # Clean up the temporary file after processing is done (or failed)
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info(f"Successfully deleted temp file: {temp_file_path}")
            except OSError as e:
                 logger.error(f"Error deleting temp file {temp_file_path}: {e}")

# --- Refactor Upload Endpoint --- 
@router.post("/upload", status_code=status.HTTP_202_ACCEPTED, response_model=Dict[str, Any])
async def upload_paper(
    background_tasks: BackgroundTasks,
    response: Response, # Inject Response object to set headers
    file: UploadFile = File(...),
    extractor_type: str = Form("pymupdf")
):
    """
    Accepts paper upload, saves it, schedules background processing, and returns immediately.
    
    Args:
        background_tasks: FastAPI background tasks dependency.
        response: FastAPI response object.
        file: The PDF file to upload.
        extractor_type: The type of PDF extractor ('pymupdf' or 'mistral_ocr').
    """
    if extractor_type not in ["pymupdf", "mistral_ocr"]:
        raise HTTPException(status_code=400, detail=f"Invalid extractor type: {extractor_type}. Must be 'pymupdf' or 'mistral_ocr'")
    
    paper_id = str(uuid.uuid4())
    temp_file_path = None
    
    try:
        # 1. Save the uploaded file to a temporary location
        # Use a secure temp directory if possible
        temp_dir = tempfile.gettempdir()
        safe_filename = f"paper_{paper_id}.pdf" # Avoid using raw filename
        temp_file_path = os.path.join(temp_dir, safe_filename)

        async with aiofiles.open(temp_file_path, 'wb') as out_file:
            content = await file.read()
            if not content:
                 raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            await out_file.write(content)
        logger.info(f"Saved uploaded file for {paper_id} to {temp_file_path}")

        # 2. Create initial Paper record in DB
        paper = Paper(
            id=paper_id,
            status=PaperStatus.PENDING,
            title=file.filename or "Untitled Paper", # Use original filename for initial title
            diagnostics={"parser_used": extractor_type} # Store extractor choice early
        )
        PaperDatabase.add_paper(paper)
        logger.info(f"Created initial PENDING paper record for {paper_id}")

        # 3. Add the processing task to the background
        background_tasks.add_task(
            run_paper_processing, 
            temp_file_path=temp_file_path, 
            paper_id=paper_id, 
            extractor_type=extractor_type
        )
        logger.info(f"Scheduled background processing for paper {paper_id}")

        # 4. Return 202 Accepted immediately
        results_url = f"/api/papers/{paper_id}" # URL to check status/results
        response.headers["Location"] = results_url # Set Location header
        
        return {
            "paper_id": paper.id,
            "status": paper.status.value, # Return PENDING
            "title": paper.title,
            "message": "Paper upload accepted, processing started in background.",
            "results_url": results_url
        }

    except HTTPException as http_exc:
         # Re-raise HTTPExceptions to let FastAPI handle them
         raise http_exc
    except Exception as e:
        logger.exception(f"Error during initial paper upload for {paper_id}: {e}")
        # Clean up temp file if created before error
        if temp_file_path and os.path.exists(temp_file_path):
            try: os.unlink(temp_file_path) 
            except OSError: pass
        # Return a 500 error for unexpected issues during upload/scheduling phase
        raise HTTPException(status_code=500, detail=f"Internal server error during upload initiation: {str(e)}")

@router.get("/{paper_id}", response_model=PaperResponse)
async def get_paper(paper_id: str):
    """
    Get paper information
    
    Args:
        paper_id: ID of the paper
        
    Returns:
        PaperResponse: Paper information
    """
    paper = PaperDatabase.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get basic section names if available
    section_names = list(paper.sections.keys()) if paper.sections else []
    
    # For failed papers, include diagnostics information
    diagnostics = None
    error_message = None
    error_details = None
    
    if paper.status == PaperStatus.FAILED or paper.status == PaperStatus.ERROR:
        # Check if paper has diagnostics information
        if hasattr(paper, 'diagnostics'):
            diagnostics = paper.diagnostics
        
        # Get error message from processing attempt
        if hasattr(paper, 'error'):
            error_message = paper.error
        elif hasattr(paper, 'details') and isinstance(paper.details, dict) and 'error' in paper.details:
            error_message = paper.details['error']
            
        # Get error details
        if hasattr(paper, 'error_details'):
            error_details = paper.error_details
    
    return PaperResponse(
        id=paper.id,
        title=paper.title,
        status=paper.status,
        paper_type=paper.paper_type,
        sections=section_names,
        diagnostics=diagnostics,
        error_message=error_message,
        error_details=error_details
    )

@router.get("/{paper_id}/sections")
async def get_paper_sections(paper_id: str):
    """
    Get paper sections
    
    Args:
        paper_id: ID of the paper
        
    Returns:
        dict: Paper sections
    """
    paper = PaperDatabase.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    return {"sections": paper.sections}

@router.get("/{paper_id}/section/{section_name}")
async def get_paper_section(paper_id: str, section_name: str):
    """
    Get a specific paper section
    
    Args:
        paper_id: ID of the paper
        section_name: Name of the section
        
    Returns:
        dict: Section information
    """
    paper = PaperDatabase.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if section_name not in paper.sections:
        raise HTTPException(status_code=404, detail="Section not found")
    
    return {"section": paper.sections[section_name]}

@router.get("/{paper_id}/status", response_model=PaperResponse)
async def get_paper_status(paper_id: str):
    """
    Get the processing status of a paper
    """
    paper = PaperDatabase.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # For error or failed papers, include error details
    error_message = None
    error_details = None
    
    # Check for both ERROR and FAILED status
    if paper.status == PaperStatus.ERROR or paper.status == PaperStatus.FAILED:
        if hasattr(paper, 'error'):
            error_message = paper.error
        
        if hasattr(paper, 'error_details'):
            error_details = paper.error_details
    
    return PaperResponse(
        id=paper.id,
        title=paper.title,
        status=paper.status,
        message=f"Paper status: {paper.status.value}", # Use .value for enum string
        error_message=error_message,
        error_details=error_details
    )

@router.post("/test/create-sample", response_model=PaperResponse)
async def create_sample_paper():
    """
    Create a sample paper with mock data for testing purposes
    """
    paper_id = str(uuid.uuid4())
    
    # Create mock components
    components = [
        Component(
            paper_id=paper_id,
            type=ComponentType.DATA_COLLECTION,
            name="MNIST Dataset",
            description="Handwritten digit dataset with 60,000 training examples and 10,000 test examples",
            source_section="Data",
            source_page=3,
            details={
                "source": "http://yann.lecun.com/exdb/mnist/",
                "size": "60,000 training, 10,000 testing",
                "dimensions": "28x28 grayscale images"
            }
        ),
        Component(
            paper_id=paper_id,
            type=ComponentType.PREPROCESSING,
            name="Normalization",
            description="Normalize pixel values to range [0,1]",
            source_section="Methods",
            source_page=4,
            details={
                "method": "Division by 255",
                "input_range": "[0,255]",
                "output_range": "[0,1]"
            }
        ),
        Component(
            paper_id=paper_id,
            type=ComponentType.DATA_PARTITION,
            name="Train-Test Split",
            description="Standard MNIST train/test split",
            source_section="Experimental Setup",
            source_page=5,
            details={
                "train_samples": 60000,
                "test_samples": 10000,
                "validation": "None"
            }
        ),
        Component(
            paper_id=paper_id,
            type=ComponentType.MODEL,
            name="ResNet-18",
            description="Residual Network with 18 layers",
            source_section="Model Architecture",
            source_page=6,
            details={
                "layers": 18,
                "parameters": "11.7 million",
                "activation": "ReLU"
            }
        ),
        Component(
            paper_id=paper_id,
            type=ComponentType.TRAINING,
            name="SGD Training",
            description="Trained with SGD optimizer for 90 epochs",
            source_section="Training Procedure",
            source_page=7,
            details={
                "optimizer": "SGD",
                "learning_rate": 0.1,
                "momentum": 0.9,
                "weight_decay": 1e-4,
                "epochs": 90
            }
        ),
        Component(
            paper_id=paper_id,
            type=ComponentType.EVALUATION,
            name="Top-1 Accuracy",
            description="Evaluated on MNIST test set",
            source_section="Evaluation",
            source_page=8,
            details={
                "metrics": ["accuracy", "error_rate"],
                "test_set": "MNIST test set (10,000 images)"
            }
        ),
        Component(
            paper_id=paper_id,
            type=ComponentType.RESULTS,
            name="Final Results",
            description="99.2% accuracy on test set",
            source_section="Results",
            source_page=9,
            details={
                "accuracy": 0.992,
                "error_rate": 0.008,
                "comparison": "State-of-the-art for simple CNNs on MNIST"
            }
        )
    ]
    
    # Create mock relationships
    relationships = []
    for i in range(len(components) - 1):
        relationships.append(
            Relationship(
                paper_id=paper_id,
                source_id=components[i].id,
                target_id=components[i+1].id,
                type="flow",
                description=f"Flow from {components[i].name} to {components[i+1].name}"
            )
        )
    
    # Add special relationship from data partition to evaluation
    relationships.append(
        Relationship(
            paper_id=paper_id,
            source_id=components[2].id,  # DATA_PARTITION
            target_id=components[5].id,  # EVALUATION
            type="reference",
            description="Test data is used for evaluation"
        )
    )
    
    # Create mock visualization
    mermaid_diagram = """flowchart TD
    A[MNIST Dataset] -->|Raw Data| B[Normalization]
    B -->|Normalized Data| C[Train-Test Split]
    C -->|Training Data| D[ResNet-18]
    D --> E[SGD Training]
    E --> F[Top-1 Accuracy]
    F --> G[Final Results]
    C -.->|Test Data| F
    
    classDef dataCollection fill:#10B981,stroke:#047857,color:white;
    classDef preprocessing fill:#6366F1,stroke:#4338CA,color:white;
    classDef dataPartition fill:#F59E0B,stroke:#B45309,color:white;
    classDef model fill:#EF4444,stroke:#B91C1C,color:white;
    classDef training fill:#8B5CF6,stroke:#6D28D9,color:white;
    classDef evaluation fill:#EC4899,stroke:#BE185D,color:white;
    classDef results fill:#0EA5E9,stroke:#0369A1,color:white;
    
    class A dataCollection;
    class B preprocessing;
    class C dataPartition;
    class D model;
    class E training;
    class F evaluation;
    class G results;"""
    
    visualization = Visualization(
        paper_id=paper_id,
        diagram_type="mermaid",
        diagram_data=mermaid_diagram,
        component_mapping={
            "A": components[0].id,
            "B": components[1].id,
            "C": components[2].id,
            "D": components[3].id,
            "E": components[4].id,
            "F": components[5].id,
            "G": components[6].id
        }
    )
    
    # Create the paper
    paper = Paper(
        id=paper_id,
        title="Deep Residual Learning for Image Recognition",
        status=PaperStatus.COMPLETED,
        components=components,
        relationships=relationships,
        visualization=visualization
    )
    
    # Save to database
    PaperDatabase.add_paper(paper)
    
    return PaperResponse(
        id=paper.id,
        title=paper.title,
        status=paper.status,
        message="Sample paper created successfully"
    )
