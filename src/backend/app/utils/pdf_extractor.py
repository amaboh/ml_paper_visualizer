import os
import logging
from typing import Dict, Any, List, Optional, Tuple
import fitz  # PyMuPDF
import tempfile
import re

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
                "figures": [],
                "structured_text": {}
            }
            
            # Open the PDF file
            doc = fitz.open(self.file_path)
            
            # Extract metadata
            result["metadata"] = self._extract_metadata(doc)
            
            # Extract text from each page
            all_text = []
            structured_pages = []
            
            for page_num, page in enumerate(doc):
                text = page.get_text()
                result["text"].append(text)
                all_text.append(text)
                
                # Extract structured text with blocks, paragraphs, and font information
                structured_page = self._extract_structured_page(page, page_num)
                structured_pages.append(structured_page)
            
            # Join all text for section detection
            full_text = "\n".join(all_text)
            result["structured_text"]["pages"] = structured_pages
            
            # Extract sections based on headings and structure
            result["sections"] = self._detect_sections(full_text, structured_pages)
            
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
    
    def _extract_structured_page(self, page: fitz.Page, page_num: int) -> Dict[str, Any]:
        """
        Extract structured text from a page with font information and hierarchy
        
        Args:
            page: PyMuPDF page object
            page_num: Page number
            
        Returns:
            Dict[str, Any]: Structured page content
        """
        structured_page = {
            "page_num": page_num,
            "blocks": []
        }
        
        # Extract text with blocks information
        blocks_dict = page.get_text("dict")
        
        # Process each block
        for block_num, block in enumerate(blocks_dict["blocks"]):
            if block["type"] == 0:  # Text block
                lines = []
                block_text = ""
                
                for line in block["lines"]:
                    spans = []
                    line_text = ""
                    
                    # Process spans in the line
                    for span in line["spans"]:
                        span_info = {
                            "text": span["text"],
                            "font": span.get("font", ""),
                            "size": span.get("size", 0),
                            "flags": span.get("flags", 0),
                            "is_bold": bool(span.get("flags", 0) & 2),  # Check if bold flag is set
                            "is_italic": bool(span.get("flags", 0) & 1),  # Check if italic flag is set
                            "color": span.get("color", 0)
                        }
                        spans.append(span_info)
                        line_text += span["text"]
                    
                    line_info = {
                        "text": line_text,
                        "spans": spans,
                        "bbox": line["bbox"]
                    }
                    lines.append(line_info)
                    block_text += line_text + "\n"
                
                # Determine block type based on first line
                block_type = "normal"
                if lines and len(lines) > 0:
                    # Check if this might be a heading based on style
                    first_line = lines[0]
                    if any(span["is_bold"] for span in first_line["spans"]):
                        if any(span["size"] > 11 for span in first_line["spans"]):
                            block_type = "heading"
                    
                    # Check if all text is capitalized in a short line
                    if len(first_line["text"]) < 100 and first_line["text"].upper() == first_line["text"] and len(first_line["text"]) > 10:
                        block_type = "heading"
                
                structured_page["blocks"].append({
                    "type": block_type,
                    "block_num": block_num,
                    "text": block_text.strip(),
                    "lines": lines,
                    "bbox": block["bbox"]
                })
                
            elif block["type"] == 1:  # Image block
                structured_page["blocks"].append({
                    "type": "image",
                    "block_num": block_num,
                    "bbox": block["bbox"]
                })
        
        return structured_page
    
    def _detect_sections(self, text: str, structured_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect sections in the text based on font size, formatting, and structure
        
        Args:
            text: Full text of the PDF
            structured_pages: Structured text with font information
            
        Returns:
            List[Dict[str, Any]]: List of detected sections
        """
        # Common section keywords help identify headings
        common_section_keywords = [
            "abstract", "introduction", "related work", "background",
            "methodology", "methods", "implementation", "architecture",
            "model", "approach", "experimental", "experiments", "results",
            "evaluation", "discussion", "conclusion", "references",
            "data collection", "dataset", "training", "testing", "ablation"
        ]
        
        sections = []
        position_tracker = 0
        current_section = None
        
        # Iterate through all structured pages
        for page_data in structured_pages:
            for block in page_data["blocks"]:
                if block["type"] == "heading":
                    block_text = block["text"].lower().strip()
                    
                    # Check if this block might be a section heading
                    is_section_heading = False
                    
                    # Check if contains common section keywords
                    if any(keyword in block_text for keyword in common_section_keywords):
                        is_section_heading = True
                    
                    # Check if starts with a number pattern like "1.", "1.1", "I.", "A."
                    if re.match(r'^([0-9]+\.)|([0-9]+\.[0-9]+\.?)|([IVX]+\.)|([A-Z]\.)', block_text):
                        is_section_heading = True
                    
                    if is_section_heading:
                        # Close previous section if it exists
                        if current_section:
                            current_section["end_location"] = {
                                "page": page_data["page_num"],
                                "position": position_tracker
                            }
                            sections.append(current_section)
                        
                        # Start a new section
                        current_section = {
                            "title": block["text"].strip(),
                            "start_location": {
                                "page": page_data["page_num"],
                                "position": position_tracker
                            },
                            "summary": "",  # This will be filled by AI
                            "blocks": []
                        }
                    
                # If we have a current section, add this block to it
                if current_section:
                    current_section["blocks"].append({
                        "page": page_data["page_num"],
                        "text": block["text"],
                        "type": block["type"]
                    })
                
                # Update position tracker
                position_tracker += len(block.get("text", "")) + 1
        
        # Close the last section
        if current_section:
            current_section["end_location"] = {
                "page": structured_pages[-1]["page_num"] if structured_pages else 0,
                "position": position_tracker
            }
            sections.append(current_section)
        
        # If no sections were found through headings, create a default section
        if not sections:
            sections.append({
                "title": "Main Content",
                "start_location": {"page": 0, "position": 0},
                "end_location": {"page": len(structured_pages) - 1 if structured_pages else 0, "position": position_tracker},
                "summary": "Main content of the paper",
                "blocks": []
            })
        
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
                    
                    # Try to find caption for this image
                    # Caption heuristic: text block close to the image with words like "Figure", "Fig.", "Table"
                    caption = self._find_caption_for_image(page, img_info)
                    
                    figures.append({
                        "page": page_num + 1,
                        "index": img_index,
                        "type": "image",
                        "format": base_image["ext"],
                        "size": len(image_data),
                        "caption": caption
                    })
                except Exception as e:
                    logger.error(f"Error extracting image: {str(e)}")
        
        return figures
        
    def _find_caption_for_image(self, page: fitz.Page, img_info: Any) -> str:
        """
        Attempt to find a caption for an image
        
        Args:
            page: PyMuPDF page object
            img_info: Image information
            
        Returns:
            str: Caption text or empty string
        """
        # This is a heuristic method that looks for text containing "Figure", "Fig.", etc.
        # near the image bounding box
        try:
            # Get image rectangle
            img_rect = page.get_image_bbox(img_info[0])
            
            if not img_rect:
                return ""
            
            # Get text blocks
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if block["type"] == 0:  # Text block
                    block_rect = fitz.Rect(block["bbox"])
                    
                    # Check if block is below or close to the image
                    if (abs(block_rect.y0 - img_rect.y1) < 50 or  # Below the image
                        abs(block_rect.y1 - img_rect.y0) < 50):   # Above the image
                        
                        block_text = "".join([span["text"] for line in block["lines"] for span in line["spans"]])
                        
                        # Check if this contains caption markers
                        if re.search(r'(Figure|Fig\.|Table|Algorithm)(\s+\d+)?', block_text, re.IGNORECASE):
                            return block_text
        except Exception as e:
            logger.error(f"Error finding caption: {str(e)}")
            
        return ""

    def extract_text_with_structure(self) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text from PDF while preserving structural elements.
        
        Returns:
            tuple: (full_text, structured_text)
        """
        extraction_result = self.extract_all()
        full_text = "\n".join(extraction_result["text"])
        structured_text = extraction_result["structured_text"]
        
        return full_text, structured_text
    
    def extract_section_text(self, structured_text: Dict[str, Any], start_location: Dict[str, Any], end_location: Dict[str, Any]) -> str:
        """
        Extract text for a specific section using location information.
        
        Args:
            structured_text: Structured text data
            start_location: Starting location of section
            end_location: Ending location of section
            
        Returns:
            str: Section text
        """
        section_text = []
        pages = structured_text.get("pages", [])
        
        start_page = start_location.get("page", 0)
        end_page = end_location.get("page", len(pages)-1)
        
        for page_data in pages:
            page_num = page_data.get("page_num", 0)
            
            # Skip pages before start or after end
            if page_num < start_page or page_num > end_page:
                continue
                
            # Extract text from blocks on this page
            for block in page_data.get("blocks", []):
                block_text = block.get("text", "")
                section_text.append(block_text)
        
        return "\n".join(section_text)
