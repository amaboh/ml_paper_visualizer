import os
import sys
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.core.models import Paper, PaperStatus

client = TestClient(app)

@patch('app.routers.papers.process_paper_file')
def test_upload_paper_endpoint(mock_process_paper):
    # Create a test PDF file
    test_file_content = b'%PDF-1.5\nTest PDF content'
    test_filename = 'test_paper.pdf'
    
    # Setup the mock
    mock_process_paper.return_value = None
    
    # Make the request
    response = client.post(
        "/api/papers/upload",
        files={"file": (test_filename, test_file_content, "application/pdf")}
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "processing"
    assert data["message"] == "Paper upload received and processing started"
    
    # Verify the mock was called
    mock_process_paper.assert_called_once()

@patch('app.routers.papers.process_paper_url')
def test_upload_paper_url_endpoint(mock_process_paper_url):
    # Setup the mock
    mock_process_paper_url.return_value = None
    
    # Make the request
    response = client.post(
        "/api/papers/upload",
        data={"url": "https://arxiv.org/pdf/1512.03385.pdf"}
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] == "processing"
    assert data["message"] == "Paper URL received and processing started"
    
    # Verify the mock was called
    mock_process_paper_url.assert_called_once()

def test_upload_paper_missing_input():
    # Make the request without providing file or URL
    response = client.post("/api/papers/upload")
    
    # Check the response
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "Either file or URL must be provided" in response.json()["detail"]

@patch('app.routers.workflow.get_workflow')
def test_get_component_endpoint(mock_get_workflow):
    # Setup mock workflow response
    mock_workflow = MagicMock()
    mock_component = MagicMock()
    mock_component.id = "comp1"
    mock_workflow.components = [mock_component]
    mock_get_workflow.return_value = mock_workflow
    
    # Make the request
    response = client.get("/api/workflow/test-paper-id/components/comp1")
    
    # Check the response
    assert response.status_code == 200
    
    # Verify the mock was called
    mock_get_workflow.assert_called_once_with("test-paper-id")

@patch('app.routers.workflow.get_workflow')
def test_get_component_not_found(mock_get_workflow):
    # Setup mock workflow response with no matching component
    mock_workflow = MagicMock()
    mock_workflow.components = []
    mock_get_workflow.return_value = mock_workflow
    
    # Make the request
    response = client.get("/api/workflow/test-paper-id/components/nonexistent")
    
    # Check the response
    assert response.status_code == 404
    assert "detail" in response.json()
    assert "Component not found" in response.json()["detail"]
    
    # Verify the mock was called
    mock_get_workflow.assert_called_once_with("test-paper-id")

@patch('app.routers.visualization.get_visualization')
def test_customize_visualization_endpoint(mock_get_visualization):
    # Setup mock visualization response
    mock_visualization = {
        "paper_id": "test-paper-id",
        "diagram_type": "mermaid",
        "diagram_data": "flowchart TD\nA[Test]",
        "component_metadata": {},
        "settings": {"layout": "vertical", "theme": "default"}
    }
    mock_get_visualization.return_value = mock_visualization
    
    # Make the request
    response = client.post(
        "/api/visualization/test-paper-id/customize",
        json={"layout": "horizontal", "theme": "dark", "detail_level": "detailed", "component_filters": []}
    )
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert data["settings"]["layout"] == "horizontal"
    assert data["settings"]["theme"] == "dark"
    assert data["settings"]["detail_level"] == "detailed"
    
    # Verify the mock was called
    mock_get_visualization.assert_called_once_with("test-paper-id")

@patch('app.routers.visualization.get_visualization')
def test_export_visualization_endpoint(mock_get_visualization):
    # Setup mock visualization response
    mock_visualization = {
        "paper_id": "test-paper-id",
        "diagram_type": "mermaid",
        "diagram_data": "flowchart TD\nA[Test]",
        "component_metadata": {},
        "settings": {"layout": "vertical", "theme": "default"}
    }
    mock_get_visualization.return_value = mock_visualization
    
    # Make the request
    response = client.get("/api/visualization/test-paper-id/export?format=svg")
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    assert data["paper_id"] == "test-paper-id"
    assert data["format"] == "svg"
    assert "diagram_data" in data
    
    # Verify the mock was called
    mock_get_visualization.assert_called_once_with("test-paper-id")
