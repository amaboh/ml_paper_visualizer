import os
import sys
import pytest
from unittest.mock import patch, MagicMock
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.paper_service import process_paper
from app.core.models import Paper, PaperStatus

# Path to sample papers
SAMPLE_PAPERS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tests', 'sample_papers'))
RESNET_PATH = os.path.join(SAMPLE_PAPERS_DIR, 'resnet.pdf')
TRANSFORMER_PATH = os.path.join(SAMPLE_PAPERS_DIR, 'transformer.pdf')

@pytest.mark.asyncio
@patch('app.services.paper_service.PaperParser')
@patch('app.services.paper_service.VisualizationGenerator')
async def test_process_paper_success(mock_viz_generator, mock_parser):
    # Setup mock parser
    mock_parser_instance = MagicMock()
    mock_parser.return_value = mock_parser_instance
    
    # Setup mock components and relationships
    mock_components = [MagicMock(), MagicMock()]
    mock_relationships = [MagicMock()]
    mock_parser_instance.parse_paper.return_value = (mock_components, mock_relationships)
    
    # Setup mock visualization generator
    mock_viz_instance = MagicMock()
    mock_viz_generator.return_value = mock_viz_instance
    mock_viz_instance.create_visualization.return_value = MagicMock()
    
    # Create test paper
    paper = Paper(id="test-paper-id", status=PaperStatus.PROCESSING)
    
    # Process the paper
    result = await process_paper(paper, RESNET_PATH)
    
    # Verify that the parser was called with the correct arguments
    mock_parser_instance.parse_paper.assert_called_once_with(RESNET_PATH, paper.id)
    
    # Verify that the visualization generator was called with the correct arguments
    mock_viz_instance.create_visualization.assert_called_once_with(
        paper_id=paper.id,
        components=mock_components,
        relationships=mock_relationships
    )
    
    # Check that the function returned success
    assert result is True

@pytest.mark.asyncio
@patch('app.services.paper_service.PaperParser')
async def test_process_paper_failure_no_components(mock_parser):
    # Setup mock parser that returns no components
    mock_parser_instance = MagicMock()
    mock_parser.return_value = mock_parser_instance
    mock_parser_instance.parse_paper.return_value = ([], [])
    
    # Create test paper
    paper = Paper(id="test-paper-id", status=PaperStatus.PROCESSING)
    
    # Process the paper
    result = await process_paper(paper, TRANSFORMER_PATH)
    
    # Verify that the parser was called with the correct arguments
    mock_parser_instance.parse_paper.assert_called_once_with(TRANSFORMER_PATH, paper.id)
    
    # Check that the function returned failure
    assert result is False

@pytest.mark.asyncio
@patch('app.services.paper_service.PaperParser')
async def test_process_paper_exception(mock_parser):
    # Setup mock parser that raises an exception
    mock_parser_instance = MagicMock()
    mock_parser.return_value = mock_parser_instance
    mock_parser_instance.parse_paper.side_effect = Exception("Test exception")
    
    # Create test paper
    paper = Paper(id="test-paper-id", status=PaperStatus.PROCESSING)
    
    # Process the paper
    result = await process_paper(paper, RESNET_PATH)
    
    # Verify that the parser was called with the correct arguments
    mock_parser_instance.parse_paper.assert_called_once_with(RESNET_PATH, paper.id)
    
    # Check that the function returned failure
    assert result is False
