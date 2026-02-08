"""
Unit tests for openrouter_validator module
"""

import os
import unittest

# Import the module to test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from openrouter_validator import (
    detect_hallucination_phrases,
    validate_semantic_annotations,
    validate_reading_order,
    estimate_completeness,
    validate_openrouter_output
)


class TestHallucinationDetection(unittest.TestCase):
    """Test hallucination phrase detection."""
    
    def test_detect_commentary_phrases(self):
        """Test detection of commentary phrases."""
        markdown = """# Title

Based on the image, this is a financial report.

As shown in the document, revenue increased.
"""
        markers = detect_hallucination_phrases(markdown)
        self.assertGreater(len(markers), 0)
        self.assertTrue(any('based on' in m['matched_phrase'].lower() for m in markers))
    
    def test_detect_speculation(self):
        """Test detection of speculation phrases."""
        markdown = "It appears that the company is profitable."
        markers = detect_hallucination_phrases(markdown)
        self.assertGreater(len(markers), 0)
        self.assertEqual(markers[0]['subtype'], 'speculation')
    
    def test_clean_extraction(self):
        """Test that clean extraction has no markers."""
        markdown = """<!-- page:1 -->

<!-- role:heading level:1 -->
# Financial Report

<!-- role:paragraph -->
Revenue increased by 15% in Q4 2024.
"""
        markers = detect_hallucination_phrases(markdown)
        self.assertEqual(len(markers), 0)
    
    def test_ignore_html_comments(self):
        """Test that HTML comments are ignored."""
        markdown = "<!-- This appears to be a test comment -->\n\nActual content here."
        markers = detect_hallucination_phrases(markdown)
        self.assertEqual(len(markers), 0)


class TestSemanticAnnotationValidation(unittest.TestCase):
    """Test semantic annotation validation."""
    
    def test_valid_annotations(self):
        """Test validation of correct annotations."""
        markdown = """<!-- page:1 -->

<!-- role:heading level:1 -->
# Title

<!-- role:paragraph -->
Content here.

<!-- page:2 -->

<!-- role:table -->
| A | B |
|---|---|
| 1 | 2 |
"""
        results = validate_semantic_annotations(markdown)
        
        self.assertTrue(results['has_page_markers'])
        self.assertTrue(results['has_role_annotations'])
        self.assertEqual(results['page_count'], 2)
        self.assertGreater(results['role_count'], 0)
    
    def test_missing_page_markers(self):
        """Test detection of missing page markers."""
        markdown = "# Title\n\nContent without page markers."
        results = validate_semantic_annotations(markdown)
        
        self.assertFalse(results['has_page_markers'])
        self.assertTrue(any(i['type'] == 'missing_page_markers' for i in results['issues']))
    
    def test_non_sequential_pages(self):
        """Test detection of non-sequential page numbers."""
        markdown = "<!-- page:1 -->\n\n<!-- page:3 -->\n\n<!-- page:2 -->"
        results = validate_semantic_annotations(markdown)
        
        self.assertTrue(any(i['type'] == 'non_sequential_pages' for i in results['issues']))
    
    def test_invalid_role_types(self):
        """Test detection of invalid role types."""
        markdown = "<!-- role:invalid_type -->\n\nContent"
        results = validate_semantic_annotations(markdown)
        
        self.assertTrue(any(i['type'] == 'invalid_role_types' for i in results['issues']))


class TestReadingOrderValidation(unittest.TestCase):
    """Test reading order validation."""
    
    def test_valid_reading_order(self):
        """Test validation of correct reading order."""
        markdown = """<!-- reading-order:1 -->
First block

<!-- reading-order:2 -->
Second block

<!-- reading-order:3 -->
Third block
"""
        results = validate_reading_order(markdown)
        
        self.assertTrue(results['has_reading_order'])
        self.assertEqual(results['order_count'], 3)
        self.assertEqual(len(results['issues']), 0)
    
    def test_non_sequential_order(self):
        """Test detection of non-sequential reading order."""
        markdown = "<!-- reading-order:1 -->\n\n<!-- reading-order:3 -->\n\n<!-- reading-order:2 -->"
        results = validate_reading_order(markdown)
        
        self.assertTrue(any(i['type'] == 'non_sequential_order' for i in results['issues']))


class TestCompletenessEstimation(unittest.TestCase):
    """Test completeness estimation."""
    
    def test_normal_document(self):
        """Test completeness for normal-length document."""
        # ~300 words for 1 page (within expected range)
        markdown = " ".join(["word"] * 300)
        results = estimate_completeness(markdown, page_count=1)
        
        self.assertGreater(results['completeness_score'], 0.9)
        self.assertEqual(len(results['issues']), 0)
    
    def test_short_document(self):
        """Test detection of possibly incomplete extraction."""
        # Only 50 words for 1 page (below minimum)
        markdown = " ".join(["word"] * 50)
        results = estimate_completeness(markdown, page_count=1)
        
        self.assertLess(results['completeness_score'], 1.0)
        self.assertTrue(any(i['type'] == 'possibly_incomplete' for i in results['issues']))
    
    def test_long_document(self):
        """Test detection of possibly excessive extraction."""
        # 700 words for 1 page (above maximum)
        markdown = " ".join(["word"] * 700)
        results = estimate_completeness(markdown, page_count=1)
        
        self.assertTrue(any(i['type'] == 'possibly_excessive' for i in results['issues']))


class TestComprehensiveValidation(unittest.TestCase):
    """Test comprehensive OpenRouter output validation."""
    
    def test_high_quality_output(self):
        """Test validation of high-quality output."""
        markdown = """<!-- page:1 -->

<!-- role:heading level:1 -->
# Financial Report Q4 2024

<!-- role:paragraph -->
Revenue increased by 15% compared to Q3 2024, reaching $1.5M.

<!-- role:table -->
| Quarter | Revenue | Growth |
|---------|---------|--------|
| Q3      | $1.3M   | +10%   |
| Q4      | $1.5M   | +15%   |
"""
        report = validate_openrouter_output(markdown, page_count=1)
        
        self.assertGreater(report['quality_score'], 0.6)  # Adjusted threshold
        self.assertEqual(report['hallucination_count'], 0)
        self.assertTrue(report['semantic_annotations']['has_page_markers'])
        self.assertTrue(report['semantic_annotations']['has_role_annotations'])
    
    def test_low_quality_output(self):
        """Test validation of low-quality output with hallucinations."""
        markdown = """Based on the image, this appears to be a report.

The document shows revenue data.

It seems like the company is doing well.
"""
        report = validate_openrouter_output(markdown, page_count=1)
        
        self.assertLess(report['quality_score'], 0.5)
        self.assertGreater(report['hallucination_count'], 0)
        self.assertFalse(report['semantic_annotations']['has_page_markers'])


if __name__ == '__main__':
    unittest.main()
