import pytest
import os
from unittest.mock import patch, MagicMock
import json
import tempfile

from app.services.ai_extraction_service import AIExtractionService
from app.services.paper_characterization import PaperCharacterizationService
from app.services.component_extraction import ComponentExtractionService
from app.services.relationship_extraction import RelationshipExtractionService
from app.utils.pdf_extractor import PDFExtractor
from app.core.models import PaperType, Component, ComponentType, Section, LocationInfo

class TestAIExtractionPipeline:
    """Test the multi-stage AI extraction pipeline"""

    def setup_method(self):
        """Set up tests"""
        # Create a sample PDF file
        self.test_pdf_path = os.path.join(os.path.dirname(__file__), 'resources/test_paper.pdf')
        # If the file doesn't exist yet, create a dummy PDF file for testing
        os.makedirs(os.path.dirname(self.test_pdf_path), exist_ok=True)
        if not os.path.exists(self.test_pdf_path):
            with open(self.test_pdf_path, 'w') as f:
                f.write("Dummy PDF content for testing")

        # Sample paper ID
        self.paper_id = "test-paper-id"

    def teardown_method(self):
        """Clean up after tests"""
        # Remove the test PDF file if it was created during setup
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)

    @pytest.mark.asyncio
    @patch('app.utils.pdf_extractor.PDFExtractor.extract_all')
    @patch('app.services.paper_characterization.PaperCharacterizationService.characterize_paper')
    @patch('app.services.component_extraction.ComponentExtractionService.extract_components_from_sections')
    @patch('app.services.relationship_extraction.RelationshipExtractionService.extract_relationships')
    @patch('app.services.relationship_extraction.RelationshipExtractionService.analyze_relationships')
    async def test_process_paper_pipeline(self, mock_analyze, mock_rels, mock_comps, mock_char, mock_extract):
        """Test the complete paper processing pipeline"""
        # Mock the PDF extraction
        mock_extract.return_value = {
            "text": ["Sample paper text for testing"],
            "sections": [
                {"title": "Abstract", "start_location": {"page": 0, "position": 0}, 
                 "end_location": {"page": 0, "position": 100}}
            ],
            "structured_text": {"pages": []}
        }

        # Mock the paper characterization
        mock_char.return_value = {
            "paper_type": PaperType.NEW_ARCHITECTURE,
            "sections": {
                "abstract": {"title": "Abstract", "summary": "Test summary"},
                "methods": {"title": "Methods and Approach", "summary": "Test methods"}
            }
        }

        # Create a LocationInfo object for the Section
        start_location = LocationInfo(page=0, position=0)
        end_location = LocationInfo(page=0, position=100)

        # Mock map_sections_to_extracted_structure
        with patch.object(PaperCharacterizationService, 'map_sections_to_extracted_structure') as mock_map:
            mock_map.return_value = {
                "abstract": Section(
                    id="section-id-1",
                    name="abstract",
                    title="Abstract",
                    start_location=start_location,
                    end_location=end_location,
                    summary="Test summary"
                ),
                "methods": Section(
                    id="section-id-2",
                    name="methods",
                    title="Methods and Approach",
                    start_location=start_location,
                    end_location=end_location,
                    summary="Test methods"
                )
            }

            # Mock the section text extraction
            with patch.object(PDFExtractor, 'extract_section_text') as mock_section_text:
                mock_section_text.return_value = "Sample section text"
                
                # Mock component extraction
                mock_comps.return_value = [
                    Component(
                        id="comp-id-1",
                        paper_id=self.paper_id,
                        type=ComponentType.MODEL,
                        name="Test Model",
                        description="A test model",
                        is_novel=True
                    ),
                    Component(
                        id="comp-id-2",
                        paper_id=self.paper_id,
                        type=ComponentType.DATASET,
                        name="Test Dataset",
                        description="A test dataset"
                    )
                ]
                
                # Mock relationship extraction
                mock_rels.return_value = [
                    {
                        "id": "rel-id-1",
                        "paper_id": self.paper_id,
                        "source_id": "comp-id-2",
                        "target_id": "comp-id-1",
                        "type": "uses",
                        "description": "Model uses Dataset"
                    }
                ]
                
                # Mock relationship analysis
                mock_analyze.return_value = {
                    "relationship_types": {"uses": 1},
                    "central_components": [
                        {"id": "comp-id-1", "name": "Test Model", "type": "model", "connections": 1}
                    ],
                    "total_relationships": 1
                }
                
                # Test the full pipeline
                service = AIExtractionService()
                result = await service.process_paper(self.test_pdf_path, self.paper_id)
                
                # Verify the result
                assert result["success"] is True
                assert result["paper_type"] == PaperType.NEW_ARCHITECTURE
                assert len(result["components"]) == 2
                assert len(result["relationships"]) == 1
                assert "relationship_analysis" in result
                
                # Verify each stage was called
                mock_extract.assert_called_once()
                mock_char.assert_called_once()
                mock_comps.assert_called_once()
                mock_rels.assert_called_once()
                mock_analyze.assert_called_once()

    @pytest.mark.asyncio
    @patch('app.utils.ai_processor.AIProcessor.process_with_prompt')
    async def test_paper_characterization(self, mock_process):
        """Test paper characterization (Stage 1)"""
        # Mock the AI processor response
        mock_process.return_value = {
            "paper_type": "new_architecture",
            "sections": {
                "abstract": {"title": "Abstract", "summary": "Paper presents a new model"},
                "introduction": {"title": "Introduction", "summary": "Introduces the problem"},
                "methods": {"title": "Methods", "summary": "Describes the architecture"}
            }
        }
        
        service = PaperCharacterizationService()
        result = await service.characterize_paper("Sample paper text for testing")
        
        # Verify the result
        assert result["paper_type"] == PaperType.NEW_ARCHITECTURE
        assert len(result["sections"]) == 3
        assert "abstract" in result["sections"]
        assert "introduction" in result["sections"]
        assert "methods" in result["sections"]

    @pytest.mark.asyncio
    @patch('app.utils.ai_processor.AIProcessor.process_with_prompt')
    async def test_component_extraction(self, mock_process):
        """Test component extraction (Stage 2)"""
        # Mock the AI processor response
        mock_process.return_value = [
            {
                "name": "Test Model",
                "type": "model",
                "description": "A test model architecture",
                "details": {"layers": 12, "hidden_size": 768},
                "is_novel": True
            },
            {
                "name": "Test Dataset",
                "type": "dataset",
                "description": "Dataset used for evaluation",
                "details": {"size": "10K examples"},
                "is_novel": False
            }
        ]
        
        service = ComponentExtractionService()
        result = await service.extract_components_from_section(
            paper_id="test-id",
            paper_type=PaperType.NEW_ARCHITECTURE,
            section_name="methods",
            section_text="Sample section text"
        )
        
        # Verify the result
        assert len(result) == 2
        assert result[0].name == "Test Model"
        assert result[0].type == ComponentType.MODEL
        assert result[0].is_novel is True
        assert result[1].name == "Test Dataset"
        assert result[1].type == ComponentType.DATASET
        assert result[1].is_novel is False

    @pytest.mark.asyncio
    @patch('app.utils.ai_processor.AIProcessor.process_with_prompt')
    async def test_relationship_extraction(self, mock_process):
        """Test relationship extraction (Stage 3)"""
        # Create test components
        components = [
            Component(
                id="comp-id-1",
                paper_id="test-id",
                type=ComponentType.MODEL,
                name="Test Model",
                description="A test model"
            ),
            Component(
                id="comp-id-2",
                paper_id="test-id",
                type=ComponentType.DATASET,
                name="Test Dataset",
                description="A test dataset"
            )
        ]
        
        # Mock the AI processor response
        mock_process.return_value = [
            {
                "source_id": "comp-id-2",
                "target_id": "comp-id-1",
                "type": "uses",
                "description": "Model uses Dataset",
                "confidence": 0.9
            }
        ]
        
        service = RelationshipExtractionService()
        result = await service.extract_relationships(
            paper_id="test-id",
            paper_type=PaperType.NEW_ARCHITECTURE,
            components=components,
            paper_text="Sample paper text"
        )
        
        # Verify the result
        assert len(result) == 1
        assert result[0].source_id == "comp-id-2"
        assert result[0].target_id == "comp-id-1"
        assert result[0].type == "uses"
        
        # Test relationship analysis
        analysis = service.analyze_relationships(components, result)
        assert analysis["total_relationships"] == 1
        assert analysis["relationship_types"] == {"uses": 1}
        assert len(analysis["central_components"]) == 2 