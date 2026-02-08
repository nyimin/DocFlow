"""
Unit tests for rapidocr_validator module
"""

import os
import unittest
import sys

# Import the module to test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rapidocr_validator import (
    validate_layout_analysis,
    validate_semantic_annotations,
    analyze_confidence_distribution,
    estimate_extraction_completeness,
    validate_rapidocr_output
)


class TestLayoutAnalysisValidation(unittest.TestCase):
    """Test layout analysis validation."""
    
    def test_valid_layout_with_page_markers(self):
        """Test validation of output with page markers."""
        markdown = """<!-- page:1 -->

Content here

<!-- page:2 -->

More content"""
        
        result = validate_layout_analysis(markdown)
        
        self.assertTrue(result['has_page_markers'])
        self.assertEqual(result['page_count'], 2)
    
    def test_missing_page_markers(self):
        """Test detection of missing page markers."""
        markdown = "Just some content without markers"
        
        result = validate_layout_analysis(markdown)
        
        self.assertFalse(result['has_page_markers'])
        self.assertEqual(result['page_count'], 0)
        self.assertTrue(any(issue['type'] == 'missing_page_markers' 
                           for issue in result['issues']))
    
    def test_reading_order_detection(self):
        """Test detection of reading order markers."""
        markdown = """<!-- page:1 -->
<!-- reading-order:1 -->
Text 1
<!-- reading-order:2 -->
Text 2"""
        
        result = validate_layout_analysis(markdown)
        
        self.assertTrue(result['has_reading_order'])
        self.assertEqual(result['reading_order_count'], 2)
    
    def test_column_count_estimation(self):
        """Test column count estimation from reading order."""
        # Multi-column document with many elements
        reading_orders = '\n'.join([f'<!-- reading-order:{i} -->\nText {i}' 
                                   for i in range(1, 25)])
        markdown = f"<!-- page:1 -->\n{reading_orders}"
        
        result = validate_layout_analysis(markdown)
        
        self.assertGreater(result['detected_columns'], 1)


class TestSemanticAnnotationValidation(unittest.TestCase):
    """Test semantic annotation validation."""
    
    def test_valid_annotations(self):
        """Test validation of valid semantic annotations."""
        markdown = """<!-- role:heading -->
# Title

<!-- role:paragraph -->
Content here

<!-- role:table -->
| A | B |
|---|---|"""
        
        result = validate_semantic_annotations(markdown)
        
        self.assertTrue(result['has_annotations'])
        self.assertEqual(result['role_count'], 3)
        self.assertIn('heading', result['role_distribution'])
        self.assertIn('paragraph', result['role_distribution'])
        self.assertIn('table', result['role_distribution'])
    
    def test_invalid_role_types(self):
        """Test detection of invalid role types."""
        markdown = """<!-- role:invalid_type -->
Content"""
        
        result = validate_semantic_annotations(markdown)
        
        self.assertIn('invalid_type', result['invalid_roles'])
        self.assertTrue(any(issue['type'] == 'invalid_role_types' 
                           for issue in result['issues']))
    
    def test_missing_annotations(self):
        """Test detection of missing annotations."""
        markdown = "Just plain text without annotations"
        
        result = validate_semantic_annotations(markdown)
        
        self.assertFalse(result['has_annotations'])
        self.assertEqual(result['role_count'], 0)


class TestConfidenceAnalysis(unittest.TestCase):
    """Test confidence distribution analysis."""
    
    def test_confidence_markers(self):
        """Test extraction of confidence markers."""
        markdown = """<!-- confidence:0.65 -->
[uncertain: Blurry text]

<!-- confidence:0.58 -->
[uncertain: More blurry text]"""
        
        result = analyze_confidence_distribution(markdown)
        
        self.assertEqual(result['low_confidence_count'], 2)
        self.assertEqual(result['uncertain_count'], 2)
        self.assertIsNotNone(result['avg_low_confidence'])
        self.assertLess(result['avg_low_confidence'], 0.7)
    
    def test_high_uncertainty_warning(self):
        """Test warning for high percentage of uncertain text."""
        # Create markdown with many uncertain lines
        uncertain_lines = '\n'.join(['[uncertain: text]' for _ in range(25)])
        markdown = f"{uncertain_lines}\nNormal text"
        
        result = analyze_confidence_distribution(markdown)
        
        self.assertGreater(result['uncertain_percentage'], 20)
        self.assertTrue(any(issue['type'] == 'high_uncertainty' 
                           for issue in result['issues']))
    
    def test_very_low_confidence_error(self):
        """Test error for very low confidence scores."""
        markdown = "<!-- confidence:0.45 -->\n[uncertain: Very blurry]"
        
        result = analyze_confidence_distribution(markdown)
        
        self.assertLess(result['min_confidence'], 0.5)
        self.assertTrue(any(issue['type'] == 'very_low_confidence' 
                           for issue in result['issues']))


class TestCompletenessEstimation(unittest.TestCase):
    """Test extraction completeness estimation."""
    
    def test_normal_document(self):
        """Test completeness for normal document."""
        # ~300 words (normal for 1 page)
        words = ' '.join(['word'] * 300)
        markdown = f"<!-- page:1 -->\n{words}"
        
        result = estimate_extraction_completeness(markdown, page_count=1)
        
        self.assertEqual(result['completeness_score'], 1.0)
        self.assertGreater(result['word_count'], 250)
    
    def test_incomplete_document(self):
        """Test detection of possibly incomplete extraction."""
        # Only 50 words (low for 1 page)
        words = ' '.join(['word'] * 50)
        markdown = f"<!-- page:1 -->\n{words}"
        
        result = estimate_extraction_completeness(markdown, page_count=1)
        
        self.assertLess(result['completeness_score'], 1.0)
        self.assertTrue(any(issue['type'] == 'possibly_incomplete' 
                           for issue in result['issues']))


class TestComprehensiveValidation(unittest.TestCase):
    """Test comprehensive RapidOCR validation."""
    
    def test_high_quality_output(self):
        """Test validation of high-quality output."""
        markdown = """<!-- page:1 -->

<!-- role:heading -->
# Document Title

<!-- role:paragraph -->
This is a well-extracted document with proper annotations and good confidence scores.

<!-- role:table -->
| Header 1 | Header 2 |
|----------|----------|
| Data 1   | Data 2   |

<!-- role:paragraph -->
More content here with sufficient word count to indicate completeness.
"""
        
        result = validate_rapidocr_output(markdown, page_count=1)
        
        self.assertGreater(result['quality_score'], 0.5)  # Adjusted threshold
        self.assertTrue(result['layout_analysis']['has_page_markers'])
        self.assertTrue(result['semantic_annotations']['has_annotations'])
        self.assertEqual(result['layout_analysis']['page_count'], 1)
    
    def test_low_quality_output(self):
        """Test validation of low-quality output."""
        markdown = """No page markers

<!-- confidence:0.45 -->
[uncertain: Very blurry text]

<!-- confidence:0.52 -->
[uncertain: More blurry text]

<!-- confidence:0.38 -->
[uncertain: Even worse text]
"""
        
        result = validate_rapidocr_output(markdown, page_count=1)
        
        self.assertLess(result['quality_score'], 0.7)
        self.assertFalse(result['layout_analysis']['has_page_markers'])
        self.assertGreater(len(result['issues']), 0)
    
    def test_metrics_tracking(self):
        """Test that all metrics are tracked correctly."""
        markdown = """<!-- page:1 -->

<!-- role:heading -->
# Title

<!-- role:paragraph -->
Content with enough words to pass completeness check.
"""
        
        result = validate_rapidocr_output(markdown, page_count=1)
        
        self.assertIn('page_count', result['metrics'])
        self.assertIn('detected_columns', result['metrics'])
        self.assertIn('role_annotations', result['metrics'])
        self.assertIn('uncertain_percentage', result['metrics'])
        self.assertIn('completeness_score', result['metrics'])


if __name__ == '__main__':
    unittest.main()
