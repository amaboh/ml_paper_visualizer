import os
import sys
import pytest
from unittest.mock import patch, MagicMock
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.paper_parser import PaperParser
from app.core.models import Component, Relationship, ComponentType

# Path to sample papers
SAMPLE_PAPERS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tests', 'sample_papers'))
RESNET_PATH = os.path.join(SAMPLE_PAPERS_DIR, 'resnet.pdf')
TRANSFORMER_PATH = os.path.join(SAMPLE_PAPERS_DIR, 'transformer.pdf')

@pytest.mark.asyncio
@patch('app.services.paper_parser.AIProcessor')
async def test_paper_parser_with_resnet(mock_ai_processor):
    # Setup mock AI processor
    mock_instance = MagicMock()
    mock_ai_processor.return_value = mock_instance
    
    # Mock the analyze_paper_structure method
    mock_instance.analyze_paper_structure.return_value = {
        "sections": [
            {"title": "Abstract", "position": 0, "summary": "Overview of ResNet"},
            {"title": "Introduction", "position": 500, "summary": "Background on deep networks"},
            {"title": "Related Work", "position": 1500, "summary": "Previous CNN architectures"},
            {"title": "Deep Residual Learning", "position": 3000, "summary": "Residual learning framework"},
            {"title": "Experiments", "position": 5000, "summary": "ImageNet and CIFAR-10 experiments"}
        ]
    }
    
    # Mock the extract_ml_components method
    mock_instance.extract_ml_components.return_value = {
        "components": [
            {
                "type": "data_collection",
                "name": "ImageNet Dataset",
                "description": "1.28 million training images and 50k validation images",
                "details": {"classes": 1000, "source": "ILSVRC 2012"},
                "source_section": "Experiments",
                "source_page": 5
            },
            {
                "type": "preprocessing",
                "name": "Image Preprocessing",
                "description": "Image resizing and normalization",
                "details": {"crop_size": "224x224", "mean_subtraction": True},
                "source_section": "Experiments",
                "source_page": 5
            },
            {
                "type": "model",
                "name": "ResNet Architecture",
                "description": "Deep residual network with skip connections",
                "details": {"depth": [18, 34, 50, 101, 152], "block_type": "bottleneck"},
                "source_section": "Deep Residual Learning",
                "source_page": 3
            },
            {
                "type": "training",
                "name": "ResNet Training",
                "description": "SGD with momentum and weight decay",
                "details": {"lr": 0.1, "momentum": 0.9, "weight_decay": 0.0001},
                "source_section": "Experiments",
                "source_page": 6
            },
            {
                "type": "evaluation",
                "name": "Model Evaluation",
                "description": "Top-1 and Top-5 error rates on ImageNet validation set",
                "details": {"metrics": ["top-1 error", "top-5 error"]},
                "source_section": "Experiments",
                "source_page": 7
            }
        ]
    }
    
    # Create parser and parse the ResNet paper
    parser = PaperParser()
    components, relationships = await parser.parse_paper(RESNET_PATH, "test-paper-id")
    
    # Verify that the AI processor methods were called
    mock_instance.analyze_paper_structure.assert_called_once()
    mock_instance.extract_ml_components.assert_called_once()
    
    # Check that components were created correctly
    assert len(components) == 5
    assert components[0].type == ComponentType.DATA_COLLECTION
    assert components[0].name == "ImageNet Dataset"
    assert components[2].type == ComponentType.MODEL
    assert components[2].name == "ResNet Architecture"
    
    # Check that relationships were created
    assert len(relationships) > 0
    
    # Verify the flow relationships
    flow_relationships = [r for r in relationships if r.type == "flow"]
    assert len(flow_relationships) == 4  # Should be n-1 where n is number of components

@pytest.mark.asyncio
@patch('app.services.paper_parser.AIProcessor')
async def test_paper_parser_with_transformer(mock_ai_processor):
    # Setup mock AI processor
    mock_instance = MagicMock()
    mock_ai_processor.return_value = mock_instance
    
    # Mock the analyze_paper_structure method
    mock_instance.analyze_paper_structure.return_value = {
        "sections": [
            {"title": "Abstract", "position": 0, "summary": "Overview of Transformer model"},
            {"title": "Introduction", "position": 500, "summary": "Background on sequence models"},
            {"title": "Model Architecture", "position": 2000, "summary": "Transformer architecture details"},
            {"title": "Training", "position": 4000, "summary": "Training procedure"},
            {"title": "Results", "position": 5000, "summary": "Experimental results"}
        ]
    }
    
    # Mock the extract_ml_components method
    mock_instance.extract_ml_components.return_value = {
        "components": [
            {
                "type": "data_collection",
                "name": "WMT 2014 English-German Dataset",
                "description": "4.5 million sentence pairs for machine translation",
                "details": {"languages": ["English", "German"]},
                "source_section": "Training",
                "source_page": 4
            },
            {
                "type": "preprocessing",
                "name": "Tokenization",
                "description": "Byte-pair encoding with 37K tokens",
                "details": {"vocab_size": 37000, "method": "BPE"},
                "source_section": "Training",
                "source_page": 4
            },
            {
                "type": "model",
                "name": "Transformer Architecture",
                "description": "Encoder-decoder with self-attention",
                "details": {"layers": 6, "model_dim": 512, "heads": 8},
                "source_section": "Model Architecture",
                "source_page": 2
            },
            {
                "type": "training",
                "name": "Transformer Training",
                "description": "Adam optimizer with custom learning rate",
                "details": {"lr": "custom schedule", "dropout": 0.1},
                "source_section": "Training",
                "source_page": 4
            },
            {
                "type": "evaluation",
                "name": "BLEU Score Evaluation",
                "description": "Evaluated on WMT 2014 English-German and English-French",
                "details": {"metrics": ["BLEU"]},
                "source_section": "Results",
                "source_page": 5
            }
        ]
    }
    
    # Create parser and parse the Transformer paper
    parser = PaperParser()
    components, relationships = await parser.parse_paper(TRANSFORMER_PATH, "test-paper-id")
    
    # Verify that the AI processor methods were called
    mock_instance.analyze_paper_structure.assert_called_once()
    mock_instance.extract_ml_components.assert_called_once()
    
    # Check that components were created correctly
    assert len(components) == 5
    assert components[0].type == ComponentType.DATA_COLLECTION
    assert components[0].name == "WMT 2014 English-German Dataset"
    assert components[2].type == ComponentType.MODEL
    assert components[2].name == "Transformer Architecture"
    
    # Check that relationships were created
    assert len(relationships) > 0
    
    # Verify the flow relationships
    flow_relationships = [r for r in relationships if r.type == "flow"]
    assert len(flow_relationships) == 4  # Should be n-1 where n is number of components
