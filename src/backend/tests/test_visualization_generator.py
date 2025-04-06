import os
import sys
import pytest
from unittest.mock import MagicMock
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.visualization_generator import VisualizationGenerator
from app.core.models import Component, Relationship, ComponentType

def test_mermaid_diagram_generation():
    # Create test components
    components = [
        Component(
            id="comp1",
            paper_id="test-paper",
            type=ComponentType.DATA_COLLECTION,
            name="MNIST Dataset",
            description="Handwritten digit dataset"
        ),
        Component(
            id="comp2",
            paper_id="test-paper",
            type=ComponentType.PREPROCESSING,
            name="Normalization",
            description="Normalize pixel values"
        ),
        Component(
            id="comp3",
            paper_id="test-paper",
            type=ComponentType.MODEL,
            name="CNN Architecture",
            description="Convolutional neural network"
        ),
        Component(
            id="comp4",
            paper_id="test-paper",
            type=ComponentType.TRAINING,
            name="Model Training",
            description="Training process"
        )
    ]
    
    # Create test relationships
    relationships = [
        Relationship(
            id="rel1",
            paper_id="test-paper",
            source_id="comp1",
            target_id="comp2",
            type="flow",
            description="Data flows to preprocessing"
        ),
        Relationship(
            id="rel2",
            paper_id="test-paper",
            source_id="comp2",
            target_id="comp3",
            type="flow",
            description="Preprocessed data to model"
        ),
        Relationship(
            id="rel3",
            paper_id="test-paper",
            source_id="comp3",
            target_id="comp4",
            type="flow",
            description="Model to training"
        )
    ]
    
    # Create visualization generator
    generator = VisualizationGenerator()
    
    # Generate Mermaid diagram
    mermaid_code = generator.generate_mermaid_diagram(components, relationships)
    
    # Check that the diagram contains expected elements
    assert "flowchart TD" in mermaid_code
    assert "A[MNIST Dataset]" in mermaid_code
    assert "B[Normalization]" in mermaid_code
    assert "C[CNN Architecture]" in mermaid_code
    assert "D[Model Training]" in mermaid_code
    
    # Check that relationships are included
    assert "A -->" in mermaid_code
    assert "B -->" in mermaid_code
    assert "C -->" in mermaid_code
    
    # Check that styling classes are included
    assert "classDef dataCollection" in mermaid_code
    assert "classDef preprocessing" in mermaid_code
    assert "classDef model" in mermaid_code
    assert "classDef training" in mermaid_code
    
    # Check that classes are applied to nodes
    assert "class A dataCollection" in mermaid_code
    assert "class B preprocessing" in mermaid_code
    assert "class C model" in mermaid_code
    assert "class D training" in mermaid_code

def test_d3_data_generation():
    # Create test components
    components = [
        Component(
            id="comp1",
            paper_id="test-paper",
            type=ComponentType.DATA_COLLECTION,
            name="MNIST Dataset",
            description="Handwritten digit dataset"
        ),
        Component(
            id="comp2",
            paper_id="test-paper",
            type=ComponentType.MODEL,
            name="CNN Architecture",
            description="Convolutional neural network"
        )
    ]
    
    # Create test relationships
    relationships = [
        Relationship(
            id="rel1",
            paper_id="test-paper",
            source_id="comp1",
            target_id="comp2",
            type="flow",
            description="Data flows to model"
        )
    ]
    
    # Create visualization generator
    generator = VisualizationGenerator()
    
    # Generate D3 data
    d3_data = generator.generate_d3_data(components, relationships)
    
    # Check that the data has the expected structure
    assert "nodes" in d3_data
    assert "links" in d3_data
    
    # Check nodes
    assert len(d3_data["nodes"]) == 2
    assert d3_data["nodes"][0]["id"] == "comp1"
    assert d3_data["nodes"][0]["name"] == "MNIST Dataset"
    assert d3_data["nodes"][0]["type"] == "data_collection"
    assert d3_data["nodes"][1]["id"] == "comp2"
    assert d3_data["nodes"][1]["name"] == "CNN Architecture"
    assert d3_data["nodes"][1]["type"] == "model"
    
    # Check links
    assert len(d3_data["links"]) == 1
    assert d3_data["links"][0]["source"] == "comp1"
    assert d3_data["links"][0]["target"] == "comp2"
    assert d3_data["links"][0]["type"] == "flow"
    assert d3_data["links"][0]["description"] == "Data flows to model"

def test_create_visualization():
    # Create test components
    components = [
        Component(
            id="comp1",
            paper_id="test-paper",
            type=ComponentType.DATA_COLLECTION,
            name="MNIST Dataset",
            description="Handwritten digit dataset"
        ),
        Component(
            id="comp2",
            paper_id="test-paper",
            type=ComponentType.MODEL,
            name="CNN Architecture",
            description="Convolutional neural network"
        )
    ]
    
    # Create test relationships
    relationships = [
        Relationship(
            id="rel1",
            paper_id="test-paper",
            source_id="comp1",
            target_id="comp2",
            type="flow",
            description="Data flows to model"
        )
    ]
    
    # Create visualization generator
    generator = VisualizationGenerator()
    
    # Create visualization
    visualization = generator.create_visualization("test-paper", components, relationships)
    
    # Check that the visualization has the expected structure
    assert visualization.paper_id == "test-paper"
    assert "mermaid" in visualization.diagram_data
    assert "d3" in visualization.diagram_data
    assert visualization.settings is not None
