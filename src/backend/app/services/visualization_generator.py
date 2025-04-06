from app.core.models import Visualization, Component, Relationship, ComponentType
from app.utils.ai_processor import AIProcessor
from typing import List, Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)

class VisualizationGenerator:
    """
    Service for generating visualizations of ML workflows extracted from papers
    """
    
    def __init__(self):
        """
        Initialize the visualization generator
        """
        # We're using the AIProcessor singleton, no parameters needed
        self.ai_processor = AIProcessor()
    
    async def create_visualization(
        self,
        components: List[Component],
        relationships: List[Relationship]
    ) -> Dict[str, Any]:
        """
        Create a visualization of an ML workflow
        
        Args:
            components: List of workflow components
            relationships: List of relationships between components
            
        Returns:
            Dict[str, Any]: Visualization data
        """
        try:
            # Convert components to the format expected by the AI processor
            components_data = []
            for component in components:
                component_data = {
                    "id": component.id,  # Make sure id is included
                    "type": component.type,
                    "name": component.name,
                    "description": component.description,
                    "details": component.details,
                    "source_section": component.source_section,
                    "source_page": component.source_page
                }
                components_data.append(component_data)
            
            # Generate visualization using the AI processor
            visualization = await self.ai_processor.generate_visualization(components_data)
            
            return visualization
            
        except Exception as e:
            logger.error(f"Error generating visualization: {str(e)}")
            return {"error": str(e)}
    
    def generate_mermaid_diagram(
        self,
        components: List[Component],
        relationships: List[Relationship]
    ) -> Dict[str, Any]:
        """
        Generate a Mermaid.js diagram from components and relationships
        
        Args:
            components: List of workflow components
            relationships: List of relationships between components
            
        Returns:
            Dict[str, Any]: Mermaid diagram data
        """
        try:
            # Create a mapping of component types to node classes
            type_classes = {
                ComponentType.DATA_COLLECTION: "dataCollection",
                ComponentType.PREPROCESSING: "preprocessing",
                ComponentType.DATA_PARTITION: "dataPartition",
                ComponentType.MODEL: "model",
                ComponentType.TRAINING: "training",
                ComponentType.EVALUATION: "evaluation",
                ComponentType.RESULTS: "results"
            }
            
            # Generate node IDs
            component_ids = {}
            for i, component in enumerate(components):
                component_ids[component.id] = chr(65 + i)  # A, B, C, ...
            
            # Generate node definitions
            nodes = []
            for component in components:
                node_id = component_ids[component.id]
                node_name = component.name
                nodes.append(f"{node_id}[{node_name}]")
            
            # Generate diagram edges
            edges = []
            for relationship in relationships:
                if relationship.source_id in component_ids and relationship.target_id in component_ids:
                    source_id = component_ids[relationship.source_id]
                    target_id = component_ids[relationship.target_id]
                    
                    if relationship.type == "flow":
                        edges.append(f"{source_id} --> {target_id}")
                    elif relationship.type == "reference":
                        edges.append(f"{source_id} -.-> {target_id}")
            
            # Generate class definitions and assignments
            class_defs = [
                "classDef dataCollection fill:#10B981,stroke:#047857,color:white;",
                "classDef preprocessing fill:#6366F1,stroke:#4338CA,color:white;",
                "classDef dataPartition fill:#F59E0B,stroke:#B45309,color:white;",
                "classDef model fill:#EF4444,stroke:#B91C1C,color:white;",
                "classDef training fill:#8B5CF6,stroke:#6D28D9,color:white;",
                "classDef evaluation fill:#EC4899,stroke:#BE185D,color:white;",
                "classDef results fill:#0EA5E9,stroke:#0369A1,color:white;"
            ]
            
            class_assignments = []
            for component in components:
                if component.id in component_ids:
                    node_id = component_ids[component.id]
                    class_name = type_classes.get(component.type)
                    if class_name:
                        class_assignments.append(f"class {node_id} {class_name};")
            
            # Assemble the full diagram
            node_section = "\n    ".join(nodes)
            edge_section = "\n    ".join(edges)
            class_def_section = "\n    ".join(class_defs)
            class_assignment_section = "\n    ".join(class_assignments)
            
            diagram = f"""flowchart TD
    {node_section}
    {edge_section}
    
    {class_def_section}
    
    {class_assignment_section}
"""
            
            # Map component IDs to diagram nodes
            component_mapping = {}
            for component_id, node_id in component_ids.items():
                component_mapping[node_id] = component_id
            
            return {
                "diagram_type": "mermaid",
                "diagram_data": diagram,
                "component_mapping": component_mapping
            }
            
        except Exception as e:
            logger.error(f"Error generating Mermaid diagram: {str(e)}")
            return {"error": str(e)}
    
    def generate_d3_data(
        self, 
        components: List[Component], 
        relationships: List[Relationship]
    ) -> Dict[str, Any]:
        """
        Generate D3.js compatible data structure for visualization
        
        Args:
            components: List of ML workflow components
            relationships: List of relationships between components
            
        Returns:
            Dict[str, Any]: D3.js compatible data structure
        """
        try:
            # Create nodes
            nodes = []
            for component in components:
                nodes.append({
                    "id": component.id,
                    "name": component.name,
                    "type": component.type.value,
                    "description": component.description,
                    "details": component.details,
                    "source_section": component.source_section,
                    "source_page": component.source_page
                })
            
            # Create links
            links = []
            for relationship in relationships:
                links.append({
                    "source": relationship.source_id,
                    "target": relationship.target_id,
                    "type": relationship.type,
                    "description": relationship.description
                })
            
            return {
                "nodes": nodes,
                "links": links
            }
            
        except Exception as e:
            logger.error(f"Error generating D3 data: {str(e)}")
            return {"error": str(e)}
    
    def create_complete_visualization(
        self,
        paper_id: str,
        components: List[Component],
        relationships: List[Relationship],
        settings: Dict[str, Any] = None
    ) -> Visualization:
        """
        Create a complete visualization for a paper
        
        Args:
            paper_id: ID of the paper
            components: List of ML workflow components
            relationships: List of relationships between components
            settings: Visualization settings
            
        Returns:
            Visualization: The created visualization
        """
        if settings is None:
            settings = {
                "layout": "TD",
                "theme": "default",
                "detail_level": "standard"
            }
        
        # Generate Mermaid diagram
        layout = "TD" if settings.get("layout") == "vertical" else "LR"
        mermaid_diagram = self.generate_mermaid_diagram(components, relationships)
        
        # Generate D3 data
        d3_data = self.generate_d3_data(components, relationships)
        
        # Create component metadata for interactive features
        component_metadata = {}
        for i, component in enumerate(components):
            diagram_id = chr(65 + i)  # A, B, C, etc.
            component_metadata[diagram_id] = {
                "id": component.id,
                "type": component.type.value,
                "name": component.name,
                "description": component.description,
                "source_section": component.source_section,
                "source_page": component.source_page
            }
        
        # Create visualization object
        visualization = Visualization(
            paper_id=paper_id,
            diagram_data={
                "mermaid": mermaid_diagram["diagram_data"],
                "d3": d3_data
            },
            settings=settings
        )
        
        return visualization
