"""
Markdown Validation and Quality Scoring Module

Validates Markdown syntax, schema compliance, and assesses output quality
for RAG-optimized document processing.
"""

import re
from typing import Dict, List, Tuple, Optional, Any


class MarkdownValidator:
    """Validates Markdown syntax and schema compliance."""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
    
    def validate_syntax(self, markdown_text: str) -> bool:
        """
        Validate basic Markdown syntax.
        
        Args:
            markdown_text: Markdown content to validate
        
        Returns:
            True if syntax is valid, False otherwise
        """
        self.issues = []
        is_valid = True
        
        lines = markdown_text.split('\n')
        
        # Check for common syntax errors
        for i, line in enumerate(lines, 1):
            # Unclosed code blocks
            if line.strip().startswith('```'):
                # Count code block markers
                pass  # Will implement full check below
            
            # Malformed tables
            if '|' in line and not line.strip().startswith('|'):
                # Check if it's actually a table
                if line.count('|') >= 2:
                    parts = line.split('|')
                    if len(parts) < 3:
                        self.issues.append({
                            "type": "malformed_table",
                            "line": i,
                            "message": "Table row has insufficient columns"
                        })
                        is_valid = False
            
            # Unmatched brackets
            if line.count('[') != line.count(']'):
                self.warnings.append({
                    "type": "unmatched_brackets",
                    "line": i,
                    "message": "Unmatched square brackets (may be intentional)"
                })
            
            # Unmatched parentheses in links
            link_pattern = r'\[([^\]]+)\]\(([^\)]*)\)'
            links = re.findall(link_pattern, line)
            for text, url in links:
                if not url:
                    self.issues.append({
                        "type": "empty_link",
                        "line": i,
                        "message": f"Empty URL in link: [{text}]()"
                    })
                    is_valid = False
        
        # Check for balanced code blocks
        code_block_count = markdown_text.count('```')
        if code_block_count % 2 != 0:
            self.issues.append({
                "type": "unclosed_code_block",
                "line": None,
                "message": "Unclosed code block (odd number of ``` markers)"
            })
            is_valid = False
        
        return is_valid
    
    def validate_schema_compliance(self, markdown_text: str) -> bool:
        """
        Validate compliance with RAG-optimized Markdown schema.
        
        Checks for:
        - YAML frontmatter presence
        - Semantic role annotations
        - Page boundary markers
        
        Args:
            markdown_text: Markdown content to validate
        
        Returns:
            True if schema-compliant, False otherwise
        """
        is_compliant = True
        
        # Check for YAML frontmatter
        if not markdown_text.strip().startswith('---'):
            self.warnings.append({
                "type": "missing_frontmatter",
                "message": "Document lacks YAML frontmatter (metadata not preserved)"
            })
            is_compliant = False
        else:
            # Validate frontmatter structure
            frontmatter_end = markdown_text.find('---', 3)
            if frontmatter_end == -1:
                self.issues.append({
                    "type": "malformed_frontmatter",
                    "message": "YAML frontmatter not properly closed"
                })
                is_compliant = False
            else:
                frontmatter = markdown_text[3:frontmatter_end]
                # Check for required fields
                required_fields = ['document:', 'source_file:', 'document_id:']
                for field in required_fields:
                    if field not in frontmatter:
                        self.warnings.append({
                            "type": "missing_metadata_field",
                            "message": f"Missing required field: {field}"
                        })
        
        # Check for semantic annotations (optional but recommended)
        has_annotations = bool(re.search(r'<!-- role:\w+ -->', markdown_text))
        if not has_annotations:
            self.warnings.append({
                "type": "missing_semantic_annotations",
                "message": "No semantic role annotations found (reduces RAG effectiveness)"
            })
        
        return is_compliant
    
    def detect_hallucination_markers(self, markdown_text: str) -> List[Dict[str, Any]]:
        """
        Detect potential LLM hallucinations in extracted text.
        
        Looks for phrases that suggest the LLM is commenting rather than extracting.
        
        Args:
            markdown_text: Markdown content to check
        
        Returns:
            List of detected hallucination markers with locations
        """
        hallucination_patterns = [
            r'based on (the|this) (image|document|page)',
            r'as (shown|seen|depicted) in (the|this)',
            r'it appears (that|to be)',
            r'this (seems|looks like)',
            r'I (can see|notice|observe)',
            r'the (image|document) (shows|contains|displays)',
            r'from what I can (see|tell)',
        ]
        
        markers = []
        lines = markdown_text.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern in hallucination_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    markers.append({
                        "type": "possible_hallucination",
                        "line": i,
                        "text": line.strip(),
                        "pattern": pattern
                    })
        
        return markers
    
    def calculate_quality_score(self, markdown_text: str, 
                               extraction_method: str = "",
                               ocr_confidence: Optional[float] = None) -> float:
        """
        Calculate overall quality score for Markdown output.
        
        Scoring factors:
        - Syntax validity (0-30 points)
        - Schema compliance (0-20 points)
        - Content richness (0-20 points)
        - Extraction method quality (0-20 points)
        - OCR confidence (0-10 points)
        
        Args:
            markdown_text: Markdown content to score
            extraction_method: Name of extraction engine used
            ocr_confidence: Optional OCR confidence score (0.0-1.0)
        
        Returns:
            Quality score from 0.0 to 1.0
        """
        score = 0.0
        
        # 1. Syntax validity (30 points)
        syntax_valid = self.validate_syntax(markdown_text)
        if syntax_valid:
            score += 30
        else:
            # Partial credit based on issue severity
            score += max(0, 30 - len(self.issues) * 5)
        
        # 2. Schema compliance (20 points)
        schema_valid = self.validate_schema_compliance(markdown_text)
        if schema_valid:
            score += 20
        else:
            # Partial credit
            score += max(0, 20 - len([w for w in self.warnings if w['type'].startswith('missing')]) * 5)
        
        # 3. Content richness (20 points)
        has_headings = bool(re.search(r'^#{1,6}\s', markdown_text, re.MULTILINE))
        has_tables = '|' in markdown_text and '---' in markdown_text
        has_lists = bool(re.search(r'^[\-\*\+]\s', markdown_text, re.MULTILINE))
        has_formatting = '**' in markdown_text or '*' in markdown_text
        
        richness_score = 0
        if has_headings: richness_score += 5
        if has_tables: richness_score += 7
        if has_lists: richness_score += 4
        if has_formatting: richness_score += 4
        score += richness_score
        
        # 4. Extraction method quality (20 points)
        method_scores = {
            "OpenRouter": 20,
            "Qwen": 18,
            "Gemini": 17,
            "pymupdf4llm": 15,
            "GMFT": 14,
            "RapidOCR": 12,
            "Fallback": 8
        }
        
        for method, method_score in method_scores.items():
            if method in extraction_method:
                score += method_score
                break
        else:
            score += 10  # Default score
        
        # 5. OCR confidence (10 points)
        if ocr_confidence is not None:
            score += ocr_confidence * 10
        else:
            score += 5  # Neutral score if not applicable
        
        # Normalize to 0.0-1.0
        return min(1.0, score / 100.0)
    
    def get_validation_report(self, markdown_text: str,
                             extraction_method: str = "",
                             ocr_confidence: Optional[float] = None) -> Dict[str, Any]:
        """
        Generate comprehensive validation report.
        
        Args:
            markdown_text: Markdown content to validate
            extraction_method: Name of extraction engine
            ocr_confidence: Optional OCR confidence score
        
        Returns:
            Dictionary containing:
            - quality_score: Overall score (0.0-1.0)
            - syntax_valid: Boolean
            - schema_compliant: Boolean
            - issues: List of critical issues
            - warnings: List of warnings
            - hallucination_markers: List of potential hallucinations
            - metrics: Additional metrics
        """
        # Run all validations
        syntax_valid = self.validate_syntax(markdown_text)
        schema_compliant = self.validate_schema_compliance(markdown_text)
        hallucinations = self.detect_hallucination_markers(markdown_text)
        quality_score = self.calculate_quality_score(markdown_text, extraction_method, ocr_confidence)
        
        # Calculate metrics
        word_count = len(markdown_text.split())
        line_count = len(markdown_text.split('\n'))
        
        return {
            "quality_score": quality_score,
            "syntax_valid": syntax_valid,
            "schema_compliant": schema_compliant,
            "issues": self.issues,
            "warnings": self.warnings,
            "hallucination_markers": hallucinations,
            "metrics": {
                "word_count": word_count,
                "line_count": line_count,
                "avg_confidence": ocr_confidence if ocr_confidence else None
            }
        }


def validate_markdown(markdown_text: str, 
                     extraction_method: str = "",
                     ocr_confidence: Optional[float] = None) -> Dict[str, Any]:
    """
    Convenience function for validating Markdown output.
    
    Args:
        markdown_text: Markdown content to validate
        extraction_method: Name of extraction engine
        ocr_confidence: Optional OCR confidence score
    
    Returns:
        Validation report dictionary
    """
    validator = MarkdownValidator()
    return validator.get_validation_report(markdown_text, extraction_method, ocr_confidence)


# Example usage
if __name__ == "__main__":
    # Test validation
    sample_markdown = """---
document:
  source_file: "test.pdf"
  pages: 5
  extraction_method: "OpenRouter/Qwen2.5-VL-72B"
  document_id: "abc123def456"

metadata:
  title: "Sample Document"
  author: "Test Author"
---

<!-- role:heading level:1 -->
# Main Title

<!-- role:paragraph -->
This is a sample paragraph with **bold** and *italic* text.

<!-- role:table -->
| Column 1 | Column 2 |
|----------|----------|
| Data     | Data     |

<!-- role:list -->
- Item 1
- Item 2
"""
    
    report = validate_markdown(sample_markdown, "OpenRouter/Qwen2.5-VL-72B", 0.92)
    
    print("Validation Report:")
    print(f"Quality Score: {report['quality_score']:.2f}")
    print(f"Syntax Valid: {report['syntax_valid']}")
    print(f"Schema Compliant: {report['schema_compliant']}")
    print(f"\nIssues: {len(report['issues'])}")
    print(f"Warnings: {len(report['warnings'])}")
    print(f"Hallucination Markers: {len(report['hallucination_markers'])}")
