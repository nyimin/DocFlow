"""
Unit tests for layout_analyzer module
"""

import os
import unittest
import numpy as np

# Import the module to test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from layout_analyzer import LayoutAnalyzer


class TestColumnDetection(unittest.TestCase):
    """Test column detection functionality."""
    
    def setUp(self):
        self.analyzer = LayoutAnalyzer(column_gap_threshold=50)
    
    def test_single_column(self):
        """Test detection of single-column layout."""
        elements = [
            {'bbox': (50, 100, 250, 120)},
            {'bbox': (50, 130, 250, 150)},
            {'bbox': (50, 160, 250, 180)},
        ]
        
        columns = self.analyzer.detect_columns(elements)
        self.assertEqual(len(columns), 1)
    
    def test_two_columns(self):
        """Test detection of two-column layout."""
        elements = [
            {'bbox': (50, 100, 250, 120)},   # Column 1
            {'bbox': (350, 100, 550, 120)},  # Column 2 (gap > 50)
            {'bbox': (50, 130, 250, 150)},   # Column 1
            {'bbox': (350, 130, 550, 150)},  # Column 2
        ]
        
        columns = self.analyzer.detect_columns(elements)
        self.assertEqual(len(columns), 2)
        self.assertLess(columns[0]['x_min'], columns[1]['x_min'])
    
    def test_three_columns(self):
        """Test detection of three-column layout (newspaper style)."""
        elements = [
            {'bbox': (50, 100, 200, 120)},    # Column 1
            {'bbox': (270, 100, 420, 120)},   # Column 2
            {'bbox': (490, 100, 640, 120)},   # Column 3
        ]
        
        columns = self.analyzer.detect_columns(elements)
        self.assertEqual(len(columns), 3)


class TestColumnAssignment(unittest.TestCase):
    """Test column ID assignment."""
    
    def setUp(self):
        self.analyzer = LayoutAnalyzer(column_gap_threshold=50)
    
    def test_assign_to_correct_column(self):
        """Test that elements are assigned to correct columns."""
        elements = [
            {'bbox': (50, 100, 250, 120), 'text': 'Col1'},
            {'bbox': (350, 100, 550, 120), 'text': 'Col2'},
        ]
        
        columns = self.analyzer.detect_columns(elements)
        elements = self.analyzer.assign_column_ids(elements, columns)
        
        self.assertEqual(elements[0]['column_id'], 0)
        self.assertEqual(elements[1]['column_id'], 1)


class TestXYCutSorting(unittest.TestCase):
    """Test XY-cut reading order algorithm."""
    
    def setUp(self):
        self.analyzer = LayoutAnalyzer(column_gap_threshold=50)
    
    def test_single_column_order(self):
        """Test top-to-bottom order in single column."""
        elements = [
            {'bbox': (50, 200, 250, 220), 'column_id': 0, 'text': 'Third'},
            {'bbox': (50, 100, 250, 120), 'column_id': 0, 'text': 'First'},
            {'bbox': (50, 150, 250, 170), 'column_id': 0, 'text': 'Second'},
        ]
        
        sorted_elems = self.analyzer.xy_cut_sort(elements)
        
        self.assertEqual(sorted_elems[0]['text'], 'First')
        self.assertEqual(sorted_elems[1]['text'], 'Second')
        self.assertEqual(sorted_elems[2]['text'], 'Third')
        self.assertEqual(sorted_elems[0]['reading_order'], 1)
        self.assertEqual(sorted_elems[2]['reading_order'], 3)
    
    def test_two_column_order(self):
        """Test left-to-right, then top-to-bottom order."""
        elements = [
            {'bbox': (350, 150, 550, 170), 'column_id': 1, 'text': 'Col2-Line2'},
            {'bbox': (50, 100, 250, 120), 'column_id': 0, 'text': 'Col1-Line1'},
            {'bbox': (350, 100, 550, 120), 'column_id': 1, 'text': 'Col2-Line1'},
            {'bbox': (50, 150, 250, 170), 'column_id': 0, 'text': 'Col1-Line2'},
        ]
        
        sorted_elems = self.analyzer.xy_cut_sort(elements)
        
        # Should be: Col1-Line1, Col1-Line2, Col2-Line1, Col2-Line2
        self.assertEqual(sorted_elems[0]['text'], 'Col1-Line1')
        self.assertEqual(sorted_elems[1]['text'], 'Col1-Line2')
        self.assertEqual(sorted_elems[2]['text'], 'Col2-Line1')
        self.assertEqual(sorted_elems[3]['text'], 'Col2-Line2')


class TestSemanticRoleClassification(unittest.TestCase):
    """Test semantic role classification."""
    
    def setUp(self):
        self.analyzer = LayoutAnalyzer()
        self.page_elements = [
            {'bbox': (50, 100, 250, 130), 'text': 'Normal text'},
            {'bbox': (50, 140, 250, 160), 'text': 'More text'},
        ]
    
    def test_heading_detection(self):
        """Test heading detection (short text, larger font)."""
        elem = {'bbox': (50, 50, 250, 90), 'text': 'Chapter Title'}  # Taller bbox
        role = self.analyzer.classify_semantic_role(elem, self.page_elements)
        self.assertEqual(role, 'heading')
    
    def test_list_item_detection(self):
        """Test list item detection."""
        test_cases = [
            {'text': '• First item', 'expected': 'list_item'},
            {'text': '- Second item', 'expected': 'list_item'},
            {'text': '1. Numbered item', 'expected': 'list_item'},
            {'text': '2) Another item', 'expected': 'list_item'},
        ]
        
        for case in test_cases:
            elem = {'bbox': (50, 100, 250, 120), 'text': case['text']}
            role = self.analyzer.classify_semantic_role(elem, self.page_elements)
            self.assertEqual(role, case['expected'])
    
    def test_caption_detection(self):
        """Test caption detection."""
        elem = {'bbox': (50, 300, 250, 320), 'text': 'Figure 1: Example diagram'}
        role = self.analyzer.classify_semantic_role(elem, self.page_elements)
        self.assertEqual(role, 'caption')


class TestConfidenceFiltering(unittest.TestCase):
    """Test OCR confidence filtering."""
    
    def setUp(self):
        self.analyzer = LayoutAnalyzer()
    
    def test_filter_by_threshold(self):
        """Test filtering elements by confidence threshold."""
        elements = [
            {'text': 'High confidence', 'confidence': 0.95},
            {'text': 'Medium confidence', 'confidence': 0.75},
            {'text': 'Low confidence', 'confidence': 0.55},
        ]
        
        high_conf, low_conf = self.analyzer.filter_by_confidence(elements, threshold=0.7)
        
        self.assertEqual(len(high_conf), 2)
        self.assertEqual(len(low_conf), 1)
        self.assertTrue(low_conf[0]['uncertain'])


class TestComprehensiveAnalysis(unittest.TestCase):
    """Test comprehensive page layout analysis."""
    
    def setUp(self):
        self.analyzer = LayoutAnalyzer(column_gap_threshold=50)
    
    def test_full_analysis(self):
        """Test complete layout analysis pipeline."""
        elements = [
            {'text': 'Title', 'bbox': (50, 50, 250, 90), 'confidence': 0.95},
            {'text': 'Column 1 text', 'bbox': (50, 100, 250, 120), 'confidence': 0.92},
            {'text': 'Column 2 text', 'bbox': (350, 100, 550, 120), 'confidence': 0.88},
            {'text': 'Low conf text', 'bbox': (50, 150, 250, 170), 'confidence': 0.60},
        ]
        
        result = self.analyzer.analyze_page_layout(elements, confidence_threshold=0.7)
        
        self.assertGreater(result['column_count'], 0)
        self.assertTrue(result['reading_order_applied'])
        self.assertEqual(result['high_confidence_count'], 3)
        self.assertEqual(result['low_confidence_count'], 1)
        self.assertEqual(len(result['elements']), 4)
        
        # Check that all elements have required fields
        for elem in result['elements']:
            self.assertIn('reading_order', elem)
            self.assertIn('semantic_role', elem)


if __name__ == '__main__':
    unittest.main()
