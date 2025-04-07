import logging
from typing import Dict, Any, List, Optional
import json
from app.utils.ai_processor import AIProcessor
from app.core.models import PaperType, Section, LocationInfo

logger = logging.getLogger(__name__)

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
    
    async def characterize_paper(self, paper_text: str) -> Dict[str, Any]:
        """
        Analyze paper to determine its type and map key sections.
        
        Args:
            paper_text: The extracted text from the paper
            
        Returns:
            dict: Paper type and sections mapping
        """
        try:
            # Truncate text if needed to fit within model context limits
            max_chars = 15000
            truncated_text = paper_text[:max_chars] if len(paper_text) > max_chars else paper_text
            
            # Process with AI
            response = await self.ai_processor.process_with_prompt(
                prompt=PAPER_CHARACTERIZATION_PROMPT,
                content=truncated_text,
                output_format="json"
            )
            
            # Validate the result
            if not isinstance(response, dict):
                logger.error("Invalid response format from AI processor")
                return self._create_default_characterization()
            
            if "error" in response:
                logger.error(f"Error from AI processor: {response['error']}")
                return self._create_default_characterization()
            
            # Validate paper type
            paper_type = response.get("paper_type", "UNKNOWN")
            try:
                # Ensure it's a valid enum value
                paper_type = PaperType(paper_type.lower())
            except ValueError:
                logger.warning(f"Invalid paper type '{paper_type}', defaulting to UNKNOWN")
                paper_type = PaperType.UNKNOWN
            
            # Process sections
            processed_sections = {}
            sections_data = response.get("sections", {})
            
            for section_name, section_data in sections_data.items():
                if not isinstance(section_data, dict):
                    continue
                    
                processed_sections[section_name] = {
                    "title": section_data.get("title", section_name),
                    "summary": section_data.get("summary", "")
                }
            
            return {
                "paper_type": paper_type,
                "sections": processed_sections
            }
            
        except Exception as e:
            logger.error(f"Error characterizing paper: {str(e)}")
            return self._create_default_characterization()
    
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
        """
        Maps AI-identified sections to the extracted structure from the PDF
        
        Args:
            characterization_result: Result from characterize_paper
            extracted_sections: Sections extracted from PDF structure
            
        Returns:
            Dict[str, Section]: Mapped sections with start/end locations
        """
        ai_sections = characterization_result.get("sections", {})
        mapped_sections = {}
        
        # Try to map each AI-identified section to an extracted section
        for section_name, section_data in ai_sections.items():
            original_title = section_data.get("title", "")
            
            # Look for a matching extracted section
            matched_section = None
            for extracted in extracted_sections:
                extracted_title = extracted.get("title", "").lower()
                
                # Check for match (exact or fuzzy)
                if (original_title.lower() in extracted_title or 
                    section_name.lower() in extracted_title or
                    any(kw in extracted_title for kw in section_name.lower().split())):
                    matched_section = extracted
                    break
            
            # If we found a match, create a proper Section model
            if matched_section:
                start_location = LocationInfo(
                    page=matched_section.get("start_location", {}).get("page", 0),
                    position=matched_section.get("start_location", {}).get("position", 0)
                )
                
                end_location = LocationInfo(
                    page=matched_section.get("end_location", {}).get("page", 0),
                    position=matched_section.get("end_location", {}).get("position", 0)
                )
                
                mapped_sections[section_name] = Section(
                    name=section_name,
                    title=original_title,
                    start_location=start_location,
                    end_location=end_location,
                    summary=section_data.get("summary", "")
                )
        
        return mapped_sections 