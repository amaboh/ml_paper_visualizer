from app.core.models import Visualization, Component, Relationship, ComponentType, PaperType
from app.utils.ai_processor import AIProcessor
from typing import List, Dict, Any, Optional
import logging
import json
import re # Import regex module
import html

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

**Syntax Guidelines:**
- Use simple, alphanumeric node IDs (e.g., `A`, `B`, `Node1`).
- Enclose node text containing special characters or spaces in double quotes (e.g., `A["Node Text with Spaces"]`).
- Use standard Mermaid link syntax (`-->`, `-.->`, `-- text -->`).
- Ensure all `subgraph` blocks are properly closed with `end`.

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
            node_ids = set() # Keep track of valid node IDs
            for component in components:
                nodes.append({
                    "id": component.id,
                    "name": component.name,
                    "type": component.type.value if hasattr(component.type, 'value') else component.type, # Handle potential string type
                    "description": component.description,
                    "details": component.details,
                    "source_section": component.source_section,
                    "source_page": component.source_page,
                    # Add novelty and importance if they exist
                    "is_novel": getattr(component, 'is_novel', False),
                    "importance": getattr(component, 'importance', None),
                })
                node_ids.add(component.id)
            
            # Create links
            links = []
            if relationships:
                for relationship in relationships:
                    # Ensure both source and target nodes actually exist in the current node list
                    if relationship.source_id in node_ids and relationship.target_id in node_ids:
                        links.append({
                            "source": relationship.source_id,
                            "target": relationship.target_id,
                            "type": relationship.type,
                            "description": relationship.description
                        })
                    else:
                        logger.warning(f"Skipping relationship {relationship.id} because source or target node not found in provided components.")
            
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

    def generate_simple_svg(self, components: List[Component], relationships: List[Relationship]) -> str:
        """Generates a simple SVG representation of the workflow with descriptions and novelty highlights."""
        if not components:
            return '<svg width="300" height="100" xmlns="http://www.w3.org/2000/svg"><text x="10" y="50" fill="#cc0000">No components found to visualize.</text></svg>'

        # Basic SVG setup - Increased height and adjusted spacing
        width = 600
        box_width = 250 # Made wider to potentially accommodate more text
        box_height = 80  # Increased height for description
        v_spacing = 50 # Increased vertical space between boxes
        total_height = len(components) * (box_height + v_spacing) + v_spacing 

        svg_elements = []
        component_coords = {}

        # Define colors using string literals matching enum values as keys
        type_colors = {
            "data_collection": ("#e8f5e9", "#388e3c"),
            "preprocessing": ("#e1f5fe", "#0288d1"),
            "data_partition": ("#fff3e0", "#f57c00"),
            "model": ("#ffebee", "#d32f2f"),
            "training": ("#f3e5f5", "#7b1fa2"),
            "evaluation": ("#fce4ec", "#c2185b"),
            "results": ("#e0f7fa", "#0097a7"),
            "other": ("#f5f5f5", "#616161")
        }
        novel_border_color = "#FFC107" # Gold/Amber for novel components
        novel_stroke_width = "2.5"
        default_stroke_width = "1.5"

        # Create component groups (rect + text)
        for i, comp in enumerate(components):
            x = (width - box_width) / 2
            y = v_spacing + i * (box_height + v_spacing)
            
            is_novel = hasattr(comp, 'is_novel') and comp.is_novel
            bg_color, default_border = type_colors.get(comp.type, type_colors["other"])
            current_border_color = novel_border_color if is_novel else default_border
            current_stroke_width = novel_stroke_width if is_novel else default_stroke_width

            component_coords[comp.id] = {
                'top_center': (x + box_width / 2, y),
                'bottom_center': (x + box_width / 2, y + box_height)
            }

            # Create a JSON string of component data to embed in SVG
            # Include only essential fields to keep it compact
            component_data = {
                "id": comp.id,
                "name": comp.name,
                "type": comp.type.value if hasattr(comp.type, 'value') else comp.type,
                "description": comp.description,
                "source_section": comp.source_section if hasattr(comp, 'source_section') else None,
                "source_page": comp.source_page if hasattr(comp, 'source_page') else None,
                "is_novel": is_novel
            }
            
            # JSON-stringify and escape the data for embedding in SVG
            component_data_str = html.escape(json.dumps(component_data))
            
            # Wrap component elements in a group (<g>) with data attributes
            svg_elements.append(f'<g data-component-id="{comp.id}" data-component-data="{component_data_str}" style="cursor: pointer;">')
            
            # Rectangle with conditional novel styling
            svg_elements.append(
                f'  <rect x="{x}" y="{y}" width="{box_width}" height="{box_height}" \n'
                f'      rx="8" ry="8" fill="{bg_color}" stroke="{current_border_color}" stroke-width="{current_stroke_width}" />'
            )
            
            # Add Novel label if applicable
            if is_novel:
                svg_elements.append(
                    f'  <text x="{x + box_width - 10}" y="{y + 15}" font-family="Arial, sans-serif" font-size="10" text-anchor="end" fill="#b45309" font-weight="bold" pointer-events="none">Novel</text>'
                )
            
            # Text - Name (Title)
            text_name = (comp.name[:30] + '...') if len(comp.name) > 33 else comp.name
            svg_elements.append(
                f'  <text x="{x + box_width / 2}" y="{y + 25}" dy="0" \n'
                f'      font-family="Arial, sans-serif" font-size="14" font-weight="bold" text-anchor="middle" fill="#333" pointer-events="none">{text_name}</text>'
            )
            
            # Text - Description (Truncated)
            text_desc = comp.description or ""
            text_desc = (text_desc[:60] + '...') if len(text_desc) > 63 else text_desc
            svg_elements.append(
                f'  <text x="{x + box_width / 2}" y="{y + 50}" dy=".3em" \n'
                f'      font-family="Arial, sans-serif" font-size="11" text-anchor="middle" fill="#555" pointer-events="none">{text_desc}</text>'
            )
            
            svg_elements.append('</g>') # Close the group
            
        # Create relationship lines (using updated coords)
        for i in range(len(components) - 1):
            comp1_id = components[i].id
            comp2_id = components[i+1].id
            if comp1_id in component_coords and comp2_id in component_coords:
                x1, y1 = component_coords[comp1_id]['bottom_center']
                x2, y2 = component_coords[comp2_id]['top_center']
                svg_elements.append(
                    f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#aaa" stroke-width="2" marker-end="url(#arrowhead)" />'
                )
                
        # SVG Header and Defs (no changes needed here)
        svg_header = (
           f'<svg width="{width}" height="{total_height}" xmlns="http://www.w3.org/2000/svg" style="background-color: #f8f9fa;">\n' # Added background color
           f'  <defs>\n'
           f'    <marker id="arrowhead" viewBox="0 -5 10 10" refX="5" refY="0" markerWidth="6" markerHeight="6" orient="auto">\n'
           f'      <path d="M0,-5L10,0L0,5" fill="#aaa"/>\n' # Slightly darker arrow
           f'    </marker>\n'
           f'  </defs>\n'
        )

        svg_content = "\n".join(svg_elements)
        svg_footer = "</svg>"

        return svg_header + svg_content + svg_footer
