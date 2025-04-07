import logging
from typing import Dict, Any, List, Optional
import json
from app.utils.ai_processor import AIProcessor
from app.core.models import PaperType, Section, LocationInfo

logger = logging.getLogger(__name__)

# Define constant for text truncation
MAX_TEXT_LENGTH = 15000 # Adjust as needed based on model context window and desired detail

PAPER_CHARACTERIZATION_PROMPT = """
You are an expert in analyzing scientific research papers, especially ML/AI papers. Analyze this research paper and provide:

1. Paper Type: Classify as one of: 
   - NEW_ARCHITECTURE (introduces a new model/architecture)
   - SURVEY (reviews existing literature)
   - APPLICATION (applies existing methods to a new domain)
   - THEORETICAL (focuses on theoretical aspects without implementation)
   - UNKNOWN (if unclear)

2. Key Sections: Identify and map the following sections in the paper:
   - Abstract
   - Introduction
   - Related Work
   - Background
   - Methods/Methodology/Approach
   - Model Architecture
   - Data
   - Experiments
   - Results
   - Evaluation
   - Discussion
   - Conclusion
   - References

For each section you identify, provide:
- Section name (standardized to one of the above)
- Original section title as it appears in the paper
- A brief 1-2 sentence summary of the section's content

Return the results as a structured JSON object with this format:
{
  "paper_type": "TYPE",
  "sections": {
    "section_name": {
      "title": "Original Title",
      "summary": "Brief summary"
    },
    ...
  }
}
"""

class PaperCharacterizationService:
    """
    Service for characterizing research papers by type and identifying key sections
    """
    
    def __init__(self, ai_api_key: Optional[str] = None):
        """
        Initialize the paper characterization service
        
        Args:
            ai_api_key: OpenAI API key (optional, will use environment variable if not provided)
        """
        # Use the AIProcessor singleton
        self.ai_processor = AIProcessor(api_key=ai_api_key)
    
    def _validate_paper_type(self, paper_type_str: str) -> PaperType:
        """Validate and convert paper type string to enum."""
        try:
            return PaperType(paper_type_str.lower())
        except (ValueError, AttributeError):
            logger.warning(f"Invalid paper type {paper_type_str}, falling back to UNKNOWN")
            return PaperType.UNKNOWN

    def _validate_section(self, section_data: Dict[str, Any]) -> Optional[Section]:
        """Validate and create a section with proper error handling."""
        try:
            required_fields = ['name', 'title']
            for field in required_fields:
                if not section_data.get(field):
                    logger.warning(f"Missing required field {field} in section data")
                    return None

            # Create location info with validation
            start_location = LocationInfo(
                page=section_data.get('start_location', {}).get('page'),
                paragraph=section_data.get('start_location', {}).get('paragraph'),
                position=section_data.get('start_location', {}).get('position')
            )
            
            end_location = LocationInfo(
                page=section_data.get('end_location', {}).get('page'),
                paragraph=section_data.get('end_location', {}).get('paragraph'),
                position=section_data.get('end_location', {}).get('position')
            )

            return Section(
                name=section_data['name'],
                title=section_data['title'],
                start_location=start_location,
                end_location=end_location,
                summary=section_data.get('summary', ''),
                text=section_data.get('text')
            )
        except Exception as e:
            logger.error(f"Error creating section: {e}")
            return None

    async def characterize_paper(self, text: str) -> Dict[str, Any]:
        """Characterize paper with enhanced error handling."""
        try:
            # Validate input
            if not text or len(text.strip()) == 0:
                 return {"error": "Empty text provided...", "success": False} # Added success flag

            # Process with AI, forcing JSON output
            response_str = await self.ai_processor.process_text(
                prompt=PAPER_CHARACTERIZATION_PROMPT + text[:MAX_TEXT_LENGTH], 
                force_json=True # Request JSON output format
            )

            try:
                # First attempt: Direct JSON parsing
                result = json.loads(response_str)
                if isinstance(result, dict) and "error" in result:
                     # Handle potential error returned from AIProcessor
                     logger.error(f"AI processor returned an error: {result['error']}")
                     return {**result, "success": False}
                     
            except json.JSONDecodeError as e1:
                logger.warning(f"Direct JSON parsing failed ({e1}). Trying markdown extraction...")
                # Second attempt: Extract from markdown code block
                import re
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_str, re.MULTILINE)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1))
                        logger.info("Successfully parsed JSON extracted from markdown block.")
                    except json.JSONDecodeError as e2:
                        logger.error(f"Failed to parse extracted JSON: {e2}")
                        return {
                            "error": "Failed to parse extracted JSON content",
                            "raw_response": response_str,
                            "success": False
                        }
                else:
                    # Failed both direct and markdown parsing
                    logger.error(f"Failed to parse AI response as JSON (Direct & Markdown): {response_str[:500]}...")
                    return {
                        "error": "Failed to parse paper characterization response (Not valid JSON)",
                        "raw_response": response_str, 
                        "success": False
                    }
            
            # Ensure result is a dictionary before proceeding
            if not isinstance(result, dict):
                 logger.error(f"Parsed result is not a dictionary: {type(result)}")
                 return {
                      "error": "Parsed AI response was not a valid dictionary structure.",
                      "success": False
                 }

            # Validate paper type
            paper_type = self._validate_paper_type(result.get('paper_type', 'unknown'))

            # Validate and process sections (using existing _validate_section helper)
            sections = {}
            raw_sections_map = result.get('sections', {}) # Expecting dict {name: {details}} now
            
            if not isinstance(raw_sections_map, dict):
                logger.error("Invalid sections format in AI response (expected dict)")
                raw_sections_map = {}

            for section_name, section_data in raw_sections_map.items():
                if not isinstance(section_data, dict):
                    continue
                # Add the standardized name to the data before validation
                section_data['name'] = section_name 
                section = self._validate_section(section_data)
                if section:
                    sections[section.name] = section # Use validated name as key

            return {
                "paper_type": paper_type,
                "sections": sections,
                "confidence": result.get('confidence', 0.0),
                "success": True # Indicate success
            }

        except Exception as e:
            logger.error(f"Error in paper characterization: {e}", exc_info=True)
            return {
                "error": f"Paper characterization failed: {str(e)}",
                "paper_type": PaperType.UNKNOWN,
                "sections": {},
                "success": False
            }
    
    def _create_default_characterization(self) -> Dict[str, Any]:
        """
        Create a default characterization result when analysis fails
        
        Returns:
            dict: Default paper type and sections
        """
        return {
            "paper_type": PaperType.UNKNOWN,
            "sections": {
                "abstract": {"title": "Abstract", "summary": ""},
                "introduction": {"title": "Introduction", "summary": ""},
                "methods": {"title": "Methods", "summary": ""},
                "results": {"title": "Results", "summary": ""},
                "conclusion": {"title": "Conclusion", "summary": ""}
            }
        }
    
    def map_sections_to_extracted_structure(
        self,
        characterization_result: Dict[str, Any],
        extracted_sections: List[Dict[str, Any]]
    ) -> Dict[str, Section]:
        """Map AI-identified sections to extracted structure with validation."""
        try:
            mapped_sections = {}
            ai_sections = characterization_result.get('sections', {})

            for section_name, ai_section in ai_sections.items():
                # Find best matching extracted section
                best_match = None
                best_score = 0

                for extracted in extracted_sections:
                    if not isinstance(extracted, dict):
                        continue

                    # Calculate similarity score
                    score = self._calculate_section_similarity(
                        ai_section.title,
                        extracted.get('title', '')
                    )

                    if score > best_score and score > 0.7:  # Minimum similarity threshold
                        best_score = score
                        best_match = extracted

                if best_match:
                    # Update AI section with extracted information
                    mapped_section = self._validate_section({
                        **ai_section.dict(),
                        'start_location': best_match.get('start_location', {}),
                        'end_location': best_match.get('end_location', {}),
                        'text': best_match.get('text', '')
                    })
                    
                    if mapped_section:
                        mapped_sections[section_name] = mapped_section

            return mapped_sections

        except Exception as e:
            logger.error(f"Error mapping sections: {e}")
            return characterization_result.get('sections', {})

    def _calculate_section_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between section titles."""
        try:
            # Simple case-insensitive comparison
            t1 = title1.lower().strip()
            t2 = title2.lower().strip()
            
            if t1 == t2:
                return 1.0
            
            # TODO: Implement more sophisticated similarity calculation if needed
            # For now, return 0 if not exact match
            return 0.0
            
        except Exception as e:
            logger.error(f"Error calculating section similarity: {e}")
            return 0.0 