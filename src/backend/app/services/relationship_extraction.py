import logging
from typing import Dict, Any, List, Optional
import json
from app.utils.ai_processor import AIProcessor
from app.core.models import Component, Relationship, PaperType

logger = logging.getLogger(__name__)

# Updated Prompt for Strategy A (Component-Only)
RELATIONSHIP_EXTRACTION_PROMPT = """
You are an expert system specialized in analyzing machine learning research papers and their components.
Your task is to identify the direct, primary relationships between the provided components, representing the workflow or structure described implicitly or explicitly by the components themselves.

**Input Components:**

```json
{components_json}
```

**Instructions:**

1.  Analyze the `id`, `name`, `type`, and `description` of each component in the list above.
2.  Identify direct relationships between these components based on their information and typical ML workflow patterns (e.g., data usage, model architecture, training steps, evaluation methods).
3.  Focus on connections like `USES` (e.g., model uses dataset), `PRODUCES` (e.g., preprocessing produces features), `EVALUATES` (e.g., evaluation uses metric), `CONTAINS` (e.g., model contains layer), `PART_OF` (e.g., layer is part of encoder), `FLOWS_TO` (general sequential step).
4.  **Output Format:** Return your findings ONLY as a valid JSON list of relationship objects. Each object in the list MUST have the following keys:
    *   `source_component_id`: string (The `id` of the source component from the input list)
    *   `target_component_id`: string (The `id` of the target component from the input list)
    *   `relationship_type`: string (A descriptive type like `USES`, `PRODUCES`, `EVALUATES`, `CONTAINS`, `PART_OF`, `FLOWS_TO`)
    *   `description`: string (A brief explanation of why this relationship exists based on the component data)
5.  **Constraints:**
    *   Only include relationships where both `source_component_id` and `target_component_id` are present in the provided Input Components list.
    *   Do NOT include relationships to components not in the list.
    *   Do NOT include self-relationships (source and target are the same).
    *   If no direct relationships can be confidently identified, return an empty JSON list: `[]`.
    *   Ensure the entire output is a single, valid JSON list.

**JSON Output:**
"""

class RelationshipExtractionService:
    """
    Service for extracting relationships between components in research papers
    """
    
    def __init__(self, ai_api_key: Optional[str] = None):
        """
        Initialize the relationship extraction service
        
        Args:
            ai_api_key: OpenAI API key (optional, will use environment variable if not provided)
        """
        # Use the AIProcessor singleton
        self.ai_processor = AIProcessor(api_key=ai_api_key)
    
    async def extract_relationships(
        self,
        paper_id: str, # Keep for Relationship model
        paper_type: PaperType, # Keep for context if needed by AI
        components: List[Component],
        paper_text: str # Keep for potential future use (Strategy B/C), but ignore for now
    ) -> List[Relationship]:
        """
        Extract relationships between components using Strategy A (Component-Only Prompt).
        """
        if not components or len(components) < 2:
            logger.warning(f"[{paper_id}] Not enough components ({len(components)}) to extract relationships. Skipping AI call.")
            # Consider removing fallback generation here if AI is primary method
            # return self._generate_fallback_relationships(paper_id, components) 
            return [] # Return empty if not enough components
        
        # Prepare components data for the prompt (JSON serializable dict)
        components_for_prompt = []
        component_ids = set() # Keep track of valid IDs
        for comp in components:
            components_for_prompt.append({
                "id": comp.id,
                "name": comp.name,
                "type": comp.type.value if hasattr(comp.type, 'value') else str(comp.type),
                "description": comp.description
                # Add other relevant fields? details? source_section?
            })
            component_ids.add(comp.id)
        
        # Convert component data to a JSON string for the prompt
        try:
            components_json = json.dumps(components_for_prompt, indent=2)
        except TypeError as e:
            logger.error(f"[{paper_id}] Failed to serialize components to JSON for prompt: {e}")
            return [] # Cannot proceed without component data

        # Create the prompt using the new template
        prompt = RELATIONSHIP_EXTRACTION_PROMPT.format(
            components_json=components_json
            # paper_type=paper_type.value # Removed paper_type for now to simplify
        )
        
        logger.info(f"[{paper_id}] Sending relationship extraction prompt (Strategy A) to AI.")
        logger.debug(f"[{paper_id}] Relationship Prompt (first 500 chars): {prompt[:500]}...")
        
        # Process with AI, ensuring JSON output is forced
        response_str = await self.ai_processor.process_text(
            prompt=prompt,
            force_json=True 
        )
        
        relationships = []
        if not response_str or response_str.startswith('{"error":'):
            logger.error(f"[{paper_id}] AI Processor failed during relationship extraction or returned error: {response_str}")
            # Fallback? For now, return empty
            return []

        # Parse the JSON response
        try:
            parsed_response = json.loads(response_str)
            
            relationships_list = []
            # Check if the response is an object containing the 'relationships' key
            if isinstance(parsed_response, dict) and 'relationships' in parsed_response:
                if isinstance(parsed_response['relationships'], list):
                    relationships_list = parsed_response['relationships']
                    logger.info(f"[{paper_id}] Extracted relationship list from 'relationships' key in AI response object.")
                else:
                    logger.error(f"[{paper_id}] 'relationships' key found in AI response, but its value is not a list. Value: {parsed_response['relationships']}")
                    return []
            # Check if the response is directly a list (as originally prompted)
            elif isinstance(parsed_response, list):
                relationships_list = parsed_response
                logger.info(f"[{paper_id}] AI response for relationships was already a JSON list.")
            # Handle unexpected format
            else:
                logger.error(f"[{paper_id}] AI response for relationships was not a JSON list or expected object. Response: {response_str[:500]}...")
                return []

            # Process the extracted relationship list
            for item in relationships_list:
                if not isinstance(item, dict):
                    logger.warning(f"[{paper_id}] Skipping invalid item in relationship list: {item}")
                    continue
                
                source_id = item.get("source_component_id")
                target_id = item.get("target_component_id")
                rel_type = item.get("relationship_type", "RELATED_TO") # Default type
                description = item.get("description", "")
                
                # Validate IDs and relationship structure
                if not source_id or not target_id or not rel_type:
                    logger.warning(f"[{paper_id}] Skipping relationship item with missing fields: {item}")
                    continue
                    
                # Validate that IDs exist in the original components list
                if source_id not in component_ids or target_id not in component_ids:
                    logger.warning(f"[{paper_id}] Skipping relationship with invalid component ID(s): {source_id} -> {target_id}")
                    continue
                
                # Skip self-references
                if source_id == target_id:
                    logger.warning(f"[{paper_id}] Skipping self-relationship for component ID: {source_id}")
                    continue
                
                # Create the relationship object
                relationship = Relationship(
                    paper_id=paper_id,
                    source_id=source_id,
                    target_id=target_id,
                    type=rel_type.upper(), # Standardize type casing
                    description=description
                )
                relationships.append(relationship)
                
            logger.info(f"[{paper_id}] Successfully extracted {len(relationships)} relationships from AI response.")

        except json.JSONDecodeError as e:
            logger.error(f"[{paper_id}] Failed to decode AI JSON response for relationships: {e}. Response: {response_str[:500]}...")
            return [] # Return empty on JSON parsing error
        except Exception as e:
            logger.error(f"[{paper_id}] Error processing AI relationship response: {e}", exc_info=True)
            return []
        
        # Optional: If AI returns no relationships, maybe still generate fallbacks?
        # if not relationships:
        #     logger.warning(f"[{paper_id}] AI found no relationships, generating fallbacks.")
        #     return self._generate_fallback_relationships(paper_id, components)
        
        return relationships
    
    def _generate_fallback_relationships(self, paper_id: str, components: List[Component]) -> List[Relationship]:
        """
        Generate simple flow-based relationships between components as a fallback
        
        Args:
            paper_id: ID of the paper
            components: List of components
            
        Returns:
            List[Relationship]: Generated relationships
        """
        from app.core.models import ComponentType
        
        relationships = []
        
        # Skip if not enough components
        if not components or len(components) < 2:
            return relationships
        
        # Sort components by type to establish a logical flow
        type_order = {
            ComponentType.DATA_COLLECTION: 1,
            ComponentType.DATASET: 2,
            ComponentType.PREPROCESSING: 3,
            ComponentType.DATA_PARTITION: 4,
            ComponentType.MODEL: 5,
            ComponentType.LAYER: 6,
            ComponentType.MODULE: 7,
            ComponentType.TRAINING: 8,
            ComponentType.EVALUATION: 9,
            ComponentType.METRIC: 10,
            ComponentType.RESULTS: 11
        }
        
        # Default order for types not explicitly listed
        default_order = 100
        
        # Sort components by type order
        sorted_components = sorted(
            components, 
            key=lambda c: type_order.get(c.type, default_order)
        )
        
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
        
        # Add some special relationships based on component types
        
        # Find components by type
        datasets = [c for c in components if c.type in [ComponentType.DATASET, ComponentType.DATA_COLLECTION]]
        data_partitions = [c for c in components if c.type == ComponentType.DATA_PARTITION]
        models = [c for c in components if c.type == ComponentType.MODEL]
        evaluations = [c for c in components if c.type == ComponentType.EVALUATION]
        metrics = [c for c in components if c.type == ComponentType.METRIC]
        
        # Create dataset -> model relationships
        for dataset in datasets:
            for model in models:
                if dataset.id != model.id:  # Avoid self-references
                    relationships.append(Relationship(
                        paper_id=paper_id,
                        source_id=dataset.id,
                        target_id=model.id,
                        type="uses",
                        description=f"{model.name} uses {dataset.name}"
                    ))
        
        # Create data partition -> evaluation relationships
        for partition in data_partitions:
            for evaluation in evaluations:
                if partition.id != evaluation.id:  # Avoid self-references
                    relationships.append(Relationship(
                        paper_id=paper_id,
                        source_id=partition.id,
                        target_id=evaluation.id,
                        type="uses",
                        description=f"{evaluation.name} uses test data from {partition.name}"
                    ))
        
        # Create evaluation -> metric relationships
        for evaluation in evaluations:
            for metric in metrics:
                if evaluation.id != metric.id:  # Avoid self-references
                    relationships.append(Relationship(
                        paper_id=paper_id,
                        source_id=evaluation.id,
                        target_id=metric.id,
                        type="uses",
                        description=f"{evaluation.name} uses {metric.name}"
                    ))
        
        return relationships
    
    def analyze_relationships(self, components: List[Component], relationships: List[Relationship]) -> Dict[str, Any]:
        """
        Analyze extracted relationships to provide insights
        
        Args:
            components: List of components
            relationships: List of relationships
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        # Count relationships by type
        rel_types = {}
        for rel in relationships:
            rel_type = rel.type
            rel_types[rel_type] = rel_types.get(rel_type, 0) + 1
        
        # Find central components (highest connectivity)
        component_connections = {}
        for rel in relationships:
            component_connections[rel.source_id] = component_connections.get(rel.source_id, 0) + 1
            component_connections[rel.target_id] = component_connections.get(rel.target_id, 0) + 1
        
        # Sort components by connectivity
        sorted_components = sorted(
            component_connections.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Get top 3 most connected components
        central_components = []
        for comp_id, conn_count in sorted_components[:3]:
            comp = next((c for c in components if c.id == comp_id), None)
            if comp:
                central_components.append({
                    "id": comp.id,
                    "name": comp.name,
                    "type": comp.type.value,
                    "connections": conn_count
                })
        
        return {
            "relationship_types": rel_types,
            "central_components": central_components,
            "total_relationships": len(relationships)
        } 