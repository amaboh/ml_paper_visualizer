import logging
from typing import Dict, Any, List, Optional
import json
import os
from app.utils.ai_processor import AIProcessor
from app.core.models import ComponentType, Component, PaperType

logger = logging.getLogger(__name__)

# Base prompt template for component extraction
COMPONENT_EXTRACTION_BASE_PROMPT = """
You are an expert in machine learning research. Extract key components from this {section_name} section of a {paper_type} paper.

Focus on identifying the following information with high precision:
{focus_areas}

For each component you identify, provide:
1. Name: A concise name for the component
2. Type: One of the following component types: {component_types}
3. Description: A brief description of what this component is and its role
4. Details: Any specific parameters, configurations, or notable characteristics
5. Is_novel: Boolean (true/false) indicating if this appears to be a novel contribution in the paper

Return the components as a JSON array with this structure:
[
  {{
    "name": "component name",
    "type": "COMPONENT_TYPE",
    "description": "Brief description",
    "details": {{ 
      "param1": "value1",
      "param2": "value2"
    }},
    "is_novel": true/false
  }},
  ...
]

Section Content:
"""

# Specialized prompts based on paper type and section
SPECIALIZED_PROMPTS = {
    PaperType.NEW_ARCHITECTURE: {
        "model_architecture": {
            "focus_areas": """
            - Model architecture details (overall structure, layers, connections)
            - Individual layers or components (transformer blocks, attention mechanisms, etc.)
            - Key hyperparameters of the architecture
            - Novel architectural contributions
            - Input and output specifications
            """,
            "component_types": "MODEL, LAYER, MODULE, HYPERPARAMETER, ALGORITHM"
        },
        "methods": {
            "focus_areas": """
            - Overall model architecture
            - Key algorithms or methods introduced
            - Implementation details
            - Design choices and their justifications
            """,
            "component_types": "MODEL, ALGORITHM, HYPERPARAMETER, MODULE, LAYER"
        },
        "data": {
            "focus_areas": """
            - Datasets used
            - Data preprocessing techniques
            - Data partitioning (training/validation/test)
            - Data augmentation methods
            """,
            "component_types": "DATASET, PREPROCESSING, DATA_PARTITION"
        },
        "experiments": {
            "focus_areas": """
            - Training procedures
            - Hyperparameters used for training
            - Optimization methods
            - Evaluation metrics
            - Comparison models or baselines
            """,
            "component_types": "TRAINING, EVALUATION, METRIC, HYPERPARAMETER, MODEL"
        },
        "results": {
            "focus_areas": """
            - Performance metrics and results
            - Comparison to baselines
            - Ablation studies
            - Key findings
            """,
            "component_types": "RESULTS, METRIC, EVALUATION"
        }
    },
    PaperType.APPLICATION: {
        "methods": {
            "focus_areas": """
            - Existing models or architectures being applied
            - Any modifications to the original architecture
            - Application-specific adaptations
            - Domain-specific considerations
            """,
            "component_types": "MODEL, ADAPTATION, ALGORITHM, MODULE"
        },
        "data": {
            "focus_areas": """
            - Domain-specific datasets
            - Data collection methods
            - Data characteristics and challenges
            - Preprocessing for the specific application
            """,
            "component_types": "DATASET, DATA_COLLECTION, PREPROCESSING"
        }
        # Add other sections as needed
    }
    # Add other paper types as needed
}

# Default focus areas if no specialized prompt exists
DEFAULT_FOCUS_AREAS = """
- Models or architectures
- Datasets and data processing
- Training procedures
- Evaluation methods and metrics
- Results and findings
"""

# All valid component types for the default prompt
ALL_COMPONENT_TYPES = ", ".join([t.value for t in ComponentType])

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
    
    async def extract_components_from_sections(
        self, 
        paper_id: str,
        paper_type: PaperType,
        sections: Dict[str, Dict[str, Any]],
        section_texts: Dict[str, str]
    ) -> List[Component]:
        """
        Extract components from paper sections based on paper type
        
        Args:
            paper_id: ID of the paper
            paper_type: Type of the paper
            sections: Dictionary of sections with metadata
            section_texts: Dictionary of section texts
            
        Returns:
            List[Component]: Extracted components
        """
        all_components = []
        
        # Iterate through sections with section text available
        for section_name, section_data in sections.items():
            if section_name not in section_texts:
                continue
                
            section_text = section_texts[section_name]
            
            # Skip sections that are too short
            if len(section_text) < 100:
                continue
            
            # Extract components from this section
            components = await self.extract_components_from_section(
                paper_id=paper_id,
                paper_type=paper_type,
                section_name=section_name,
                section_text=section_text
            )
            
            # Add source section information to each component
            for component in components:
                component.source_section = section_name
                component.paper_id = paper_id
            
            all_components.extend(components)
        
        return all_components
    
    async def extract_components_from_section(
        self,
        paper_id: str,
        paper_type: PaperType,
        section_name: str,
        section_text: str
    ) -> List[Component]:
        """
        Extract components from a specific section using specialized prompts
        
        Args:
            paper_id: ID of the paper
            paper_type: Type of the paper
            section_name: Name of the section
            section_text: Text content of the section
            
        Returns:
            List[Component]: Extracted components
        """
        # Create the appropriate prompt based on paper type and section
        prompt = self._create_extraction_prompt(paper_type, section_name)
        
        # Truncate section text if too long
        max_chars = 12000
        truncated_text = section_text[:max_chars] if len(section_text) > max_chars else section_text
        
        # Process with AI
        response = await self.ai_processor.process_with_prompt(
            prompt=prompt,
            content=truncated_text,
            output_format="json"
        )
        
        # Process the response into Component objects
        components = []
        
        if isinstance(response, list):
            for item in response:
                if not isinstance(item, dict):
                    continue
                    
                # Extract component type
                try:
                    component_type_str = item.get("type", "").upper()
                    component_type = ComponentType(component_type_str.lower())
                except (ValueError, AttributeError):
                    # If type is invalid, try to infer from context
                    component_type = self._infer_component_type(item, section_name)
                
                # Create component
                component = Component(
                    paper_id=paper_id,
                    type=component_type,
                    name=item.get("name", f"Unnamed {component_type.value}"),
                    description=item.get("description", ""),
                    details=item.get("details", {}),
                    is_novel=item.get("is_novel", False)
                )
                
                components.append(component)
                
        else:
            logger.warning(f"Invalid response format for section {section_name}")
        
        return components
    
    def _create_extraction_prompt(self, paper_type: PaperType, section_name: str) -> str:
        """
        Create specialized extraction prompt based on paper type and section
        
        Args:
            paper_type: Type of the paper
            section_name: Name of the section
            
        Returns:
            str: Specialized prompt
        """
        # Normalize section name for lookup
        normalized_section = self._normalize_section_name(section_name)
        
        # Get specialized prompt if available
        specialized = SPECIALIZED_PROMPTS.get(paper_type, {}).get(normalized_section)
        
        if specialized:
            focus_areas = specialized.get("focus_areas")
            component_types = specialized.get("component_types")
        else:
            focus_areas = DEFAULT_FOCUS_AREAS
            component_types = ALL_COMPONENT_TYPES
        
        # Format the base prompt with specialized details
        prompt = COMPONENT_EXTRACTION_BASE_PROMPT.format(
            section_name=section_name,
            paper_type=paper_type.value,
            focus_areas=focus_areas,
            component_types=component_types
        )
        
        return prompt
    
    def _normalize_section_name(self, section_name: str) -> str:
        """
        Normalize section name for prompt lookup
        
        Args:
            section_name: Section name from paper
            
        Returns:
            str: Normalized section name
        """
        section_name = section_name.lower()
        
        # Map common variations to standard names
        if any(term in section_name for term in ["method", "approach", "technique"]):
            return "methods"
        elif any(term in section_name for term in ["architecture", "model", "network"]):
            return "model_architecture"
        elif any(term in section_name for term in ["experiment", "evaluation", "test"]):
            return "experiments"
        elif any(term in section_name for term in ["data", "dataset", "corpus"]):
            return "data"
        elif any(term in section_name for term in ["result", "performance", "finding"]):
            return "results"
        
        return section_name
    
    def _infer_component_type(self, component_data: Dict[str, Any], section_name: str) -> ComponentType:
        """
        Infer component type from context when type is invalid
        
        Args:
            component_data: Component data
            section_name: Section name
            
        Returns:
            ComponentType: Inferred component type
        """
        # Check component name for clues
        name = component_data.get("name", "").lower()
        description = component_data.get("description", "").lower()
        
        # Check for dataset indicators
        if any(term in name or term in description for term in ["dataset", "corpus", "data"]):
            return ComponentType.DATASET
        
        # Check for model indicators
        if any(term in name or term in description for term in ["model", "network", "architecture"]):
            return ComponentType.MODEL
        
        # Check for layer indicators
        if any(term in name or term in description for term in ["layer", "block", "attention"]):
            return ComponentType.LAYER
        
        # Check for metric indicators
        if any(term in name or term in description for term in ["accuracy", "precision", "recall", "f1", "loss"]):
            return ComponentType.METRIC
        
        # Fallback based on section
        normalized_section = self._normalize_section_name(section_name)
        
        if normalized_section == "methods":
            return ComponentType.ALGORITHM
        elif normalized_section == "model_architecture":
            return ComponentType.MODULE
        elif normalized_section == "data":
            return ComponentType.PREPROCESSING
        elif normalized_section == "results":
            return ComponentType.RESULTS
        elif normalized_section == "experiments":
            return ComponentType.EVALUATION
        
        # Final fallback
        return ComponentType.MODEL 