import logging
from typing import Dict, Any, List, Optional, Tuple
import json
import os
from app.services.paper_characterization import PaperCharacterizationService
from app.services.component_extraction import ComponentExtractionService
from app.services.relationship_extraction import RelationshipExtractionService
from app.utils.pdf_extractor import PDFExtractor
from app.core.models import Component, Relationship, PaperType, Section

logger = logging.getLogger(__name__)

class AIExtractionService:
    """
    Orchestrates the multi-stage AI analysis of a research paper
    """
    
    def __init__(self, ai_api_key: Optional[str] = None):
        """
        Initialize the AI extraction service
        
        Args:
            ai_api_key: OpenAI API key (optional, will use environment variable if not provided)
        """
        self.paper_characterization = PaperCharacterizationService(ai_api_key=ai_api_key)
        self.component_extraction = ComponentExtractionService(ai_api_key=ai_api_key)
        self.relationship_extraction = RelationshipExtractionService(ai_api_key=ai_api_key)
    
    async def process_paper(self, paper_path: str, paper_id: str) -> Dict[str, Any]:
        """
        Process a paper with multi-stage AI analysis
        
        Args:
            paper_path: Path to the PDF file
            paper_id: ID of the paper record
            
        Returns:
            Dict[str, Any]: Processed paper data including paper type, sections, and components
        """
        try:
            logger.info(f"Starting multi-stage AI extraction for paper {paper_id}")
            
            # Stage 0: Extract text and structure from PDF
            extractor = PDFExtractor(paper_path)
            extraction_result = extractor.extract_all()
            
            if "error" in extraction_result:
                logger.error(f"Error extracting PDF content: {extraction_result['error']}")
                return {"error": extraction_result["error"]}
            
            # Get full text and extracted sections
            full_text = "\n".join(extraction_result["text"])
            extracted_sections = extraction_result["sections"]
            structured_text = extraction_result["structured_text"]
            
            # Stage 1: Paper characterization (paper type and section mapping)
            logger.info("Stage 1: Paper characterization and section mapping")
            characterization_result = await self.paper_characterization.characterize_paper(full_text)
            
            if "error" in characterization_result:
                logger.error(f"Error in paper characterization: {characterization_result['error']}")
                return {"error": characterization_result["error"]}
            
            # Get paper type and AI-identified sections
            paper_type = characterization_result.get("paper_type", PaperType.UNKNOWN)
            ai_sections = characterization_result.get("sections", {})
            
            # Map AI-identified sections to extracted PDF structure
            mapped_sections = self.paper_characterization.map_sections_to_extracted_structure(
                characterization_result, extracted_sections
            )
            
            # Extract text for each section using location info
            section_texts = {}
            for section_name, section in mapped_sections.items():
                section_text = extractor.extract_section_text(
                    structured_text,
                    section.start_location.model_dump(),
                    section.end_location.model_dump()
                )
                section_texts[section_name] = section_text
            
            # Stage 2: Component extraction based on paper type and sections
            logger.info("Stage 2: Targeted component extraction")
            components = await self.component_extraction.extract_components_from_sections(
                paper_id=paper_id,
                paper_type=paper_type,
                sections=ai_sections,
                section_texts=section_texts
            )
            
            if not components:
                logger.warning("No components extracted from paper")
                return {"error": "Failed to extract components from paper"}
            
            # Stage 3: Relationship identification between components
            logger.info("Stage 3: Relationship identification")
            relationships = await self.relationship_extraction.extract_relationships(
                paper_id=paper_id,
                paper_type=paper_type,
                components=components,
                paper_text=full_text
            )
            
            # Analyze relationships to provide insights
            relationship_analysis = self.relationship_extraction.analyze_relationships(
                components=components,
                relationships=relationships
            )
            
            logger.info(f"Extracted {len(components)} components and {len(relationships)} relationships from paper {paper_id}")
            
            # Return all the extracted information
            return {
                "paper_id": paper_id,
                "paper_type": paper_type,
                "sections": mapped_sections,
                "components": components,
                "relationships": relationships,
                "relationship_analysis": relationship_analysis,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error in AI extraction service: {str(e)}")
            return {"error": str(e), "success": False} 