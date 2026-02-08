"""
Unit tests for metadata_extractor module
"""

import os
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
import fitz  # PyMuPDF
from PIL import Image

# Import the module to test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from metadata_extractor import (
    parse_pdf_date,
    generate_document_id,
    extract_pdf_metadata,
    extract_image_metadata,
    format_yaml_frontmatter,
    add_yaml_frontmatter
)


class TestPDFDateParsing(unittest.TestCase):
    """Test PDF date parsing functionality."""
    
    def test_full_date_string(self):
        """Test parsing complete PDF date string."""
        result = parse_pdf_date("D:20240115120000")
        self.assertEqual(result, "2024-01-15T12:00:00")
    
    def test_partial_date_string(self):
        """Test parsing partial PDF date string."""
        result = parse_pdf_date("D:20240115")
        self.assertEqual(result, "2024-01-15T00:00:00")
    
    def test_no_prefix(self):
        """Test parsing date without D: prefix."""
        result = parse_pdf_date("20240115120000")
        self.assertEqual(result, "2024-01-15T12:00:00")
    
    def test_empty_string(self):
        """Test parsing empty string."""
        result = parse_pdf_date("")
        self.assertEqual(result, "")
    
    def test_invalid_date(self):
        """Test parsing invalid date string."""
        result = parse_pdf_date("invalid")
        self.assertEqual(result, "")


class TestDocumentID(unittest.TestCase):
    """Test document ID generation."""
    
    def test_deterministic_hash(self):
        """Test that same file produces same ID."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            id1 = generate_document_id(temp_path)
            id2 = generate_document_id(temp_path)
            self.assertEqual(id1, id2)
            self.assertEqual(len(id1), 16)
        finally:
            os.unlink(temp_path)
    
    def test_different_files_different_ids(self):
        """Test that different files produce different IDs."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f1:
            f1.write("content 1")
            temp_path1 = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f2:
            f2.write("content 2")
            temp_path2 = f2.name
        
        try:
            id1 = generate_document_id(temp_path1)
            id2 = generate_document_id(temp_path2)
            self.assertNotEqual(id1, id2)
        finally:
            os.unlink(temp_path1)
            os.unlink(temp_path2)


class TestPDFMetadataExtraction(unittest.TestCase):
    """Test PDF metadata extraction."""
    
    def setUp(self):
        """Create a test PDF file."""
        self.temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        self.temp_pdf.close()
        
        # Create a simple PDF with metadata
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((100, 100), "Test content")
        
        doc.set_metadata({
            "title": "Test Title",
            "author": "Test Author",
            "subject": "Test Subject",
            "creator": "Test Creator"
        })
        
        doc.save(self.temp_pdf.name)
        doc.close()
    
    def tearDown(self):
        """Clean up test PDF."""
        if os.path.exists(self.temp_pdf.name):
            os.unlink(self.temp_pdf.name)
    
    def test_extract_basic_metadata(self):
        """Test extraction of basic PDF metadata."""
        metadata = extract_pdf_metadata(self.temp_pdf.name)
        
        self.assertIn("source_file", metadata)
        self.assertIn("pages", metadata)
        self.assertIn("title", metadata)
        self.assertIn("author", metadata)
        self.assertIn("document_id", metadata)
        
        self.assertEqual(metadata["pages"], 1)
        self.assertEqual(metadata["title"], "Test Title")
        self.assertEqual(metadata["author"], "Test Author")
    
    def test_document_id_present(self):
        """Test that document ID is generated."""
        metadata = extract_pdf_metadata(self.temp_pdf.name)
        self.assertEqual(len(metadata["document_id"]), 16)
    
    def test_extraction_date_format(self):
        """Test that extraction date is in ISO format."""
        metadata = extract_pdf_metadata(self.temp_pdf.name)
        # Should be parseable as ISO datetime
        datetime.fromisoformat(metadata["extraction_date"])


class TestImageMetadataExtraction(unittest.TestCase):
    """Test image metadata extraction."""
    
    def setUp(self):
        """Create a test image file."""
        self.temp_image = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        self.temp_image.close()
        
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(self.temp_image.name)
    
    def tearDown(self):
        """Clean up test image."""
        if os.path.exists(self.temp_image.name):
            os.unlink(self.temp_image.name)
    
    def test_extract_basic_metadata(self):
        """Test extraction of basic image metadata."""
        metadata = extract_image_metadata(self.temp_image.name)
        
        self.assertIn("source_file", metadata)
        self.assertIn("width", metadata)
        self.assertIn("height", metadata)
        self.assertIn("format", metadata)
        self.assertIn("document_id", metadata)
        
        self.assertEqual(metadata["width"], 100)
        self.assertEqual(metadata["height"], 100)
    
    def test_document_id_present(self):
        """Test that document ID is generated."""
        metadata = extract_image_metadata(self.temp_image.name)
        self.assertEqual(len(metadata["document_id"]), 16)


class TestYAMLFrontmatter(unittest.TestCase):
    """Test YAML frontmatter generation."""
    
    def test_format_pdf_frontmatter(self):
        """Test formatting PDF metadata as YAML."""
        metadata = {
            "source_file": "test.pdf",
            "pages": 5,
            "title": "Test Document",
            "author": "Test Author",
            "extraction_date": "2024-01-15T12:00:00",
            "document_id": "abc123def456"
        }
        
        frontmatter = format_yaml_frontmatter(metadata, "pymupdf4llm", 0.92, "en")
        
        self.assertTrue(frontmatter.startswith("---"))
        self.assertTrue(frontmatter.endswith("---\n"))
        self.assertIn("source_file:", frontmatter)
        self.assertIn("pages: 5", frontmatter)
        self.assertIn("extraction_method:", frontmatter)
        self.assertIn("confidence_score: 0.92", frontmatter)
        self.assertIn("document_id:", frontmatter)
    
    def test_add_frontmatter_to_markdown(self):
        """Test adding frontmatter to Markdown text."""
        metadata = {
            "source_file": "test.pdf",
            "pages": 1,
            "extraction_date": "2024-01-15T12:00:00",
            "document_id": "abc123"
        }
        
        markdown = "# Heading\n\nContent here."
        result = add_yaml_frontmatter(markdown, metadata, "RapidOCR")
        
        self.assertTrue(result.startswith("---"))
        self.assertIn("# Heading", result)
        self.assertIn("Content here.", result)


if __name__ == '__main__':
    unittest.main()
