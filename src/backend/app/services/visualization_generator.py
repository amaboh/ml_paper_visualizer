from app.core.models import Visualization, Component, Relationship, ComponentType, PaperType
from app.utils.ai_processor import AIProcessor
from typing import List, Dict, Any, Optional
import logging
import json
import re # Import regex module

logger = logging.getLogger(__name__)

# Prompt for AI-driven Mermaid Diagram Generation
MERMAID_GENERATION_PROMPT = """
You are an expert in analyzing machine learning research papers and generating detailed Mermaid flowchart diagrams to represent their workflow and structure.

**Task:**
Read the following paper text and create a comprehensive Mermaid `flowchart TD` diagram. The diagram should clearly illustrate the paper's key contributions, including:
1.  **Overall Architecture:** Use `subgraph` for major sections like Architecture, Training, Evaluation, Components.
2.  **Model Hierarchy:** Use nested `subgraph` blocks for model components (e.g., Encoder/Decoder Stacks, Layers, Sub-layers like Multi-Head Attention, FFN).
3.  **Data Flow:** Show the sequence of data processing and usage (e.g., Dataset -> Preprocessing -> Model Input).
4.  **Training Details:** Include important parameters, optimizers, learning rate schedules, hardware used.
5.  **Evaluation:** Show metrics used and key results reported.
6.  **Key Mechanisms:** Detail important algorithms or components like Attention mechanisms within their own subgraphs if appropriate.

**Example Output Structure (Illustrative - Adapt based on paper content):**

```mermaid
flowchart TD
    subgraph Paper["Paper Title (e.g., Attention Is All You Need)"]
        subgraph DataProcessing["Data Processing"]
            Dataset[WMT 2014 En-De] --> BPE[Byte-Pair Encoding]
        end
        subgraph Architecture["Transformer Architecture"]
            BPE --> InputEmb[Input Embeddings + Positional Encoding]
            InputEmb --> Encoder[Encoder Stack N=6]
            Encoder --> Decoder[Decoder Stack N=6]
            Decoder --> LinearLayer[Linear + Softmax]
            LinearLayer --> OutputProbs[Output Probabilities]
        end
        subgraph EncoderDetails[Encoder Layer Details]
             MHA[Multi-Head Self-Attention] --> AddNorm1[Add & Norm]
             AddNorm1 --> FFN[Feed-Forward Network]
             FFN --> AddNorm2[Add & Norm]
        end
        // ... other subgraphs for Decoder Details, Training, Evaluation etc. ...
    end
```

**Output Requirements:**
- Your output MUST be ONLY the raw Mermaid syntax string.
- Start the output directly with `flowchart TD`.
- Enclose the entire Mermaid syntax within a single markdown code block: ```mermaid ... ```.
- Do NOT include any other text, explanations, or introductions before or after the code block.

**Paper Text:**

{paper_text}
"""

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
            # Handle case with no components or only a minimal component
            if not components or (len(components) == 1 and components[0].id == "minimal_component"):
                # Return a simple diagram indicating minimal/no data
                minimal_name = components[0].name if components else "Paper Processing"
                minimal_diagram = f"""flowchart TD
    A[{minimal_name}] -.-> B(Extraction Unsuccessful or Minimal)
    classDef minimal fill:#f9f,stroke:#333,stroke-width:2px;
    class A,B minimal;
"""
                return {
                    "diagram_type": "mermaid",
                    "diagram_data": minimal_diagram,
                    "component_mapping": {"A": components[0].id if components else "minimal_component"}, # Minimal mapping
                    "is_minimal": True
                }

            # Create a mapping of component types to node classes
            type_classes = {
                ComponentType.DATA_COLLECTION: "dataCollection",
                ComponentType.PREPROCESSING: "preprocessing",
                ComponentType.DATA_PARTITION: "dataPartition",
                ComponentType.MODEL: "model",
                ComponentType.TRAINING: "training",
                ComponentType.EVALUATION: "evaluation",
                ComponentType.RESULTS: "results",
                ComponentType.OTHER: "other"  # Add a class for OTHER type
            }

            # Generate node IDs
            component_ids = {}
            for i, component in enumerate(components):
                component_ids[component.id] = chr(65 + i)  # A, B, C, ...

            # Generate node definitions
            nodes = []
            for component in components:
                node_id = component_ids.get(component.id)
                if node_id: # Ensure node_id exists
                    node_name = component.name.replace('"', '#quot;') # Escape quotes for Mermaid
                    nodes.append(f'{node_id}["{node_name}"]')

            # Generate diagram edges
            edges = []
            if relationships: # Only generate edges if relationships exist
                for relationship in relationships:
                    source_node_id = component_ids.get(relationship.source_id)
                    target_node_id = component_ids.get(relationship.target_id)
                    
                    if source_node_id and target_node_id:
                        if relationship.type == "flow":
                            edges.append(f"{source_node_id} --> {target_node_id}")
                        elif relationship.type == "reference":
                            edges.append(f"{source_node_id} -.-> {target_node_id}")
                        else:
                             edges.append(f"{source_node_id} -- {relationship.type} --> {target_node_id}") # Default link

            # Generate class definitions and assignments
            class_defs = [
                "classDef dataCollection fill:#10B981,stroke:#047857,color:white;",
                "classDef preprocessing fill:#6366F1,stroke:#4338CA,color:white;",
                "classDef dataPartition fill:#F59E0B,stroke:#B45309,color:white;",
                "classDef model fill:#EF4444,stroke:#B91C1C,color:white;",
                "classDef training fill:#8B5CF6,stroke:#6D28D9,color:white;",
                "classDef evaluation fill:#EC4899,stroke:#BE185D,color:white;",
                "classDef results fill:#0EA5E9,stroke:#0369A1,color:white;",
                "classDef other fill:#9CA3AF,stroke:#4B5563,color:white;" # Style for OTHER
            ]

            class_assignments = []
            for component in components:
                node_id = component_ids.get(component.id)
                if node_id:
                    class_name = type_classes.get(component.type, "other") # Default to 'other'
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
                "component_mapping": component_mapping,
                "is_minimal": False # It's not minimal if we reached here
            }

        except Exception as e:
            logger.error(f"Error generating Mermaid diagram: {str(e)}")
            # Return error or a minimal error diagram
            error_diagram = f"""flowchart TD
    A[Error Generating Diagram] --> B({str(e).replace('"', '')})
"""
            return {
                "diagram_type": "mermaid",
                "diagram_data": error_diagram,
                "component_mapping": {},
                "error": str(e)
            }
    
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
            
            d3_data = {
                "nodes": nodes,
                "links": links
            }
            logger.info(f"Generated D3 data: nodes={len(nodes)}, links={len(links)}")
            logger.debug(f"D3 Data structure: {json.dumps(d3_data, indent=2)}") # Log the actual data
            return d3_data
            
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

    async def generate_mermaid_via_ai(self, paper_text: str, paper_type: PaperType) -> str:
        """Generates Mermaid diagram syntax directly using an AI prompt."""
        logger.info("Attempting to generate Mermaid diagram via AI.")
        try:
            # Truncate text if needed (adjust as necessary)
            # Consider a larger limit as this is the primary input now
            max_chars = 25000 
            truncated_text = paper_text[:max_chars] if len(paper_text) > max_chars else paper_text

            prompt = MERMAID_GENERATION_PROMPT.format(paper_text=truncated_text)
            
            logger.debug(f"Sending Mermaid generation prompt (first 300 chars): {prompt[:300]}...")
            
            # Use process_text, expect text/markdown output
            response_str = await self.ai_processor.process_text(
                prompt=prompt,
                model="gpt-4-turbo", # Use a powerful model if possible
                max_tokens=3000,     # Allow ample tokens for complex diagrams
                temperature=0.1      # Low temp for more deterministic structure
            )

            if not response_str or response_str.startswith('{"error":'):
                logger.error(f"AI Processor failed or returned error during Mermaid generation: {response_str}")
                return self._generate_error_mermaid("AI processing failed")

            # Extract content from the markdown code block
            match = re.search(r"```(?:mermaid)?\s*([\s\S]*?)\s*```", response_str, re.MULTILINE)
            if match:
                mermaid_syntax = match.group(1).strip()
                logger.info(f"Successfully extracted Mermaid syntax from AI response (length: {len(mermaid_syntax)}).")
                # Basic validation: Check if it starts reasonably
                if not mermaid_syntax.strip().startswith("flowchart"):
                     logger.warning("Extracted content doesn't look like Mermaid flowchart syntax.")
                     return self._generate_error_mermaid("AI response did not contain valid Mermaid flowchart syntax")
                return mermaid_syntax
            else:
                logger.error("Could not find Mermaid markdown code block in AI response.")
                logger.debug(f"Full AI response for Mermaid gen: {response_str}")
                return self._generate_error_mermaid("AI response format incorrect (missing Mermaid block)")

        except Exception as e:
            logger.error(f"Error during AI Mermaid generation: {e}", exc_info=True)
            return self._generate_error_mermaid(f"Unexpected error: {e}")

    def _generate_error_mermaid(self, error_message: str) -> str:
        """Generates a simple Mermaid diagram indicating an error."""
        escaped_message = error_message.replace('"', '#quot;')
        return f"""flowchart TD
    A[Error Generating Visualization] --> B("{escaped_message}");
    classDef error fill:#f9f,stroke:#333,stroke-width:2px;
    class A,B error;
"""
