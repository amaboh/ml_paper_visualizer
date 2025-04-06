import logging
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
import os
import json
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class AIProcessor:
    """
    Utility class for AI-powered processing of paper content
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI processor
        
        Args:
            api_key: OpenAI API key (optional, will use environment variable if not provided)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No OpenAI API key provided. AI processing will not work.")
        else:
            # Initialize the async client
            self.client = AsyncOpenAI(api_key=self.api_key)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def analyze_paper_structure(self, text: str) -> Dict[str, Any]:
        """
        Analyze the structure of a paper to identify sections
        
        Args:
            text: The paper text content
            
        Returns:
            Dict[str, Any]: Dictionary containing identified sections
        """
        if not self.api_key:
            return {"error": "No API key provided"}
        
        try:
            # Truncate text if too long
            max_length = 15000  # Adjust based on model limits
            truncated_text = text[:max_length] if len(text) > max_length else text
            
            prompt = f"""
            You are an expert in analyzing scientific papers. Analyze the following paper text and identify the key sections.
            
            For each section, provide:
            1. The section title
            2. The starting position in the text (approximate)
            3. A brief summary of what the section contains
            
            Focus on identifying these key sections:
            - Abstract
            - Introduction
            - Related Work
            - Methods/Methodology
            - Data Collection
            - Preprocessing
            - Model Architecture
            - Training Process
            - Experiments
            - Results
            - Discussion
            - Conclusion
            
            Paper text:
            {truncated_text}
            
            Respond with a JSON structure containing the identified sections. Format:
            {{
              "sections": [
                {{
                  "title": "section_name",
                  "position": position_number,
                  "summary": "brief_summary"
                }},
                ...
              ]
            }}
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that analyzes scientific papers and extracts structured information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            # Extract and parse the response
            result_text = response.choices[0].message.content
            
            # Extract JSON from the response
            try:
                # Try to parse the entire response as JSON
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', result_text)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # If that also fails, log error and return empty structure
                    logger.error("Failed to parse JSON from AI response")
                    return {"sections": []}
            
            return result
            
        except Exception as e:
            logger.error(f"Error in AI processing: {str(e)}")
            return {"error": str(e)}
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def extract_ml_components(self, text: str, sections: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract ML workflow components from paper text
        
        Args:
            text: The paper text content
            sections: Dictionary of identified sections
            
        Returns:
            Dict[str, Any]: Dictionary containing extracted ML components
        """
        if not self.api_key:
            return {"error": "No API key provided"}
        
        try:
            # Construct a prompt with focused excerpts from relevant sections
            methodology_sections = [
                s for s in sections.get("sections", [])
                if any(kw in s.get("title", "").lower() for kw in 
                      ["method", "model", "architecture", "data", "preprocess", "training", "experiment"])
            ]
            
            # Extract relevant section texts
            excerpts = []
            for section in methodology_sections:
                position = section.get("position", 0)
                # Extract about 1000 characters from each section
                excerpt_start = max(0, position)
                excerpt_end = min(len(text), position + 1000)
                excerpt = text[excerpt_start:excerpt_end]
                excerpts.append(f"--- {section.get('title', 'Section')} ---\n{excerpt}")
            
            sections_text = "\n\n".join(excerpts)
            
            prompt = f"""
            You are an expert in machine learning. Extract the ML workflow components from the following paper sections:
            
            {sections_text}
            
            For each component of the ML workflow, identify:
            1. Component type (one of: data_collection, preprocessing, data_partition, model, training, evaluation, results)
            2. Component name (short, descriptive title)
            3. Component description (brief summary of what it does)
            4. Details (any parameters, dimensions, or specifics mentioned)
            5. Source section (which section this was found in)
            
            Respond with a JSON structure of identified components. Format:
            {{
              "components": [
                {{
                  "type": "component_type",
                  "name": "component_name",
                  "description": "component_description",
                  "details": {{
                    "param1": "value1",
                    "param2": "value2"
                  }},
                  "source_section": "section_name"
                }},
                ...
              ]
            }}
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that extracts structured ML workflow information from research papers."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            # Extract and parse the response
            result_text = response.choices[0].message.content
            
            # Extract JSON from the response
            try:
                # Try to parse the entire response as JSON
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from markdown code blocks
                import re
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', result_text)
                if json_match:
                    result = json.loads(json_match.group(1))
                else:
                    # If that also fails, log error and return empty structure
                    logger.error("Failed to parse JSON from AI response")
                    return {"components": []}
            
            # Add source page info (mock for now)
            for i, component in enumerate(result.get("components", [])):
                component["source_page"] = i + 1
            
            return result
            
        except Exception as e:
            logger.error(f"Error in AI processing: {str(e)}")
            return {"error": str(e)}
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_visualization(self, components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate visualization data from extracted components
        
        Args:
            components: List of ML workflow components
            
        Returns:
            Dict[str, Any]: Dictionary containing visualization data
        """
        if not self.api_key:
            return {"error": "No API key provided"}
        
        try:
            # Create a mapping of component types to node classes
            type_classes = {
                "data_collection": "dataCollection",
                "preprocessing": "preprocessing",
                "data_partition": "dataPartition",
                "model": "model",
                "training": "training",
                "evaluation": "evaluation",
                "results": "results"
            }
            
            # Generate node IDs (A, B, C, ...)
            component_ids = {}
            for i, component in enumerate(components):
                component_ids[component["id"]] = chr(65 + i)
            
            # Generate a Mermaid flowchart
            component_info = "\n".join([
                f"{component_ids[comp['id']]}[{comp['name']}]" 
                for comp in components
            ])
            
            # Generate relationships
            relationships = []
            for i in range(len(components) - 1):
                source = components[i]
                target = components[i + 1]
                relationships.append(
                    f"{component_ids[source['id']]} --> {component_ids[target['id']]}"
                )
            
            # Special relationship - data partition to evaluation
            data_partition = next((c for c in components if c["type"] == "data_partition"), None)
            evaluation = next((c for c in components if c["type"] == "evaluation"), None)
            
            if data_partition and evaluation:
                relationships.append(
                    f"{component_ids[data_partition['id']]} -.-> {component_ids[evaluation['id']]}"
                )
            
            relationship_info = "\n".join(relationships)
            
            # Generate class definitions for styling
            class_defs = "\n".join([
                f"class {component_ids[comp['id']]} {type_classes.get(comp['type'], 'default')};"
                for comp in components
            ])
            
            # Complete Mermaid diagram
            mermaid_diagram = f"""flowchart TD
{component_info}
{relationship_info}

classDef dataCollection fill:#10B981,stroke:#047857,color:white;
classDef preprocessing fill:#6366F1,stroke:#4338CA,color:white;
classDef dataPartition fill:#F59E0B,stroke:#B45309,color:white;
classDef model fill:#EF4444,stroke:#B91C1C,color:white;
classDef training fill:#8B5CF6,stroke:#6D28D9,color:white;
classDef evaluation fill:#EC4899,stroke:#BE185D,color:white;
classDef results fill:#0EA5E9,stroke:#0369A1,color:white;
classDef default fill:#9CA3AF,stroke:#4B5563,color:white;

{class_defs}
"""
            
            # Create component mapping for the frontend
            component_mapping = {}
            for comp in components:
                component_mapping[component_ids[comp["id"]]] = comp["id"]
            
            return {
                "diagram_type": "mermaid",
                "diagram_data": mermaid_diagram,
                "component_mapping": component_mapping
            }
            
        except Exception as e:
            logger.error(f"Error generating visualization: {str(e)}")
            return {"error": str(e)}
