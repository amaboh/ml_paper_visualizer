from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import uuid
import os
import tempfile
import aiofiles
import logging

from app.core.models import Paper, PaperStatus, PaperResponse, PaperUpload, PaperDatabase, Component, ComponentType, Relationship, Visualization

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload", response_model=PaperResponse)
async def upload_paper(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None)
):
    """
    Upload a paper file or provide a URL to a paper
    """
    if file is None and url is None:
        raise HTTPException(status_code=400, detail="Either file or URL must be provided")
    
    paper_id = str(uuid.uuid4())
    
    if file:
        # Create a new paper record
        paper = Paper(
            id=paper_id,
            status=PaperStatus.UPLOADED,
            title=file.filename
        )
        
        # Save paper to database
        PaperDatabase.add_paper(paper)
        
        # Import here to avoid circular imports
        from app.services.paper_service import process_paper_file, process_paper_path
        
        try:
            # Create a temporary file to store the uploaded PDF
            temp_path = None
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_path = temp_file.name
                
                # Save the uploaded file to the temporary location
                content = await file.read()
                with open(temp_path, 'wb') as out_file:
                    out_file.write(content)
            
            # Process the file in the background, passing the file path instead of the UploadFile
            background_tasks.add_task(process_paper_path, paper, temp_path)
            
            return PaperResponse(
                id=paper.id,
                title=paper.title,
                status=paper.status,
                message="Paper upload received and processing started"
            )
        except Exception as e:
            logger.error(f"Error saving uploaded file: {str(e)}")
            paper.status = PaperStatus.FAILED
            PaperDatabase.update_paper(paper)
            raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")
    
    elif url:
        # Create a new paper record
        paper = Paper(
            id=paper_id,
            status=PaperStatus.UPLOADED,
            url=url
        )
        
        # Save paper to database
        PaperDatabase.add_paper(paper)
        
        # Import here to avoid circular imports
        from app.services.paper_service import process_paper_url
        
        # Process the URL in the background
        background_tasks.add_task(process_paper_url, paper, url)
        
        return PaperResponse(
            id=paper.id,
            title=None,
            status=paper.status,
            message="Paper URL received and processing started"
        )

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
    
    return PaperResponse(
        id=paper.id,
        title=paper.title,
        status=paper.status,
        paper_type=paper.paper_type,
        sections=section_names
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
    
    return PaperResponse(
        id=paper.id,
        title=paper.title,
        status=paper.status,
        message=f"Paper status: {paper.status}"
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
