import pytest
from fastapi.testclient import TestClient
import json
import os

from app.main import app
from app.core.models import Paper, PaperStatus, PaperDatabase, Component, ComponentType
from app.core.models import PaperType, Section, LocationInfo, Relationship

client = TestClient(application=app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to ML Paper Visualizer API"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_api_papers_endpoint():
    # This is a placeholder test that will be expanded with actual paper upload testing
    # For now, we're just checking that the endpoint exists and returns the expected response
    response = client.get("/api/papers/sample-id")
    assert response.status_code == 501  # Not Implemented
    assert "message" in response.json()

def test_api_workflow_endpoint():
    # Test the workflow endpoint with a sample paper ID
    response = client.get("/api/workflow/sample-id")
    assert response.status_code == 200
    data = response.json()
    
    # Check that the response has the expected structure
    assert "paper_id" in data
    assert "components" in data
    assert "relationships" in data
    
    # Check that components have the expected fields
    assert len(data["components"]) > 0
    component = data["components"][0]
    assert "id" in component
    assert "type" in component
    assert "name" in component
    assert "description" in component
    
    # Check that relationships have the expected fields
    assert len(data["relationships"]) > 0
    relationship = data["relationships"][0]
    assert "source_id" in relationship
    assert "target_id" in relationship
    assert "type" in relationship

def test_api_visualization_endpoint():
    # Test the visualization endpoint with a sample paper ID
    response = client.get("/api/visualization/sample-id")
    assert response.status_code == 200
    data = response.json()
    
    # Check that the response has the expected structure
    assert "paper_id" in data
    assert "diagram_type" in data
    assert "diagram_data" in data
    assert "component_metadata" in data
    assert "settings" in data
    
    # Check that the diagram data is a non-empty string
    assert isinstance(data["diagram_data"], str)
    assert len(data["diagram_data"]) > 0
    
    # Check that component metadata has entries
    assert len(data["component_metadata"]) > 0

@pytest.mark.asyncio
async def test_get_paper_with_sections_and_type():
    """Test the get_paper endpoint with paper type and sections"""
    # Create a test paper with type and sections
    paper = Paper(
        id="test-paper-id", 
        title="Test Paper",
        paper_type=PaperType.NEW_ARCHITECTURE,
        sections={
            "abstract": Section(
                id="section-1",
                name="abstract",
                title="Abstract",
                start_location=LocationInfo(page=0, position=0),
                end_location=LocationInfo(page=0, position=100),
                summary="Test abstract"
            ),
            "methods": Section(
                id="section-2",
                name="methods",
                title="Methods",
                start_location=LocationInfo(page=1, position=0),
                end_location=LocationInfo(page=2, position=100),
                summary="Test methods"
            )
        }
    )
    
    # Store the paper in the database
    PaperDatabase.add_paper(paper)
    
    # Make a request to the API
    response = client.get(f"/api/papers/{paper.id}")
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == paper.id
    assert data["title"] == paper.title
    assert data["paper_type"] == PaperType.NEW_ARCHITECTURE
    assert len(data["sections"]) == 2
    assert "abstract" in data["sections"]
    assert "methods" in data["sections"]

@pytest.mark.asyncio
async def test_get_paper_sections():
    """Test the get_paper_sections endpoint"""
    # Create a test paper with sections
    paper = Paper(
        id="test-paper-id", 
        title="Test Paper",
        sections={
            "abstract": Section(
                id="section-1",
                name="abstract",
                title="Abstract",
                start_location=LocationInfo(page=0, position=0),
                end_location=LocationInfo(page=0, position=100),
                summary="Test abstract"
            )
        }
    )
    
    # Store the paper in the database
    PaperDatabase.add_paper(paper)
    
    # Make a request to the API
    response = client.get(f"/api/papers/{paper.id}/sections")
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "sections" in data
    assert len(data["sections"]) == 1
    assert "abstract" in data["sections"]

@pytest.mark.asyncio
async def test_get_relationship_analysis():
    """Test the get_workflow_relationship_analysis endpoint"""
    # Create a test paper with components, relationships, and analysis
    paper = Paper(
        id="test-paper-id", 
        title="Test Paper",
        components=[
            Component(
                id="comp-id-1",
                paper_id="test-paper-id",
                type=ComponentType.MODEL,
                name="Test Model",
                description="A test model"
            ),
            Component(
                id="comp-id-2",
                paper_id="test-paper-id",
                type=ComponentType.DATASET,
                name="Test Dataset",
                description="A test dataset"
            )
        ],
        relationships=[
            Relationship(
                id="rel-id-1",
                paper_id="test-paper-id",
                source_id="comp-id-2",
                target_id="comp-id-1",
                type="uses",
                description="Dataset is used by Model"
            )
        ],
        details={
            "relationship_analysis": {
                "relationship_types": {"uses": 1},
                "central_components": [
                    {"id": "comp-id-1", "name": "Test Model", "type": "model", "connections": 1}
                ],
                "total_relationships": 1
            }
        }
    )
    
    # Store the paper in the database
    PaperDatabase.add_paper(paper)
    
    # Make a request to the API
    response = client.get(f"/api/workflow/{paper.id}/relationships/analysis")
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "relationship_analysis" in data
    analysis = data["relationship_analysis"]
    assert "relationship_types" in analysis
    assert "central_components" in analysis
    assert "total_relationships" in analysis
    assert analysis["total_relationships"] == 1

@pytest.mark.asyncio
async def test_get_relationship_types():
    """Test the get_workflow_relationship_types endpoint"""
    # Make a request to the API
    response = client.get("/api/workflow/relationship-types")
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "relationship_types" in data
    relationship_types = data["relationship_types"]
    assert "flow" in relationship_types
    assert "uses" in relationship_types
    assert "contains" in relationship_types
    assert "evaluates" in relationship_types
