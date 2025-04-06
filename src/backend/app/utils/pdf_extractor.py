import os
import logging
from typing import Dict, Any, List, Optional, Tuple
import fitz  # PyMuPDF
import tempfile

logger = logging.getLogger(__name__)

class PDFExtractor:
    """
    Utility class for extracting content from PDF files
    """
    
    def __init__(self, file_path: str):
        """
        Initialize the PDF extractor
        
        Args:
            file_path: Path to the PDF file
        """
        self.file_path = file_path
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
    
    def extract_all(self) -> Dict[str, Any]:
        """
        Extract all content from the PDF file
        
        Returns:
            Dict[str, Any]: Dictionary containing extracted text and metadata
        """
        try:
            result = {
                "text": [],
                "metadata": {},
                "sections": [],
                "figures": []
            }
            
            # Open the PDF file
            doc = fitz.open(self.file_path)
            
            # Extract metadata
            result["metadata"] = self._extract_metadata(doc)
            
            # Extract text from each page
            all_text = []
            for page_num, page in enumerate(doc):
                text = page.get_text()
                result["text"].append(text)
                all_text.append(text)
            
            # Join all text for section detection
            full_text = "\n".join(all_text)
            
            # Extract sections based on headings
            result["sections"] = self._detect_sections(full_text)
            
            # Extract figures
            result["figures"] = self._extract_figures(doc)
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting PDF content: {str(e)}")
            return {"error": str(e)}
        
    def _extract_metadata(self, doc: fitz.Document) -> Dict[str, Any]:
        """
        Extract metadata from the PDF document
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            Dict[str, Any]: Dictionary containing metadata
        """
        metadata = {}
        
        # Extract standard metadata
        for key in ["title", "author", "subject", "keywords", "creator", "producer", "creationDate", "modDate"]:
            metadata[key] = doc.metadata.get(key, "")
        
        # Extract additional metadata
        metadata["pageCount"] = len(doc)
        
        return metadata
    
    def _detect_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect sections in the text based on font size and formatting
        
        Args:
            text: Full text of the PDF
            
        Returns:
            List[Dict[str, Any]]: List of detected sections
        """
        # This is a simplified approach. In a real implementation,
        # we would use more sophisticated methods to detect sections,
        # such as analyzing font sizes, indentation, etc.
        
        # Split text into lines
        lines = text.split("\n")
        
        sections = []
        current_position = 0
        
        common_section_keywords = [
            "abstract", "introduction", "related work", "background",
            "methodology", "methods", "implementation", "architecture",
            "model", "experimental", "experiments", "results",
            "evaluation", "discussion", "conclusion", "references"
        ]
        
        # Look for potential section headings
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            # Skip short lines and lines that don't start with numbers or text
            if len(line_lower) < 3 or not (line_lower[0].isalpha() or line_lower[0].isdigit()):
                current_position += len(line) + 1  # +1 for the newline
                continue
            
            # Check if line might be a heading
            is_heading = False
            
            # Check if line contains common section keywords
            if any(keyword in line_lower for keyword in common_section_keywords):
                is_heading = True
            
            # Check if line starts with a number followed by dot (e.g., "1. Introduction")
            if line_lower.split(". ", 1)[0].isdigit():
                is_heading = True
            
            # Check if line is all uppercase or title case
            if line.isupper() or (line.strip() and line == line.title() and len(line) > 10):
                is_heading = True
            
            if is_heading:
                # Sections should have at least 3 characters
                if len(line.strip()) >= 3:
                    sections.append({
                        "title": line.strip(),
                        "position": current_position,
                        "summary": ""  # Summary would be generated with AI in a full implementation
                    })
            
            current_position += len(line) + 1  # +1 for the newline
        
        return sections
    
    def _extract_figures(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """
        Extract figures and diagrams from the PDF
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            List[Dict[str, Any]]: List of extracted figures
        """
        figures = []
        
        for page_num, page in enumerate(doc):
            # Extract images
            image_list = page.get_images(full=True)
            
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                
                try:
                    base_image = doc.extract_image(xref)
                    image_data = base_image["image"]
                    
                    figures.append({
                        "page": page_num + 1,
                        "index": img_index,
                        "type": "image",
                        "format": base_image["ext"],
                        "size": len(image_data)
                    })
                except Exception as e:
                    logger.error(f"Error extracting image: {str(e)}")
        
        return figures
