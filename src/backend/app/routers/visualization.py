from fastapi import APIRouter, Path, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Dict, Any, Optional, List
from app.core.models import Visualization, VisualizationSettings, Paper, PaperStatus, ComponentType, PaperDatabase, Component, Relationship
from app.services.visualization_generator import VisualizationGenerator

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
    paper_id: str = Path(..., description="The ID of the paper"),
    format: str = Query("svg", description="Export format (svg, png, json)")
):
    """
    Export the visualization in various formats
    """
    paper = PaperDatabase.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if paper.status != PaperStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Paper is not ready for visualization (status: {paper.status})")
    
    if format.lower() == "svg":
        # For SVG, we can return the Mermaid diagram rendered as SVG
        if not paper.visualization or not paper.visualization.diagram_data:
            raise HTTPException(status_code=404, detail="Visualization data not found")
        
        # In a real implementation, this would convert Mermaid to SVG
        # For now, we'll return an SVG placeholder
        svg_data = f'''
        <svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
            <style>
                text {{ font-family: Arial, sans-serif; font-size: 12px; }}
                .title {{ font-size: 16px; font-weight: bold; }}
            </style>
            <text x="400" y="20" text-anchor="middle" class="title">{paper.title}</text>
            <!-- This would be the actual SVG content generated from Mermaid -->
        </svg>
        '''
        
        return {
            "paper_id": paper_id,
            "format": "svg",
            "data": svg_data,
            "filename": f"{paper.title.replace(' ', '_')}_visualization.svg"
        }
    
    elif format.lower() == "json":
        # For JSON, return the structured data used for visualizations
        d3_data = await get_d3_visualization(paper_id)
        mermaid_data = await get_mermaid_visualization(paper_id)
        
        export_data = {
            "paper": {
                "id": paper.id,
                "title": paper.title,
                "status": paper.status,
                "paper_type": paper.paper_type if hasattr(paper, "paper_type") else None
            },
            "components": [dict(comp) for comp in paper.components],
            "relationships": [dict(rel) for rel in paper.relationships],
            "d3_visualization": d3_data,
            "mermaid_visualization": mermaid_data
        }
        
        return {
            "paper_id": paper_id,
            "format": "json",
            "data": export_data,
            "filename": f"{paper.title.replace(' ', '_')}_data.json"
        }
    
    elif format.lower() == "png":
        # For PNG, we would need to render SVG and convert to PNG
        # This would typically be handled by a service like Puppeteer
        # For now, return an error indicating this is not implemented
        raise HTTPException(status_code=501, detail="PNG export is handled client-side for now")
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported export format: {format}")

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

@router.get("/{paper_id}/mermaid", response_model=Dict[str, Any])
async def get_mermaid_visualization(
    paper_id: str = Path(..., description="The ID of the paper")
):
    """
    Get Mermaid diagram data for a paper's ML workflow
    """
    paper = PaperDatabase.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if paper.status != PaperStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Paper is not ready for visualization (status: {paper.status})")
    
    if not paper.visualization or not paper.visualization.diagram_data:
        raise HTTPException(status_code=404, detail="Mermaid diagram data not found for this paper")
    
    return {
        "diagram_data": paper.visualization.diagram_data
    }

@router.get("/{paper_id}/d3", response_model=Dict[str, Any])
async def get_d3_visualization(
    paper_id: str = Path(..., description="The ID of the paper")
):
    """
    Get D3 visualization data for a paper's ML workflow
    """
    paper = PaperDatabase.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if paper.status != PaperStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Paper is not ready for visualization (status: {paper.status})")
    
    # Handle case where there are no components or relationships
    if not paper.components:
        # Return minimal D3 data with a placeholder node
        return {
            "nodes": [{
                "id": "minimal_component",
                "name": f"Paper: {paper.title if hasattr(paper, 'title') and paper.title else paper.id}",
                "type": "other",
                "description": "This paper's content could not be automatically parsed into specific components.",
                "details": {
                    "extraction_note": "Automatic extraction created minimal components only."
                }
            }],
            "links": [],
            "hierarchical_nodes": [],
            "is_minimal": True
        }
    
    # Create a copy of components to work with
    nodes = [dict(comp) for comp in paper.components]
    
    # Organize nodes into a hierarchical structure
    hierarchical_nodes = []
    component_map = {comp["id"]: comp for comp in nodes}
    
    # Initialize links list
    links = []
    
    # Process relationships if they exist
    if paper.relationships:
        # Identify potential parent-child relationships
        for rel in paper.relationships:
            # Check if it's a part_of or contains relationship
            if rel.type in ["part_of", "contains", "component_of", "sub_module"]:
                # Get the components
                if rel.source_id in component_map and rel.target_id in component_map:
                    # In "part_of" relationships, source is the child, target is the parent
                    parent_comp = component_map[rel.target_id]
                    child_comp = component_map[rel.source_id]
                    
                    # Add hierarchy information
                    child_comp["parent"] = parent_comp["id"]
                    
                    # Initialize or add to children list
                    if "children" not in parent_comp:
                        parent_comp["children"] = []
                    
                    parent_comp["children"].append(child_comp)
        
        # Format links for D3
        for rel in paper.relationships:
            # Skip the hierarchical relationships already represented in the node structure
            if rel.type not in ["part_of", "contains", "component_of", "sub_module"]:
                links.append({
                    "source": rel.source_id,
                    "target": rel.target_id,
                    "type": rel.type, 
                    "description": rel.description
                })
    
    # Extract top-level components (those without parents)
    for comp_id, comp in component_map.items():
        if "parent" not in comp:
            hierarchical_nodes.append(comp)
    
    return {
        "nodes": nodes,  # Include all nodes for reference
        "links": links,
        "hierarchical_nodes": hierarchical_nodes,  # Top-level nodes with children
        "is_minimal": len(paper.components) == 1  # Flag if this is just a minimal component
    }

@router.get("/{paper_id}/simple_svg", response_class=PlainTextResponse)
async def get_simple_svg_visualization(
    paper_id: str = Path(..., description="The ID of the paper")
):
    """
    Get a simple SVG representation of the paper's ML workflow.
    """
    paper = PaperDatabase.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if paper.status != PaperStatus.COMPLETED:
        # Allow generating even if processing, but might be incomplete
        if paper.status != PaperStatus.PROCESSING:
             raise HTTPException(status_code=400, detail=f"Paper cannot be visualized (status: {paper.status})")
    
    if not paper.components:
        # Return an SVG indicating no components
        return PlainTextResponse(
            content='<svg width="300" height="100" xmlns="http://www.w3.org/2000/svg"><text x="10" y="50" fill="#cc0000">No components extracted for this paper.</text></svg>',
            media_type="image/svg+xml"
        )
        
    # Instantiate the generator and create SVG
    viz_generator = VisualizationGenerator()
    svg_string = viz_generator.generate_simple_svg(paper.components, paper.relationships or [])
    
    return PlainTextResponse(content=svg_string, media_type="image/svg+xml")
