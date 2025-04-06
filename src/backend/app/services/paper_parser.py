from app.utils.pdf_extractor import PDFExtractor
from app.utils.ai_processor import AIProcessor
from app.core.models import Paper, Component, Relationship, ComponentType
import logging
import os
import tempfile
import json
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class PaperParser:
    """
    Service for parsing ML research papers and extracting ML workflow components
    """
    
    def __init__(self, ai_api_key: Optional[str] = None):
        """
        Initialize the paper parser
        
        Args:
            ai_api_key: OpenAI API key (optional, will use environment variable if not provided)
        """
        # Use the AIProcessor singleton - any api_key passed will be ignored after first initialization
        self.ai_processor = AIProcessor(api_key=ai_api_key)
    
    async def parse_paper(self, file_path: str, paper_id: str) -> Tuple[List[Component], List[Relationship]]:
        """
        Parse a paper and extract ML workflow components and relationships
        
        Args:
            file_path: Path to the PDF file
            paper_id: ID of the paper record
            
        Returns:
            Tuple[List[Component], List[Relationship]]: Extracted components and relationships
        """
        try:
            # Extract text and structure from PDF
            extractor = PDFExtractor(file_path)
            extraction_result = extractor.extract_all()
            
            if "error" in extraction_result:
                logger.error(f"Error extracting PDF content: {extraction_result['error']}")
                return [], []
            
            # Combine text from all pages
            full_text = "\n".join(extraction_result["text"])
            
            # Analyze paper structure
            structure_result = await self.ai_processor.analyze_paper_structure(full_text)
            
            if "error" in structure_result:
                logger.error(f"Error analyzing paper structure: {structure_result['error']}")
                return [], []
            
            # Extract ML components
            components_result = await self.ai_processor.extract_ml_components(full_text, structure_result)
            
            if "error" in components_result:
                logger.error(f"Error extracting ML components: {components_result['error']}")
                return [], []
            
            # Convert to domain models
            components = []
            for comp_data in components_result.get("components", []):
                try:
                    component_type = ComponentType(comp_data["type"])
                    component = Component(
                        paper_id=paper_id,
                        type=component_type,
                        name=comp_data["name"],
                        description=comp_data.get("description", ""),
                        details=comp_data.get("details", {}),
                        source_section=comp_data.get("source_section"),
                        source_page=comp_data.get("source_page")
                    )
                    components.append(component)
                except Exception as e:
                    logger.error(f"Error creating component: {str(e)}")
            
            # Generate relationships between components
            relationships = self._generate_relationships(paper_id, components)
            
            return components, relationships
            
        except Exception as e:
            logger.error(f"Error parsing paper: {str(e)}")
            return [], []
    
    def _generate_relationships(self, paper_id: str, components: List[Component]) -> List[Relationship]:
        """
        Generate relationships between components based on their types
        
        Args:
            paper_id: ID of the paper record
            components: List of extracted components
            
        Returns:
            List[Relationship]: Generated relationships
        """
        relationships = []
        
        # Sort components by type to establish a logical flow
        type_order = {
            ComponentType.DATA_COLLECTION: 1,
            ComponentType.PREPROCESSING: 2,
            ComponentType.DATA_PARTITION: 3,
            ComponentType.MODEL: 4,
            ComponentType.TRAINING: 5,
            ComponentType.EVALUATION: 6,
            ComponentType.RESULTS: 7
        }
        
        sorted_components = sorted(components, key=lambda c: type_order.get(c.type, 999))
        
        # Create flow relationships between sequential components
        for i in range(len(sorted_components) - 1):
            source = sorted_components[i]
            target = sorted_components[i + 1]
            
            relationship = Relationship(
                paper_id=paper_id,
                source_id=source.id,
                target_id=target.id,
                type="flow",
                description=f"Flow from {source.name} to {target.name}"
            )
            relationships.append(relationship)
        
        # Add special relationships
        # For example, connect data partition to evaluation (test data usage)
        data_partition = next((c for c in components if c.type == ComponentType.DATA_PARTITION), None)
        evaluation = next((c for c in components if c.type == ComponentType.EVALUATION), None)
        
        if data_partition and evaluation:
            relationship = Relationship(
                paper_id=paper_id,
                source_id=data_partition.id,
                target_id=evaluation.id,
                type="reference",
                description="Test data is used for evaluation"
            )
            relationships.append(relationship)
        
        return relationships
