import logging
from typing import Dict, Any, List, Optional
import json
from app.utils.ai_processor import AIProcessor
from app.core.models import Component, Relationship, PaperType

logger = logging.getLogger(__name__)

# Base prompt template for relationship extraction
RELATIONSHIP_EXTRACTION_PROMPT = """
You are an expert in machine learning research. Based on the paper content and the extracted components, 
identify the relationships between components.

Paper Type: {paper_type}

Extracted Components:
{components_list}

Focus on identifying the following types of relationships:
1. "flow" - Data or processing flow from one component to another (X is input to Y)
2. "uses" - One component uses or depends on another (X uses Y)
3. "contains" - Hierarchical relationship (X contains Y)
4. "evaluates" - Evaluation relationship (X evaluates Y)
5. "compares" - Comparison relationship (X is compared to Y)
6. "improves" - Improvement relationship (X improves upon Y)
7. "part_of" - Component is part of another (X is part of Y)

For each relationship, provide:
1. Source: The ID of the source component
2. Target: The ID of the target component
3. Type: The relationship type (from the list above)
4. Description: Brief description of the relationship
5. Confidence: A number between 0-1 indicating confidence in this relationship

Return the relationships as a JSON array with this structure:
[
  {{
    "source_id": "component_id_1",
    "target_id": "component_id_2",
    "type": "relationship_type",
    "description": "brief description",
    "confidence": 0.9
  }},
  ...
]

Paper Content:
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
        paper_id: str,
        paper_type: PaperType,
        components: List[Component],
        paper_text: str
    ) -> List[Relationship]:
        """
        Extract relationships between components
        
        Args:
            paper_id: ID of the paper
            paper_type: Type of the paper
            components: List of extracted components
            paper_text: Text content of the paper or relevant sections
            
        Returns:
            List[Relationship]: Extracted relationships
        """
        if not components or len(components) < 2:
            logger.warning("Not enough components to extract relationships")
            return self._generate_fallback_relationships(paper_id, components)
        
        # Create a simplified list of components for the prompt
        components_list = "\n".join([
            f"ID: {comp.id} | Type: {comp.type.value} | Name: {comp.name} | " +
            f"Description: {comp.description}" 
            for comp in components
        ])
        
        # Create the prompt
        prompt = RELATIONSHIP_EXTRACTION_PROMPT.format(
            paper_type=paper_type.value,
            components_list=components_list
        )
        
        # Truncate paper text if too long
        max_chars = 15000
        truncated_text = paper_text[:max_chars] if len(paper_text) > max_chars else paper_text
        
        # Process with AI
        response = await self.ai_processor.process_with_prompt(
            prompt=prompt,
            content=truncated_text,
            output_format="json"
        )
        
        # Process the response into Relationship objects
        relationships = []
        
        if isinstance(response, list):
            # Create a map of component IDs for validation
            component_ids = {comp.id for comp in components}
            
            for item in response:
                if not isinstance(item, dict):
                    continue
                
                source_id = item.get("source_id")
                target_id = item.get("target_id")
                
                # Validate source and target IDs
                if not source_id or not target_id:
                    continue
                    
                if source_id not in component_ids or target_id not in component_ids:
                    logger.warning(f"Invalid component ID in relationship: {source_id} -> {target_id}")
                    continue
                
                # Skip self-references
                if source_id == target_id:
                    continue
                
                # Extract relationship type
                rel_type = item.get("type", "flow").lower()
                
                # Create the relationship
                relationship = Relationship(
                    paper_id=paper_id,
                    source_id=source_id,
                    target_id=target_id,
                    type=rel_type,
                    description=item.get("description", f"Relationship from {source_id} to {target_id}")
                )
                
                relationships.append(relationship)
        
        # If no relationships were extracted, fall back to simple relationships
        if not relationships:
            logger.warning("No relationships extracted, falling back to simple relationships")
            relationships = self._generate_fallback_relationships(paper_id, components)
        
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