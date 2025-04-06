from fastapi import APIRouter, Path, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
from app.core.models import Visualization, VisualizationSettings, Paper, PaperStatus, ComponentType, PaperDatabase

router = APIRouter()

@router.get("/{paper_id}", response_model=Dict[str, Any])
async def get_visualization(paper_id: str):
    """
    Get the visualization data for a paper's ML workflow
    """
    # This would normally fetch from a database and generate visualization
    # For now, return a mock response with sample Mermaid.js diagram data
    
    # Sample Mermaid.js flowchart for ML workflow
    mermaid_diagram = """
    flowchart TD
        A[MNIST Dataset] -->|Raw Data| B[Normalization]
        B -->|Normalized Data| C[Train-Test Split]
        C -->|Training Data| D[Convolutional Neural Network]
        D --> E[Model Training]
        E --> F[Model Evaluation]
        F --> G[Results: 99.2% Accuracy]
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
        class G results;
    """
    
    # Component metadata for interactive features
    component_metadata = {
        "A": {
            "id": "comp1",
            "type": "data_collection",
            "name": "MNIST Dataset",
            "description": "Handwritten digit dataset with 60,000 training examples and 10,000 test examples",
            "source_section": "Data",
            "source_page": 3
        },
        "B": {
            "id": "comp2",
            "type": "preprocessing",
            "name": "Normalization",
            "description": "Normalize pixel values to range [0,1]",
            "source_section": "Methods",
            "source_page": 4
        },
        "C": {
            "id": "comp3",
            "type": "data_partition",
            "name": "Train-Test Split",
            "description": "Use predefined train-test split from MNIST",
            "source_section": "Experimental Setup",
            "source_page": 5
        },
        "D": {
            "id": "comp4",
            "type": "model",
            "name": "Convolutional Neural Network",
            "description": "3-layer CNN with max pooling and dropout",
            "source_section": "Model Architecture",
            "source_page": 6
        },
        "E": {
            "id": "comp5",
            "type": "training",
            "name": "Model Training",
            "description": "Trained using Adam optimizer with categorical cross-entropy loss",
            "source_section": "Training",
            "source_page": 7
        },
        "F": {
            "id": "comp6",
            "type": "evaluation",
            "name": "Model Evaluation",
            "description": "Evaluated on test set using accuracy and confusion matrix",
            "source_section": "Evaluation",
            "source_page": 8
        },
        "G": {
            "id": "comp7",
            "type": "results",
            "name": "Results",
            "description": "Achieved 99.2% accuracy on the test set",
            "source_section": "Results",
            "source_page": 9
        }
    }
    
    return {
        "paper_id": paper_id,
        "diagram_type": "mermaid",
        "diagram_data": mermaid_diagram,
        "component_metadata": component_metadata,
        "settings": {
            "layout": "vertical",
            "theme": "default",
            "detail_level": "standard"
        }
    }

@router.post("/{paper_id}/customize", response_model=Dict[str, Any])
async def customize_visualization(
    paper_id: str,
    settings: VisualizationSettings
):
    """
    Customize the visualization settings for a paper
    """
    # This would normally update settings in the database
    # For now, return the same visualization with updated settings
    visualization = await get_visualization(paper_id)
    visualization["settings"] = {
        "layout": settings.layout,
        "theme": settings.theme,
        "detail_level": settings.detail_level,
        "component_filters": [comp.value for comp in settings.component_filters]
    }
    
    return visualization

@router.get("/{paper_id}/export", response_model=Dict[str, Any])
async def export_visualization(
    paper_id: str,
    format: str = Query("svg", description="Export format (svg, png, html)")
):
    """
    Export the visualization in various formats
    """
    # This would normally generate the requested format
    # For now, return a mock response
    visualization = await get_visualization(paper_id)
    
    return {
        "paper_id": paper_id,
        "format": format,
        "data": visualization["diagram_data"],
        "message": f"Visualization exported as {format}"
    }

@router.get("/{paper_id}/diagram")
async def get_visualization_diagram(
    paper_id: str = Path(..., description="The ID of the paper"),
    format: str = Query("mermaid", description="Visualization format (mermaid or d3)")
):
    """
    Get visualization diagram for a paper
    """
    paper = PaperDatabase.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if paper.status != PaperStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Paper is not ready for visualization (status: {paper.status})")
    
    if not paper.visualization:
        raise HTTPException(status_code=404, detail="Visualization not found for this paper")
    
    # Return the diagram data based on the requested format
    if format == "mermaid":
        return {
            "type": "mermaid",
            "data": paper.visualization.diagram_data
        }
    else:
        raise HTTPException(status_code=400, detail=f"Visualization format '{format}' not supported")

@router.get("/{paper_id}/components")
async def get_visualization_components(
    paper_id: str = Path(..., description="The ID of the paper"),
    component_types: Optional[List[ComponentType]] = Query(None, description="Filter by component types")
):
    """
    Get components for a paper visualization
    """
    paper = PaperDatabase.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if paper.status != PaperStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Paper is not ready for visualization (status: {paper.status})")
    
    if not paper.components:
        raise HTTPException(status_code=404, detail="Components not found for this paper")
    
    # Filter components if component_types is provided
    if component_types:
        filtered_components = [c for c in paper.components if c.type in component_types]
        return {"components": filtered_components}
    
    return {"components": paper.components}

@router.get("/{paper_id}/relationships")
async def get_visualization_relationships(
    paper_id: str = Path(..., description="The ID of the paper")
):
    """
    Get relationships for a paper visualization
    """
    paper = PaperDatabase.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if paper.status != PaperStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Paper is not ready for visualization (status: {paper.status})")
    
    if not paper.relationships:
        raise HTTPException(status_code=404, detail="Relationships not found for this paper")
    
    return {"relationships": paper.relationships}

@router.get("/{paper_id}/component/{component_id}")
async def get_component_details(
    paper_id: str = Path(..., description="The ID of the paper"),
    component_id: str = Path(..., description="The ID of the component")
):
    """
    Get detailed information about a specific component
    """
    paper = PaperDatabase.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if paper.status != PaperStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Paper is not ready for visualization (status: {paper.status})")
    
    # Find the component by ID
    component = next((c for c in paper.components if c.id == component_id), None)
    
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    return component
