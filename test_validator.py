"""
Unit tests for validator module
"""

import os
import unittest

# Import the module to test
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from validator import MarkdownValidator, validate_markdown


class TestMarkdownSyntaxValidation(unittest.TestCase):
    """Test Markdown syntax validation."""
    
    def setUp(self):
        """Create validator instance."""
        self.validator = MarkdownValidator()
    
    def test_valid_markdown(self):
        """Test validation of syntactically correct Markdown."""
        markdown = """# Heading

This is a paragraph with **bold** and *italic* text.

- List item 1
- List item 2

| Column 1 | Column 2 |
|----------|----------|
| Data     | Data     |
"""
        result = self.validator.validate_syntax(markdown)
        self.assertTrue(result)
        self.assertEqual(len(self.validator.issues), 0)
    
    def test_unclosed_code_block(self):
        """Test detection of unclosed code blocks."""
        markdown = """# Heading

```python
def test():
    pass

No closing marker!
"""
        result = self.validator.validate_syntax(markdown)
        self.assertFalse(result)
        self.assertTrue(any(issue['type'] == 'unclosed_code_block' for issue in self.validator.issues))
    
    def test_empty_link(self):
        """Test detection of empty links."""
        markdown = "This is a [broken link]() in the text."
        result = self.validator.validate_syntax(markdown)
        self.assertFalse(result)
        self.assertTrue(any(issue['type'] == 'empty_link' for issue in self.validator.issues))
    
    def test_balanced_code_blocks(self):
        """Test that balanced code blocks pass validation."""
        markdown = """```python
code here
```

More text

```javascript
more code
```
"""
        result = self.validator.validate_syntax(markdown)
        self.assertTrue(result)


class TestSchemaCompliance(unittest.TestCase):
    """Test schema compliance validation."""
    
    def setUp(self):
        """Create validator instance."""
        self.validator = MarkdownValidator()
    
    def test_valid_schema(self):
        """Test validation of schema-compliant Markdown."""
        markdown = """---
document:
  source_file: "test.pdf"
  pages: 5
  document_id: "abc123"
---

# Content
"""
        result = self.validator.validate_schema_compliance(markdown)
        self.assertTrue(result)
    
    def test_missing_frontmatter(self):
        """Test detection of missing frontmatter."""
        markdown = "# Heading\n\nContent without frontmatter."
        result = self.validator.validate_schema_compliance(markdown)
        self.assertFalse(result)
        self.assertTrue(any(w['type'] == 'missing_frontmatter' for w in self.validator.warnings))
    
    def test_malformed_frontmatter(self):
        """Test detection of malformed frontmatter."""
        markdown = """---
document:
  source_file: "test.pdf"

No closing marker!

# Content
"""
        result = self.validator.validate_schema_compliance(markdown)
        self.assertFalse(result)
        self.assertTrue(any(issue['type'] == 'malformed_frontmatter' for issue in self.validator.issues))


class TestHallucinationDetection(unittest.TestCase):
    """Test hallucination marker detection."""
    
    def setUp(self):
        """Create validator instance."""
        self.validator = MarkdownValidator()
    
    def test_detect_commentary_phrases(self):
        """Test detection of LLM commentary phrases."""
        markdown = """# Document

Based on the image, this appears to be a financial report.

As shown in this document, the revenue increased.
"""
        markers = self.validator.detect_hallucination_markers(markdown)
        self.assertGreater(len(markers), 0)
        self.assertTrue(any('based on' in m['pattern'] for m in markers))
    
    def test_clean_extraction(self):
        """Test that clean extraction has no markers."""
        markdown = """# Financial Report

Revenue increased by 15% in Q4 2024.

The following table shows quarterly results.
"""
        markers = self.validator.detect_hallucination_markers(markdown)
        self.assertEqual(len(markers), 0)


class TestQualityScoring(unittest.TestCase):
    """Test quality scoring algorithm."""
    
    def setUp(self):
        """Create validator instance."""
        self.validator = MarkdownValidator()
    
    def test_high_quality_score(self):
        """Test scoring of high-quality output."""
        markdown = """---
document:
  source_file: "test.pdf"
  pages: 5
  document_id: "abc123"
---

# Main Heading

This is a paragraph with **formatting**.

| Column 1 | Column 2 |
|----------|----------|
| Data     | Data     |

- List item 1
- List item 2
"""
        score = self.validator.calculate_quality_score(markdown, "OpenRouter/Qwen2.5-VL-72B", 0.95)
        self.assertGreater(score, 0.8)
    
    def test_low_quality_score(self):
        """Test scoring of low-quality output."""
        markdown = "Just plain text with no structure."
        score = self.validator.calculate_quality_score(markdown, "Fallback", 0.5)
        self.assertLess(score, 0.6)
    
    def test_method_scoring(self):
        """Test that extraction method affects score."""
        markdown = "# Test\n\nContent"
        
        score_openrouter = self.validator.calculate_quality_score(markdown, "OpenRouter")
        score_fallback = self.validator.calculate_quality_score(markdown, "Fallback")
        
        self.assertGreater(score_openrouter, score_fallback)


class TestValidationReport(unittest.TestCase):
    """Test comprehensive validation report generation."""
    
    def test_complete_report(self):
        """Test generation of complete validation report."""
        markdown = """---
document:
  source_file: "test.pdf"
  pages: 3
  document_id: "abc123"
---

# Heading

Content with **formatting**.
"""
        report = validate_markdown(markdown, "pymupdf4llm", 0.88)
        
        self.assertIn("quality_score", report)
        self.assertIn("syntax_valid", report)
        self.assertIn("schema_compliant", report)
        self.assertIn("issues", report)
        self.assertIn("warnings", report)
        self.assertIn("hallucination_markers", report)
        self.assertIn("metrics", report)
        
        self.assertIsInstance(report["quality_score"], float)
        self.assertGreaterEqual(report["quality_score"], 0.0)
        self.assertLessEqual(report["quality_score"], 1.0)
    
    def test_metrics_calculation(self):
        """Test that metrics are calculated correctly."""
        markdown = "# Test\n\nThis is a test document with some words."
        report = validate_markdown(markdown)
        
        self.assertIn("word_count", report["metrics"])
        self.assertIn("line_count", report["metrics"])
        self.assertGreater(report["metrics"]["word_count"], 0)
        self.assertGreater(report["metrics"]["line_count"], 0)


if __name__ == '__main__':
    unittest.main()
