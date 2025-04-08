import logging
from typing import Dict, Any, List, Optional
import json
import os
from app.utils.ai_processor import AIProcessor
from app.core.models import ComponentType, Component, PaperType

logger = logging.getLogger(__name__)

# NEW Comprehensive Prompt for Hierarchical Component Extraction
COMPONENT_EXTRACTION_PROMPT = """
You are an expert system specialized in analyzing machine learning research papers. Your task is to thoroughly read the provided paper text and extract a detailed, structured representation of its key elements, focusing on the methodology and findings.

**Instructions:**

1.  **Identify Key Stages:** Analyze the paper to identify the main stages of the research pipeline. Use these standardized stage names: `Data`, `Architecture`, `Training`, `Evaluation`, `Results`. Provide a brief AI-generated summary for each stage identified.
2.  **Extract Components Hierarchically:** Within each stage, extract the relevant components. Represent the components in a nested structure using the `children` array where appropriate. For example, an `Encoder Stack` component should contain `Encoder Layer` components as children, which in turn contain `Multi-Head Attention` and `Feed-Forward Network` components.
3.  **Provide Component Details:** For each extracted component, provide the following information:
    *   `ai_component_id`: A unique temporary ID string for this component within this response (e.g., "temp_arch_1_1"). Used for relationship mapping later.
    *   `category`: A specific, descriptive category (e.g., `Dataset`, `Preprocessing`, `Model`, `Sub-Architecture`, `Layer`, `Mechanism`, `Optimizer`, `Metric`, `Result`, `Hardware`).
    *   `type`: The closest matching type from this list: {component_types_list}. Use `OTHER` if no suitable type exists.
    *   `name`: A concise, descriptive name for the component (e.g., `Transformer`, `Encoder Stack`, `Scaled Dot-Product Attention`, `Adam Optimizer`, `BLEU Score`).
    *   `description`: A brief explanation of the component's purpose and function based on the paper.
    *   `details`: A dictionary of key-value pairs containing specific parameters, configurations, formulas, or notable characteristics mentioned (e.g., `{{"N": 6, "d_model": 512}}`, `{{"formula": "QK^T / sqrt(dk)"}}`, `{{"beta1": 0.9}}`).
    *   `is_novel`: Boolean (true/false) indicating if the paper presents this component as a novel contribution.
    *   `children`: A list containing nested child component objects, following the same structure. Leave empty (`[]`) if no children.
4.  **Summarize Paper:** Provide a brief overall summary of the paper's title, main focus, and key contribution.
5.  **Output Format:** Return the entire analysis as a single JSON object matching the structure specified below.

**JSON Output Structure:**

```json
{{
  "paper_summary": {{
    "title": "Detected Paper Title",
    "focus": "AI summary of the paper's main focus",
    "contribution": "AI summary of the key contribution"
  }},
  "pipeline_stages": [
    {{
      "stage_name": "Data", 
      "summary": "AI summary of data processing...",
      "components": [
        {{
          "ai_component_id": "temp_id_1",
          "category": "Dataset",
          "type": "DATASET",
          "name": "Component Name",
          "description": "Description...",
          "details": {{ "key": "value" }},
          "is_novel": false,
          "children": []
        }},
        // ... more components in Data stage ...
      ]
    }},
    {{
      "stage_name": "Architecture",
      "summary": "AI summary of model architecture...",
      "components": [
         // ... potentially nested components ...
      ]
    }},
    // ... other stages (Training, Evaluation, Results) ...
  ]
}}
```

**Paper Text:**

{paper_text}
"""

# Remove or comment out old prompts and specialization logic for now
# COMPONENT_EXTRACTION_BASE_PROMPT = ... (Old prompt)
# SPECIALIZED_PROMPTS = ... (Old logic)
# DEFAULT_FOCUS_AREAS = ... (Old logic)

# Keep the list of all valid ComponentType enum values for the new prompt
ALL_COMPONENT_TYPES = ", ".join([t.value.upper() for t in ComponentType])

class ComponentExtractionService:
    """
    Service for extracting components from research papers based on paper type and section
    """
    
    def __init__(self, ai_api_key: Optional[str] = None):
        """
        Initialize the component extraction service
        
        Args:
            ai_api_key: OpenAI API key (optional, will use environment variable if not provided)
        """
        # Use the AIProcessor singleton
        self.ai_processor = AIProcessor(api_key=ai_api_key)
    
    async def extract_components_from_text(
        self, 
        paper_id: str,
        paper_type: PaperType, # paper_type might still be useful context for the AI
        paper_text: str
    ) -> List[Component]: # Return type will change later after parsing
        """
        Extracts hierarchical components using the new comprehensive prompt.
        NOTE: This currently returns a placeholder. Parsing logic needs implementation.
        """
        logger.info("Attempting hierarchical component extraction...")
        try:
            # Truncate text if needed (adjust length as necessary for your AI model)
            max_chars = 30000 # Increased limit for comprehensive analysis
            truncated_text = paper_text[:max_chars] if len(paper_text) > max_chars else paper_text
            
            # Format the new prompt
            prompt = COMPONENT_EXTRACTION_PROMPT.format(
                component_types_list=ALL_COMPONENT_TYPES, 
                paper_text=truncated_text
            )

            # Process with AI using the generic method, forcing JSON output
            response_str = await self.ai_processor.process_text(prompt, force_json=True)

            # Check 1: Was the response string empty?
            if not response_str: # Handles None or ""
                 logger.error("AI Processor returned an empty response for hierarchical extraction. Potential API issue or content filtering.")
                 logger.info("Attempting fallback extraction method due to empty AI response...")
                 return await self.extract_components_fallback(
                paper_id=paper_id,
                paper_type=paper_type,
                     combined_text=paper_text
                 )

            # Check 2: Did the AI processor return a formatted error string?
            if response_str.startswith('{"error":'):
                logger.error(f"AI Processor failed during hierarchical extraction: {response_str}")
                logger.info("Attempting fallback extraction method due to AI processor error...")
                return await self.extract_components_fallback(
                     paper_id=paper_id,
                     paper_type=paper_type,
                     combined_text=paper_text
                )

            # --- Proceed with Parsing Logic only if response is not empty and not an error --- 
            logger.info("Attempting to parse successful AI response for hierarchical extraction...")
            parsed_components = self._parse_hierarchical_response(response_str, paper_id)
            
            # If no components were extracted despite valid response, try fallback
            if not parsed_components or len(parsed_components) == 0:
                logger.warning("Hierarchical extraction returned no components despite valid response. Trying fallback...")
                return await self.extract_components_fallback(
                paper_id=paper_id,
                paper_type=paper_type,
                     combined_text=paper_text
                )
                
            return parsed_components 
            
        except Exception as e:
            logger.error(f"Error during hierarchical component extraction: {e}", exc_info=True)
            return [] # Return empty on error for now

    def _parse_hierarchical_response(self, response_str: str, paper_id: str) -> List[Component]:
        """Parses the new hierarchical JSON structure into flat Component list (temporary)."""
        components = []
        try:
            logger.debug(f"Raw AI response received for parsing: {repr(response_str)}") # Log raw response
            data = json.loads(response_str)
            if not isinstance(data, dict) or 'pipeline_stages' not in data:
                logger.error("Invalid root structure in AI response")
                return []

            # Recursive function to traverse the nested structure
            def traverse(component_data_list, parent_ai_id=None, stage=None):
                for comp_data in component_data_list:
                    if not isinstance(comp_data, dict):
                        continue
                    
                    # Basic validation
                    if not all(k in comp_data for k in ['ai_component_id', 'category', 'type', 'name', 'description', 'details', 'is_novel', 'children']):
                        logger.warning(f"Skipping component with missing keys: {comp_data.get('name')}")
                        continue

                    component_type_enum = self._validate_component_type(comp_data.get('type'))
                    
                    # Create the Component object (still flat for now)
                    # We'll need to add hierarchy support (e.g., parent_id) later
                    comp = Component(
                    paper_id=paper_id,
                        type=component_type_enum,
                        name=comp_data['name'],
                        description=comp_data['description'],
                        details=comp_data['details'],
                        source_section=stage, # Use stage name as section for now
                        is_novel=comp_data.get('is_novel', False),
                        # Add custom fields if needed, e.g.:
                        # category=comp_data['category'], 
                        # ai_id=comp_data['ai_component_id'] 
                    )
                    components.append(comp)
                    
                    # Recurse for children
                    if isinstance(comp_data.get('children'), list) and comp_data['children']:
                        traverse(comp_data['children'], comp_data['ai_component_id'], stage)

            # Iterate through stages and call traverse
            for stage_data in data.get('pipeline_stages', []):
                 if isinstance(stage_data, dict) and isinstance(stage_data.get('components'), list):
                      traverse(stage_data['components'], stage=stage_data.get('stage_name'))
            
            logger.info(f"Parsed {len(components)} components from hierarchical response.")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse hierarchical JSON response: {e}")
        except Exception as e:
            logger.error(f"Error processing hierarchical response: {e}", exc_info=True)
        
        return components
    
    def _validate_component_type(self, component_type) -> ComponentType:
        """Validate and convert component type to proper enum."""
        if isinstance(component_type, str):
            try:
                return ComponentType(component_type.upper())  # Convert to uppercase for case-insensitive matching
            except ValueError:
                logger.warning(f"Invalid component type {component_type}, falling back to OTHER")
                return ComponentType.OTHER
        elif isinstance(component_type, ComponentType):
            return component_type
        else:
            logger.warning(f"Invalid component type format {type(component_type)}, falling back to OTHER")
            return ComponentType.OTHER

    def _create_component(self, component_data: Dict[str, Any], paper_id: str, section_name: str) -> Component:
        """Create a component with validation and error handling."""
        try:
            # Validate required fields
            if not component_data.get('name'):
                raise ValueError("Component name is required")

            # Validate and convert component type
            component_type = self._validate_component_type(component_data.get('type', 'OTHER'))

            return Component(
                paper_id=paper_id,
                type=component_type,
                name=component_data.get('name'),
                description=component_data.get('description', ''),
                details=component_data.get('details', {}),
                source_section=section_name,
                is_novel=component_data.get('is_novel', False)
            )
        except Exception as e:
            logger.error(f"Error creating component: {e}")
            # Create a fallback component
            return Component(
                paper_id=paper_id,
                type=ComponentType.OTHER,
                name="Extraction Error Component",
                description=f"Component extraction failed: {str(e)}",
                details={"error": str(e), "original_data": component_data},
                source_section=section_name,
                is_novel=False
            )

    def _create_minimal_components(self, paper_id: str, paper_type: Optional[PaperType]) -> List[Component]:
        """Create minimal components when all extraction methods fail."""
        # Ensure paper_type is valid, default to UNKNOWN if None
        valid_paper_type = paper_type if isinstance(paper_type, PaperType) else PaperType.UNKNOWN
        paper_type_value = valid_paper_type.value
        
        return [
            Component(
                paper_id=paper_id,
                type=ComponentType.OTHER,
                name=f"Paper Content ({paper_type_value})",
                description="Automatic component extraction failed. Manual review recommended.",
                details={
                    "extraction_note": "Created as fallback when extraction failed",
                    "paper_type": paper_type_value
                },
                source_section="full_paper",
                is_novel=False
            )
        ] 

    async def extract_components_fallback(
        self,
        paper_id: str,
        paper_type: PaperType,
        combined_text: str
    ) -> List[Component]:
        """Fallback extraction method with enhanced error handling."""
        try:
            # Create a simplified prompt for fallback extraction
            fallback_prompt = """
            Extract the main components from this paper. Focus on:
            1. The main model or method
            2. Key datasets used
            3. Important metrics or results
            
            Return components in JSON format as before.
            """
            
            # Ensure combined_text is not excessively long for the prompt content
            max_fallback_length = 15000 # Adjust as needed
            truncated_fallback_text = combined_text[:max_fallback_length]

            response = await self.ai_processor.process_with_prompt(
                prompt=fallback_prompt,
                content=truncated_fallback_text, 
                output_format="json"
            )
        
            # Check if the response indicates an error from the processor itself
            if isinstance(response, dict) and "error" in response:
                logger.error(f"Fallback extraction AI processor error: {response['error']}")
                return self._create_minimal_components(paper_id, paper_type)

            # Process response assuming it should be a JSON list, but handle dict case
            components_data = []
            if isinstance(response, list):
                components_data = response
            elif isinstance(response, str): # Sometimes the response might be a string containing JSON
                try:
                    parsed_response = json.loads(response)
                    if isinstance(parsed_response, list):
                        components_data = parsed_response
                    elif isinstance(parsed_response, dict) and 'components' in parsed_response and isinstance(parsed_response['components'], list):
                        # Handle common case where list is nested under 'components' key
                        components_data = parsed_response['components']
                        logger.info("Extracted components list from nested dictionary key.")
                    else:
                        logger.error(f"Fallback extraction parsed non-list/non-dict JSON: {type(parsed_response)}")
                        return self._create_minimal_components(paper_id, paper_type)
                except json.JSONDecodeError:
                    logger.error("Failed to parse fallback extraction response string")
                    return self._create_minimal_components(paper_id, paper_type)
            elif isinstance(response, dict): # Directly handle dictionary response
                if 'components' in response and isinstance(response['components'], list):
                    components_data = response['components']
                    logger.info("Extracted components list from direct dictionary response.")
                else:
                    logger.error(f"Fallback extraction received unexpected dict structure: {response.keys()}")
                    return self._create_minimal_components(paper_id, paper_type)
            else: # Unexpected response type
                logger.error(f"Unexpected response type from fallback extraction: {type(response)}")
                return self._create_minimal_components(paper_id, paper_type)

            components = []
            for comp_data in components_data:
                if not isinstance(comp_data, dict):
                    continue
                component = self._create_component(comp_data, paper_id, "full_paper")
                components.append(component)
        
            return components if components else self._create_minimal_components(paper_id, paper_type)

        except Exception as e:
            logger.error(f"Fallback extraction failed: {e}", exc_info=True)
            return self._create_minimal_components(paper_id, paper_type) 