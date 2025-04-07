import logging
from typing import Dict, Any, List, Optional, Tuple
import json
import os
from app.services.paper_characterization import PaperCharacterizationService
from app.services.component_extraction import ComponentExtractionService
from app.services.relationship_extraction import RelationshipExtractionService
from app.utils.pymupdf_extractor import extract_text_with_pymupdf
from app.utils.mistral_ocr_extractor import extract_text_with_mistral_ocr
from app.core.models import Component, Relationship, PaperType, Section, ComponentType

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
    
    def _validate_paper_type(self, paper_type) -> PaperType:
        """Validate and convert paper type to proper enum."""
        if isinstance(paper_type, str):
            try:
                return PaperType(paper_type)
            except ValueError:
                logger.warning(f"Invalid paper type {paper_type}, falling back to UNKNOWN")
                return PaperType.UNKNOWN
        elif isinstance(paper_type, PaperType):
            return paper_type
        else:
            logger.warning(f"Invalid paper type format {type(paper_type)}, falling back to UNKNOWN")
            return PaperType.UNKNOWN

    def _create_error_response(self, error_msg: str, stage: str, diagnostics: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "error": error_msg,
            "diagnostics": {
                "stage": stage,
                "error": error_msg,
                **(diagnostics or {})
            },
            "success": False
        }

    async def process_paper(self, paper_path: str, paper_id: str, parser_type: str = "pymupdf") -> Dict[str, Any]:
        """
        Process a paper with multi-stage AI analysis
        
        Args:
            paper_path: Path to the PDF file
            paper_id: ID of the paper record
            parser_type: The PDF parser to use ('pymupdf' or 'mistral_ocr'). Defaults to 'pymupdf'.
            
        Returns:
            Dict[str, Any]: Processed paper data including paper type, sections, and components
        """
        try:
            logger.info(f"Starting multi-stage AI extraction for paper {paper_id} using parser: {parser_type}")
            
            # Store diagnostics for paper processing
            diagnostics = {
                "parser_used": parser_type,
                "extraction_stages": {},
                "timings": {},
                "file_info": {}
            }
            
            import time
            start_time = time.time()
            
            # Stage 0: Extract text and structure from PDF using the chosen parser
            full_text = None
            extraction_error = None
            structured_content = None
            extracted_sections = []
            
            try:
                if parser_type == "pymupdf":
                    logger.info(f"Using PyMuPDF extractor for {paper_path}")
                    full_text, extraction_error = extract_text_with_pymupdf(paper_path)
                    structured_content = {"type": "text", "content": full_text}
                
                elif parser_type == "mistral_ocr":
                    logger.info(f"Using Mistral OCR extractor for {paper_path}")
                    markdown_text, extraction_error = await extract_text_with_mistral_ocr(paper_path)
                    if not extraction_error:
                        full_text = markdown_text
                        structured_content = {"type": "markdown", "content": markdown_text}
                        logger.info(f"Received {len(full_text)} chars of Markdown from Mistral OCR.")
                    else:
                        logger.error(f"Mistral OCR extraction failed: {extraction_error}")
                else:
                    return self._create_error_response(f"Unsupported parser type: {parser_type}", "pdf_extraction")
            except Exception as e:
                return self._create_error_response(f"PDF extraction failed: {str(e)}", "pdf_extraction")

            if extraction_error:
                return self._create_error_response(extraction_error, "pdf_extraction", diagnostics)

            if not full_text:
                return self._create_error_response(
                    f"No text could be extracted from the PDF using {parser_type}.",
                    "pdf_extraction",
                    diagnostics
                )

            # Record file info
            import os
            file_size_kb = os.path.getsize(paper_path) / 1024 if os.path.exists(paper_path) else 0
            diagnostics["file_info"].update({
                "file_size_kb": file_size_kb,
                "text_length": len(full_text),
                "content_type_extracted": structured_content.get("type") if structured_content else "unknown",
            })
            
            # Get full text and potentially extracted sections (depends on parser)
            # full_text = "\\n".join(extraction_result["text"]) # Now directly assigned above
            # extracted_sections = extraction_result["sections"] # Need to adapt based on parser output
            # structured_text = extraction_result["structured_text"] # Need to adapt based on parser output
            
            diagnostics["extraction_stages"]["pdf_extraction"] = {
                "status": "success",
                "text_length": len(full_text),
                "content_type": structured_content.get("type") if structured_content else "unknown",
            }
            diagnostics["timings"]["pdf_extraction"] = time.time() - start_time
            stage_start_time = time.time()
            
            # --- The rest of the stages (Characterization, Component Extraction, Relationships) ---
            # These stages currently rely on `full_text`. 
            # If using Mistral OCR later, `structured_text` (Markdown) might be more valuable.
            # We may need to adapt the prompts or processing in these stages depending on the input format.
            
            # Stage 1: Paper characterization with enhanced error handling
            logger.info("Stage 1: Paper characterization and section mapping")
            validated_paper_type = PaperType.UNKNOWN # Initialize with default
            ai_sections = {} # Initialize with default
            try:
                characterization_result = await self.paper_characterization.characterize_paper(full_text)
                
                if "error" in characterization_result:
                    return self._create_error_response(
                        characterization_result["error"],
                        "paper_characterization",
                        {**diagnostics, "text_sample": full_text[:500] + "..." if len(full_text) > 500 else full_text}
                    )
                
                # Validate paper type and store it
                raw_paper_type = characterization_result.get("paper_type")
                validated_paper_type = self._validate_paper_type(raw_paper_type)
                ai_sections = characterization_result.get("sections", {})
                
            except Exception as e:
                return self._create_error_response(
                    f"Paper characterization failed: {str(e)}",
                    "paper_characterization",
                    diagnostics
                )
            
            diagnostics["extraction_stages"]["characterization"] = {
                "status": "success",
                "paper_type": validated_paper_type.value, # Use validated type for diagnostics
                "ai_sections_found": len(ai_sections),
            }
            diagnostics["timings"]["characterization"] = time.time() - stage_start_time
            stage_start_time = time.time()
            
            # Map AI-identified sections to extracted PDF structure (IF available from parser)
            # mapped_sections = self.paper_characterization.map_sections_to_extracted_structure(
            #     characterization_result, extracted_sections 
            # )
            # For PyMuPDF basic text, we might skip detailed mapping for now or rely solely on AI sections
            mapped_sections = characterization_result.get("sections", {}) # Use AI sections directly for now

            # Extract text for each section using location info (IF available from parser)
            # section_texts = {}
            # for section_name, section in mapped_sections.items():
            #     # Need a way to get text per section if parser doesn't provide it.
            #     # Fallback: Pass full_text to component extraction? Or try simple text splitting?
            #     section_texts[section_name] = full_text # Simplistic fallback: use full text for all sections

            # Let's refine section text extraction later. For now, pass full text to component extractor.
            ai_sections = characterization_result.get("sections", {})

            # Stage 2: Component extraction based on paper type and sections
            logger.info("Stage 2: Targeted component extraction")
            components: List[Component] = []
            try:
                # Check if component extraction service has the new method signature
                if hasattr(self.component_extraction, 'extract_components_from_text'):
                     components = await self.component_extraction.extract_components_from_text(
                        paper_id=paper_id,
                        paper_type=validated_paper_type, # Pass the validated type
                        paper_text=full_text
                    )
                # Fallback to older method if needed (or remove if extract_components_from_text is guaranteed)
                elif hasattr(self.component_extraction, 'extract_components_from_sections'): 
                     # This path requires section_texts which we haven't fully implemented yet
                     # For now, we'll likely rely on extract_components_from_text or the fallback within it.
                     logger.warning("Using extract_components_from_sections - section text extraction might be basic.")
                     # Simplified section_texts for now
                     section_texts = {name: full_text for name in mapped_sections.keys()} if mapped_sections else {"full_paper": full_text}
                     components = await self.component_extraction.extract_components_from_sections(
                        paper_id=paper_id,
                        paper_type=validated_paper_type, # Pass the validated type
                        sections=mapped_sections, # Use mapped sections if available
                        section_texts=section_texts
                     )
                else:
                     logger.error("ComponentExtractionService has no recognized extraction method.")
                     # Handle error - maybe return an error response
                     return self._create_error_response(
                        "Component extraction method not found",
                        "component_extraction",
                        diagnostics
                    )

            except Exception as e:
                 logger.error(f"Component extraction stage failed: {str(e)}")
                 return self._create_error_response(
                    f"Component extraction failed: {str(e)}",
                    "component_extraction",
                    diagnostics
                )
            
            # Check if we have valid components
            if not components or len(components) == 0:
                logger.error("Component extraction completed but no components were returned.")
                return self._create_error_response(
                    "Component extraction produced no components",
                    "component_extraction",
                    diagnostics
                )
                
            # Record component extraction results
            diagnostics["extraction_stages"]["component_extraction"] = {
                "status": "success",
                "components_found": len(components),
                "component_types": list(set([c.type.value for c in components if hasattr(c, 'type')])),
            }
            diagnostics["timings"]["component_extraction"] = time.time() - stage_start_time
            stage_start_time = time.time()
            
            # Stage 3: Relationship identification (using validated paper_type)
            logger.info("Stage 3: Relationship identification")
            relationships: List[Relationship] = []
            try:
                # Call using positional arguments to match the definition exactly
                relationships = await self.relationship_extraction.extract_relationships(
                    paper_id,                # 1st arg (after self)
                    validated_paper_type,    # 2nd arg
                    components,              # 3rd arg
                    full_text                # 4th arg
                )
            except TypeError as te:
                 # Add specific logging for TypeError to see if it provides more info
                 logger.error(f"TypeError during relationship extraction: {str(te)}")
                 logger.exception("Full traceback for TypeError:") # Log full traceback
                 diagnostics["extraction_stages"]["relationship_extraction"] = {"status": "failed", "error": f"TypeError: {str(te)}"}
            except Exception as e:
                 error_msg = f"Relationship extraction stage failed: {str(e)}"
                 logger.error(error_msg)
                 # Decide how to handle: continue with no relationships or return error?
                 # For now, log and continue.
                 diagnostics["extraction_stages"]["relationship_extraction"] = {"status": "failed", "error": error_msg}

            # Analyze relationships to provide insights
            relationship_analysis = self.relationship_extraction.analyze_relationships(
                components=components,
                relationships=relationships
            )
            
            diagnostics["extraction_stages"]["relationship_extraction"] = {
                "status": "success",
                "relationships_extracted": len(relationships)
            }
            diagnostics["timings"]["relationship_extraction"] = time.time() - stage_start_time
            diagnostics["timings"]["total"] = time.time() - start_time
            
            logger.info(f"Extracted {len(components)} components and {len(relationships)} relationships from paper {paper_id}")
            
            # Final return dictionary
            final_success_status = True # Assume success unless an error occurred
            final_error_message = None
            
            # Check if any stage explicitly returned an error dictionary that bubbled up
            # (We modified the main try-except to return self._create_error_response)
            # If we reached this point without an exception, it implies individual stages might 
            # have handled their errors internally but we should check diagnostics.
            
            # A simpler approach: If we ended up with only minimal components, it wasn't a true success.
            is_minimal_only = len(components) == 1 and components[0].name.startswith("Paper Content")
            
            if is_minimal_only:
                logger.warning("Extraction resulted in minimal components only. Reporting as partial success/failure.")
                # Decide if this counts as success=False or maybe a different status.
                # For now, let's keep success=True but rely on frontend to interpret based on component count.
            
            return {
                "paper_id": paper_id,
                "paper_type": validated_paper_type,
                "components": components,
                "relationships": relationships,
                "relationship_analysis": relationship_analysis,
                "diagnostics": diagnostics,
                "success": True # Keep True for now, but frontend should check component count/diagnostics
            }
            
        except Exception as e:
            # Log the full exception traceback for debugging
            logger.exception(f"Critical error in AI extraction service for paper {paper_id}: {e}") 
            # Ensure error response uses the helper to include success: False
            return self._create_error_response(
                 f"An unexpected error occurred during AI processing: {e}",
                 "critical_error",
                 diagnostics
            )

    def _section_to_component_type(self, section_name: str) -> ComponentType:
        """Map section names to component types for minimal component creation"""
        section_lower = section_name.lower()
        
        if any(term in section_lower for term in ["method", "approach", "model", "architecture"]):
            return ComponentType.MODEL
        elif any(term in section_lower for term in ["data", "dataset"]):
            return ComponentType.DATA_COLLECTION
        elif any(term in section_lower for term in ["result", "evaluation", "experiment"]):
            return ComponentType.RESULTS
        elif "introduction" in section_lower:
            return ComponentType.OTHER
        elif "conclusion" in section_lower:
            return ComponentType.OTHER
        elif "abstract" in section_lower:
            return ComponentType.OTHER
        else:
            return ComponentType.OTHER 