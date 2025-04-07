"""
AI processing service for extracting components from text.
This file provides functions for extracting ML workflow components from research papers.
"""
import logging
from typing import Dict, Any, List, Tuple
from app.core.models import Component, Relationship, PaperType

logger = logging.getLogger(__name__)

async def extract_components_from_text(
    paper_id: str,
    paper_text: str,
    paper_type: PaperType = PaperType.UNKNOWN
) -> Tuple[List[Component], List[Relationship]]:
    """
    Extract components and relationships from paper text
    
    This is a simple wrapper that delegates to the ComponentExtractionService's 
    extract_components_from_text method and adds relationship extraction.
    
    Args:
        paper_id: ID of the paper
        paper_text: Full text of the paper
        paper_type: Type of the paper
        
    Returns:
        Tuple[List[Component], List[Relationship]]: Extracted components and relationships
    """
    from app.services.component_extraction import ComponentExtractionService
    from app.services.relationship_extraction import RelationshipExtractionService
    
    logger.info(f"Extracting components and relationships from text for paper {paper_id}")
    
    # Initialize the services
    component_extraction = ComponentExtractionService()
    relationship_extraction = RelationshipExtractionService()
    
    # Extract components
    components = await component_extraction.extract_components_fallback(
        paper_id=paper_id,
        paper_type=paper_type,
        combined_text=paper_text
    )
    
    # If no components were found, return empty lists
    if not components:
        logger.warning(f"No components found in paper {paper_id}")
        return [], []
    
    # Extract relationships between components
    relationships = await relationship_extraction.extract_relationships(
        paper_id=paper_id,
        paper_type=paper_type,
        components=components,
        paper_text=paper_text
    )
    
    logger.info(f"Extracted {len(components)} components and {len(relationships)} relationships from paper {paper_id}")
    
    return components, relationships 