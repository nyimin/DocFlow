"""
Metadata Extraction Module for SmolDocling-OCR

Extracts and standardizes document metadata from PDFs and images
to enable provenance tracking and RAG citation generation.
"""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import fitz  # PyMuPDF
from PIL import Image
from PIL.ExifTags import TAGS


def parse_pdf_date(date_str: str) -> str:
    """
    Parse PDF date format (D:YYYYMMDDHHmmSS) to ISO 8601.
    
    Args:
        date_str: PDF date string (e.g., "D:20240115120000")
    
    Returns:
        ISO 8601 formatted date string or empty string if parsing fails
    """
    if not date_str:
        return ""
    
    try:
        # Remove 'D:' prefix if present
        if date_str.startswith("D:"):
            date_str = date_str[2:]
        
        # Validate minimum length
        if len(date_str) < 4:
            return ""
        
        # Extract date components
        year = date_str[0:4]
        month = date_str[4:6] if len(date_str) >= 6 else "01"
        day = date_str[6:8] if len(date_str) >= 8 else "01"
        hour = date_str[8:10] if len(date_str) >= 10 else "00"
        minute = date_str[10:12] if len(date_str) >= 12 else "00"
        second = date_str[12:14] if len(date_str) >= 14 else "00"
        
        # Validate year is numeric
        int(year)
        
        # Format as ISO 8601
        return f"{year}-{month}-{day}T{hour}:{minute}:{second}"
    except (ValueError, IndexError) as e:
        print(f"Warning: Failed to parse PDF date '{date_str}': {e}")
        return ""


def generate_document_id(file_path: str) -> str:
    """
    Generate deterministic document ID from file hash.
    
    Args:
        file_path: Path to document file
    
    Returns:
        16-character hex string (first 16 chars of SHA256 hash)
    """
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        return file_hash[:16]
    except Exception as e:
        print(f"Warning: Failed to generate document ID: {e}")
        # Fallback to filename-based hash
        return hashlib.sha256(Path(file_path).name.encode()).hexdigest()[:16]


def extract_pdf_metadata(pdf_path: str) -> Dict[str, Any]:
    """
    Extract comprehensive metadata from PDF file.
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Dictionary containing:
        - source_file: Filename
        - pages: Number of pages
        - title, author, subject, creator, producer: PDF metadata fields
        - creation_date, modification_date: ISO 8601 formatted dates
        - file_size_bytes: File size
        - extraction_date: Current timestamp
        - document_id: Deterministic hash-based ID
    """
    try:
        doc = fitz.open(pdf_path)
        metadata = doc.metadata or {}
        page_count = len(doc)
        
        # Calculate text layer word count for validation ground truth
        text_layer_word_count = 0
        try:
            for page in doc:
                text = page.get_text()
                if text:
                    text_layer_word_count += len(text.split())
        except Exception as e:
            print(f"Warning: Failed to count words in PDF: {e}")
        
        doc.close()
        
        file_stats = Path(pdf_path).stat()
        
        return {
            "source_file": Path(pdf_path).name,
            "pages": page_count,
            "text_layer_word_count": text_layer_word_count,
            "title": metadata.get("title", "").strip(),
            "author": metadata.get("author", "").strip(),
            "subject": metadata.get("subject", "").strip(),
            "creator": metadata.get("creator", "").strip(),
            "producer": metadata.get("producer", "").strip(),
            "creation_date": parse_pdf_date(metadata.get("creationDate", "")),
            "modification_date": parse_pdf_date(metadata.get("modDate", "")),
            "file_size_bytes": file_stats.st_size,
            "extraction_date": datetime.now().isoformat(),
            "document_id": generate_document_id(pdf_path)
        }
    except Exception as e:
        print(f"Error extracting PDF metadata: {e}")
        # Return minimal metadata on error
        return {
            "source_file": Path(pdf_path).name,
            "pages": 0,
            "title": "",
            "author": "",
            "subject": "",
            "creator": "",
            "producer": "",
            "creation_date": "",
            "modification_date": "",
            "file_size_bytes": Path(pdf_path).stat().st_size if Path(pdf_path).exists() else 0,
            "extraction_date": datetime.now().isoformat(),
            "document_id": generate_document_id(pdf_path)
        }


def extract_image_metadata(image_path: str) -> Dict[str, Any]:
    """
    Extract metadata from image file including EXIF data.
    
    Args:
        image_path: Path to image file
    
    Returns:
        Dictionary containing:
        - source_file: Filename
        - width, height: Image dimensions
        - format: Image format (PNG, JPEG, etc.)
        - mode: Color mode (RGB, RGBA, etc.)
        - exif: EXIF data if available
        - file_size_bytes: File size
        - extraction_date: Current timestamp
        - document_id: Deterministic hash-based ID
    """
    try:
        img = Image.open(image_path)
        
        # Extract EXIF data
        exif_data = {}
        if hasattr(img, '_getexif') and img._getexif():
            exif = img._getexif()
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                exif_data[tag] = str(value)
        
        file_stats = Path(image_path).stat()
        
        metadata = {
            "source_file": Path(image_path).name,
            "width": img.width,
            "height": img.height,
            "format": img.format or "Unknown",
            "mode": img.mode,
            "exif": exif_data,
            "file_size_bytes": file_stats.st_size,
            "extraction_date": datetime.now().isoformat(),
            "document_id": generate_document_id(image_path)
        }
        
        img.close()
        return metadata
        
    except Exception as e:
        print(f"Error extracting image metadata: {e}")
        # Return minimal metadata on error
        return {
            "source_file": Path(image_path).name,
            "width": 0,
            "height": 0,
            "format": "Unknown",
            "mode": "Unknown",
            "exif": {},
            "file_size_bytes": Path(image_path).stat().st_size if Path(image_path).exists() else 0,
            "extraction_date": datetime.now().isoformat(),
            "document_id": generate_document_id(image_path)
        }


def format_yaml_frontmatter(metadata: Dict[str, Any], extraction_method: str = "", 
                            confidence_score: Optional[float] = None,
                            language: str = "en") -> str:
    """
    Format metadata as YAML frontmatter for Markdown documents.
    
    Args:
        metadata: Metadata dictionary from extract_pdf_metadata or extract_image_metadata
        extraction_method: Name of extraction engine used
        confidence_score: Optional quality/confidence score (0.0-1.0)
        language: Document language code
    
    Returns:
        YAML frontmatter string with --- delimiters
    """
    lines = ["---", "document:"]
    
    # Core document info
    lines.append(f'  source_file: "{metadata.get("source_file", "")}"')
    
    if "pages" in metadata:
        lines.append(f'  pages: {metadata["pages"]}')
    elif "width" in metadata:
        lines.append(f'  dimensions: "{metadata["width"]}x{metadata["height"]}"')
        lines.append(f'  format: "{metadata.get("format", "")}"')
    
    if extraction_method:
        lines.append(f'  extraction_method: "{extraction_method}"')
    
    lines.append(f'  extraction_date: "{metadata.get("extraction_date", "")}"')
    
    if confidence_score is not None:
        lines.append(f'  confidence_score: {confidence_score:.2f}')
    
    lines.append(f'  language: "{language}"')
    lines.append(f'  document_id: "{metadata.get("document_id", "")}"')
    
    # Optional metadata fields
    lines.append("")
    lines.append("metadata:")
    
    if metadata.get("title"):
        lines.append(f'  title: "{metadata["title"]}"')
    if metadata.get("author"):
        lines.append(f'  author: "{metadata["author"]}"')
    if metadata.get("subject"):
        lines.append(f'  subject: "{metadata["subject"]}"')
    if metadata.get("creator"):
        lines.append(f'  creator: "{metadata["creator"]}"')
    if metadata.get("creation_date"):
        lines.append(f'  creation_date: "{metadata["creation_date"]}"')
    
    lines.append("---")
    lines.append("")  # Empty line after frontmatter
    
    return "\n".join(lines)


def add_yaml_frontmatter(markdown_text: str, metadata: Dict[str, Any], 
                        extraction_method: str = "",
                        confidence_score: Optional[float] = None,
                        language: str = "en") -> str:
    """
    Prepend YAML frontmatter to Markdown text.
    
    Args:
        markdown_text: Original Markdown content
        metadata: Metadata dictionary
        extraction_method: Name of extraction engine
        confidence_score: Optional quality score
        language: Document language
    
    Returns:
        Markdown text with YAML frontmatter prepended
    """
    frontmatter = format_yaml_frontmatter(metadata, extraction_method, confidence_score, language)
    return frontmatter + markdown_text


# Example usage
if __name__ == "__main__":
    # Test PDF metadata extraction
    test_pdf = "test.pdf"
    if os.path.exists(test_pdf):
        pdf_meta = extract_pdf_metadata(test_pdf)
        print("PDF Metadata:")
        print(pdf_meta)
        print("\nYAML Frontmatter:")
        print(format_yaml_frontmatter(pdf_meta, "pymupdf4llm", 0.92))
    
    # Test image metadata extraction
    test_image = "test.png"
    if os.path.exists(test_image):
        img_meta = extract_image_metadata(test_image)
        print("\nImage Metadata:")
        print(img_meta)
        print("\nYAML Frontmatter:")
        print(format_yaml_frontmatter(img_meta, "RapidOCR", 0.85))
