import os
import sys
import pytest
from fastapi.testclient import TestClient
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app

client = TestClient(app)

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
