"""
RapidOCR Validator Module

Validates RapidOCR extraction output for quality, completeness, and layout analysis accuracy.
"""

from typing import Dict, Any, List, Tuple
import re
import validator  # Existing base validator


def validate_layout_analysis(markdown_text: str, 
                             expected_columns: int = None) -> Dict[str, Any]:
    """
    Validate layout analysis quality.
    
    Args:
        markdown_text: Extracted Markdown content
        expected_columns: Expected number of columns (if known)
    
    Returns:
        Layout validation results
    """
    issues = []
    
    # Check for page markers
    page_markers = re.findall(r'<!-- page:(\d+) -->', markdown_text)
    has_page_markers = len(page_markers) > 0
    page_count = len(page_markers)
    
    if not has_page_markers:
        issues.append({
            "type": "missing_page_markers",
            "severity": "warning",
            "message": "No page markers found"
        })
    
    # Check for reading order markers (indicates multi-column detection)
    reading_order_markers = re.findall(r'<!-- reading-order:(\d+) -->', markdown_text)
    has_reading_order = len(reading_order_markers) > 0
    
    # Check for column consistency (reading order should be sequential)
    if has_reading_order:
        order_numbers = [int(m) for m in reading_order_markers]
        expected_sequence = list(range(1, len(order_numbers) + 1))
        
        if order_numbers != expected_sequence:
            issues.append({
                "type": "reading_order_inconsistent",
                "severity": "error",
                "message": f"Reading order not sequential: {order_numbers}"
            })
    
    # Estimate column count from reading order density
    detected_columns = 1
    if has_reading_order and page_count > 0:
        avg_elements_per_page = len(reading_order_markers) / page_count
        # Heuristic: 2+ columns if >20 elements per page with reading order
        if avg_elements_per_page > 20:
            detected_columns = 2
        if avg_elements_per_page > 40:
            detected_columns = 3
    
    # Validate against expected columns
    if expected_columns and detected_columns != expected_columns:
        issues.append({
            "type": "column_count_mismatch",
            "severity": "warning",
            "message": f"Expected {expected_columns} columns, detected {detected_columns}"
        })
    
    return {
        "has_page_markers": has_page_markers,
        "page_count": page_count,
        "has_reading_order": has_reading_order,
        "detected_columns": detected_columns,
        "reading_order_count": len(reading_order_markers),
        "issues": issues
    }


def validate_semantic_annotations(markdown_text: str) -> Dict[str, Any]:
    """
    Validate semantic role annotations.
    
    Args:
        markdown_text: Extracted Markdown content
    
    Returns:
        Semantic annotation validation results
    """
    issues = []
    
    # Extract all role annotations
    role_pattern = r'<!-- role:(\w+)(?: .*?)? -->'
    roles = re.findall(role_pattern, markdown_text)
    
    # Valid role types
    valid_roles = {'heading', 'paragraph', 'list_item', 'table', 'caption', 'footnote'}
    
    # Check for invalid roles
    invalid_roles = [r for r in roles if r not in valid_roles]
    if invalid_roles:
        issues.append({
            "type": "invalid_role_types",
            "severity": "error",
            "message": f"Invalid role types found: {set(invalid_roles)}"
        })
    
    # Count role distribution
    role_distribution = {}
    for role in roles:
        role_distribution[role] = role_distribution.get(role, 0) + 1
    
    # Check for semantic coverage (should have at least some annotations)
    has_annotations = len(roles) > 0
    
    if not has_annotations:
        issues.append({
            "type": "missing_semantic_annotations",
            "severity": "warning",
            "message": "No semantic role annotations found"
        })
    
    return {
        "has_annotations": has_annotations,
        "role_count": len(roles),
        "role_distribution": role_distribution,
        "invalid_roles": list(set(invalid_roles)),
        "issues": issues
    }


def analyze_confidence_distribution(markdown_text: str) -> Dict[str, Any]:
    """
    Analyze OCR confidence score distribution.
    
    Args:
        markdown_text: Extracted Markdown content
    
    Returns:
        Confidence analysis results
    """
    issues = []
    
    # Extract confidence markers
    confidence_pattern = r'<!-- confidence:(0\.\d+) -->'
    confidence_scores = [float(c) for c in re.findall(confidence_pattern, markdown_text)]
    
    # Extract uncertain text markers
    uncertain_pattern = r'\[uncertain: (.*?)\]'
    uncertain_texts = re.findall(uncertain_pattern, markdown_text)
    uncertain_count = len(uncertain_texts)
    
    # Calculate statistics
    if confidence_scores:
        avg_low_confidence = sum(confidence_scores) / len(confidence_scores)
        min_confidence = min(confidence_scores)
    else:
        avg_low_confidence = None
        min_confidence = None
    
    # Flag if too much uncertain text
    total_lines = len(markdown_text.split('\n'))
    uncertain_percentage = (uncertain_count / total_lines * 100) if total_lines > 0 else 0
    
    if uncertain_percentage > 20:
        issues.append({
            "type": "high_uncertainty",
            "severity": "warning",
            "message": f"{uncertain_percentage:.1f}% of text marked as uncertain"
        })
    
    if min_confidence and min_confidence < 0.5:
        issues.append({
            "type": "very_low_confidence",
            "severity": "error",
            "message": f"Minimum confidence score: {min_confidence:.2f}"
        })
    
    return {
        "low_confidence_count": len(confidence_scores),
        "uncertain_count": uncertain_count,
        "uncertain_percentage": uncertain_percentage,
        "avg_low_confidence": avg_low_confidence,
        "min_confidence": min_confidence,
        "issues": issues
    }


def estimate_extraction_completeness(markdown_text: str, 
                                     page_count: int,
                                     expected_words_per_page: Tuple[int, int] = (150, 600)) -> Dict[str, Any]:
    """
    Estimate extraction completeness based on word count.
    
    Args:
        markdown_text: Extracted Markdown content
        page_count: Number of pages in document
        expected_words_per_page: (min, max) expected words per page
    
    Returns:
        Completeness estimation results
    """
    issues = []
    
    # Remove HTML comments for word count
    text_only = re.sub(r'<!--.*?-->', '', markdown_text, flags=re.DOTALL)
    
    # Count words
    words = text_only.split()
    word_count = len(words)
    
    # Calculate expected range
    min_expected = page_count * expected_words_per_page[0]
    max_expected = page_count * expected_words_per_page[1]
    
    # Calculate completeness score
    if word_count < min_expected:
        completeness_score = word_count / min_expected
        issues.append({
            "type": "possibly_incomplete",
            "severity": "warning",
            "message": f"Word count ({word_count}) below expected minimum ({min_expected})"
        })
    elif word_count > max_expected:
        completeness_score = 1.0
        # Not necessarily an issue - could be dense document
    else:
        completeness_score = 1.0
    
    return {
        "word_count": word_count,
        "expected_range": (min_expected, max_expected),
        "completeness_score": completeness_score,
        "issues": issues
    }


def validate_rapidocr_output(markdown_text: str,
                             page_count: int,
                             original_method: str = "RapidOCR",
                             expected_columns: int = None) -> Dict[str, Any]:
    """
    Comprehensive validation of RapidOCR extraction output.
    
    Args:
        markdown_text: Extracted Markdown content
        page_count: Number of pages in original document
        original_method: Extraction method name
        expected_columns: Expected number of columns (if known)
    
    Returns:
        Comprehensive validation report
    """
    # Run all validation checks
    layout_validation = validate_layout_analysis(markdown_text, expected_columns)
    semantic_validation = validate_semantic_annotations(markdown_text)
    confidence_analysis = analyze_confidence_distribution(markdown_text)
    completeness = estimate_extraction_completeness(markdown_text, page_count)
    
    # Use existing validator for base checks
    base_validation = validator.validate_markdown(markdown_text, original_method)
    
    # Calculate enhanced quality score
    quality_penalties = 0
    
    # Penalize missing page markers
    if not layout_validation["has_page_markers"]:
        quality_penalties += 0.15
    
    # Penalize missing semantic annotations
    if not semantic_validation["has_annotations"]:
        quality_penalties += 0.10
    
    # Penalize high uncertainty
    if confidence_analysis["uncertain_percentage"] > 20:
        quality_penalties += 0.15
    
    # Penalize incompleteness
    quality_penalties += (1.0 - completeness["completeness_score"]) * 0.20
    
    # Penalize layout issues
    layout_error_count = sum(1 for issue in layout_validation["issues"] 
                             if issue["severity"] == "error")
    quality_penalties += layout_error_count * 0.10
    
    # Adjust base quality score
    enhanced_quality_score = max(0.0, base_validation["quality_score"] - quality_penalties)
    
    # Compile comprehensive report
    all_issues = (
        layout_validation["issues"] +
        semantic_validation["issues"] +
        confidence_analysis["issues"] +
        completeness["issues"] +
        base_validation["issues"]
    )
    
    return {
        "quality_score": enhanced_quality_score,
        "base_quality_score": base_validation["quality_score"],
        "layout_analysis": layout_validation,
        "semantic_annotations": semantic_validation,
        "confidence_analysis": confidence_analysis,
        "completeness": completeness,
        "syntax_valid": base_validation["syntax_valid"],
        "schema_compliant": base_validation["schema_compliant"],
        "issues": all_issues,
        "warnings": base_validation["warnings"],
        "metrics": {
            **base_validation["metrics"],
            "page_count": layout_validation["page_count"],
            "detected_columns": layout_validation["detected_columns"],
            "role_annotations": semantic_validation["role_count"],
            "uncertain_percentage": confidence_analysis["uncertain_percentage"],
            "completeness_score": completeness["completeness_score"]
        }
    }


# Example usage
if __name__ == "__main__":
    # Sample RapidOCR output
    sample_output = """<!-- page:1 -->

<!-- role:heading -->
# Introduction

This is a sample document with layout analysis.

<!-- role:paragraph -->
First paragraph of content.

<!-- confidence:0.65 -->
[uncertain: Some blurry text here]

<!-- role:table -->
| Header 1 | Header 2 |
|----------|----------|
| Data 1   | Data 2   |
"""
    
    report = validate_rapidocr_output(
        sample_output,
        page_count=1,
        original_method="RapidOCR"
    )
    
    print(f"Quality Score: {report['quality_score']:.2f}")
    print(f"Page Count: {report['layout_analysis']['page_count']}")
    print(f"Detected Columns: {report['layout_analysis']['detected_columns']}")
    print(f"Role Annotations: {report['semantic_annotations']['role_count']}")
    print(f"Uncertain %: {report['confidence_analysis']['uncertain_percentage']:.1f}%")
    print(f"Issues: {len(report['issues'])}")
