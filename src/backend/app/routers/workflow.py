from fastapi import APIRouter, Path, HTTPException, Depends
from typing import Dict, Any, List, Optional
import json

from app.core.models import Paper, Component, Relationship, PaperStatus, ComponentType, PaperDatabase

router = APIRouter()

@router.get("/{paper_id}/components")
async def get_workflow_components(
    paper_id: str = Path(..., description="The ID of the paper")
):
    """
    Get the ML workflow components for a paper
    """
    paper = PaperDatabase.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if paper.status != PaperStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Paper processing is not complete (status: {paper.status})")
    
    return {"components": paper.components}

@router.get("/{paper_id}/components/{component_id}")
async def get_workflow_component(
    paper_id: str = Path(..., description="The ID of the paper"),
    component_id: str = Path(..., description="The ID of the component")
):
    """
    Get details for a specific ML workflow component
    """
    paper = PaperDatabase.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    component = next((c for c in paper.components if c.id == component_id), None)
    
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    
    return component

@router.get("/{paper_id}/relationships")
async def get_workflow_relationships(
    paper_id: str = Path(..., description="The ID of the paper")
):
    """
    Get the relationships between ML workflow components for a paper
    """
    paper = PaperDatabase.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if paper.status != PaperStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Paper processing is not complete (status: {paper.status})")
    
    return {"relationships": paper.relationships}

@router.get("/{paper_id}/summary")
async def get_workflow_summary(
    paper_id: str = Path(..., description="The ID of the paper")
):
    """
    Get a summary of the ML workflow for a paper
    """
    paper = PaperDatabase.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    if paper.status != PaperStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Paper processing is not complete (status: {paper.status})")
    
    # Create a summary of the workflow
    summary = {
        "paper_id": paper.id,
        "title": paper.title,
        "component_counts": {},
        "total_components": len(paper.components),
        "total_relationships": len(paper.relationships)
    }
    
    # Count components by type
    for component_type in ComponentType:
        count = len([c for c in paper.components if c.type == component_type])
        if count > 0:
            summary["component_counts"][component_type] = count
    
    return summary

@router.get("/{paper_id}/relationships/analysis")
async def get_workflow_relationship_analysis(paper_id: str):
    """
    Get the relationship analysis for a paper workflow
    
    Args:
        paper_id: ID of the paper
        
    Returns:
        dict: Relationship analysis data
    """
    paper = PaperDatabase.get_paper(paper_id)
    
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Get relationship analysis from paper details
    relationship_analysis = paper.details.get("relationship_analysis", {}) if hasattr(paper, "details") else {}
    
    return {
        "paper_id": paper_id,
        "relationship_analysis": relationship_analysis
    }

@router.get("/relationship-types")
async def get_workflow_relationship_types():
    """
    Get all available relationship types with descriptions
    
    Returns:
        dict: Map of relationship types and descriptions
    """
    relationship_types = {
        "flow": "Data or processing flow from one component to another (X is input to Y)",
        "uses": "One component uses or depends on another (X uses Y)",
        "contains": "Hierarchical relationship (X contains Y)",
        "evaluates": "Evaluation relationship (X evaluates Y)",
        "compares": "Comparison relationship (X is compared to Y)",
        "improves": "Improvement relationship (X improves upon Y)",
        "part_of": "Component is part of another (X is part of Y)"
    }
    
    return {
        "relationship_types": relationship_types
    }
