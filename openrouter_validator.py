"""
OpenRouter Output Validation Module

Validates LLM-generated Markdown for hallucinations, semantic compliance,
and quality issues specific to OpenRouter extraction.
"""

import re
from typing import Dict, List, Any, Optional
import validator  # Use existing validator module


def detect_hallucination_phrases(markdown_text: str) -> List[Dict[str, Any]]:
    """
    Detect phrases that indicate LLM hallucination or commentary.
    
    Args:
        markdown_text: Markdown content to check
    
    Returns:
        List of detected hallucination markers with locations
    """
    hallucination_patterns = [
        (r'based on (the|this) (image|document|page)', "commentary_phrase"),
        (r'as (shown|seen|depicted) in (the|this)', "commentary_phrase"),
        (r'it appears (that|to be)', "speculation"),
        (r'this (seems|looks like)', "speculation"),
        (r'I (can see|notice|observe|believe)', "first_person"),
        (r'the (image|document) (shows|contains|displays)', "meta_reference"),
        (r'from what I can (see|tell|determine)', "uncertainty"),
        (r'(probably|possibly|likely|perhaps)', "hedging"),
    ]
    
    markers = []
    lines = markdown_text.split('\n')
    
    for i, line in enumerate(lines, 1):
        # Skip HTML comments (these are semantic annotations, not content)
        if line.strip().startswith('<!--'):
            continue
            
        for pattern, marker_type in hallucination_patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                markers.append({
                    "type": "hallucination",
                    "subtype": marker_type,
                    "line": i,
                    "text": line.strip(),
                    "matched_phrase": match.group(0),
                    "severity": "high"
                })
    
    return markers


def validate_semantic_annotations(markdown_text: str) -> Dict[str, Any]:
    """
    Validate presence and correctness of semantic annotations.
    
    Args:
        markdown_text: Markdown content to validate
    
    Returns:
        Validation results with coverage metrics
    """
    results = {
        "has_page_markers": False,
        "has_role_annotations": False,
        "page_count": 0,
        "role_count": 0,
        "role_types": set(),
        "issues": []
    }
    
    # Check for page markers
    page_markers = re.findall(r'<!-- page:(\d+) -->', markdown_text)
    if page_markers:
        results["has_page_markers"] = True
        results["page_count"] = len(page_markers)
        
        # Validate sequential page numbers
        page_numbers = [int(p) for p in page_markers]
        if page_numbers != list(range(1, len(page_numbers) + 1)):
            results["issues"].append({
                "type": "non_sequential_pages",
                "message": f"Page numbers not sequential: {page_numbers}"
            })
    else:
        results["issues"].append({
            "type": "missing_page_markers",
            "message": "No page boundary markers found"
        })
    
    # Check for role annotations
    role_pattern = r'<!-- role:(\w+)(?:\s+([^>]+))? -->'
    role_matches = re.findall(role_pattern, markdown_text)
    
    if role_matches:
        results["has_role_annotations"] = True
        results["role_count"] = len(role_matches)
        results["role_types"] = set(role for role, _ in role_matches)
    else:
        results["issues"].append({
            "type": "missing_role_annotations",
            "message": "No semantic role annotations found"
        })
    
    # Validate role types
    valid_roles = {
        'heading', 'paragraph', 'table', 'list', 'figure', 
        'caption', 'footnote', 'equation', 'code',
        'header', 'footer', 'page_number', 'artifact', 'watermark'
    }
    
    invalid_roles = results["role_types"] - valid_roles
    if invalid_roles:
        results["issues"].append({
            "type": "invalid_role_types",
            "message": f"Invalid role types found: {invalid_roles}"
        })
    
    return results


def validate_reading_order(markdown_text: str) -> Dict[str, Any]:
    """
    Validate reading order markers and detect potential issues.
    
    Args:
        markdown_text: Markdown content to validate
    
    Returns:
        Reading order validation results
    """
    results = {
        "has_reading_order": False,
        "order_count": 0,
        "issues": []
    }
    
    # Check for reading order markers
    order_markers = re.findall(r'<!-- reading-order:(\d+) -->', markdown_text)
    
    if order_markers:
        results["has_reading_order"] = True
        results["order_count"] = len(order_markers)
        
        # Validate sequential order
        order_numbers = [int(o) for o in order_markers]
        if order_numbers != list(range(1, len(order_numbers) + 1)):
            results["issues"].append({
                "type": "non_sequential_order",
                "message": f"Reading order not sequential: {order_numbers}"
            })
    
    return results


def estimate_completeness(markdown_text: str, page_count: int, expected_word_count: Optional[int] = None) -> Dict[str, Any]:
    """
    Estimate extraction completeness using heuristics or provided word count.
    
    Args:
        markdown_text: Extracted Markdown content
        page_count: Number of pages in original document
        expected_word_count: Optional expected word count from source metadata
    
    Returns:
        Completeness metrics
    """
    # Remove semantic annotations for word count
    clean_text = re.sub(r'<!--.*?-->', '', markdown_text, flags=re.DOTALL)
    
    word_count = len(clean_text.split())
    line_count = len([l for l in clean_text.split('\n') if l.strip()])
    
    # Calculate expected range
    if expected_word_count and expected_word_count > 0:
        # If we have ground truth (e.g. from PDF text layer), use it
        # OCR might extract slightly more (headers/footers) or less (layout issues)
        # Allow 20% variance
        expected_words_min = int(expected_word_count * 0.8)
        expected_words_max = int(expected_word_count * 1.5) # Allow more for artifacts/hallucinations
    else:
        # Heuristic: expect ~200-500 words per page for typical documents
        expected_words_min = page_count * 150
        expected_words_max = page_count * 600
    
    completeness_score = 1.0
    issues = []
    
    if word_count < expected_words_min:
        completeness_score = word_count / expected_words_min if expected_words_min > 0 else 0
        issues.append({
            "type": "possibly_incomplete",
            "message": f"Word count ({word_count}) below expected minimum ({expected_words_min})",
            "severity": "medium"
        })
    elif word_count > expected_words_max:
        issues.append({
            "type": "possibly_excessive",
            "message": f"Word count ({word_count}) above expected maximum ({expected_words_max})",
            "severity": "low"
        })
    
    return {
        "word_count": word_count,
        "line_count": line_count,
        "expected_range": (expected_words_min, expected_words_max),
        "completeness_score": completeness_score,
        "issues": issues
    }


def validate_openrouter_output(markdown_text: str, 
                               page_count: int,
                               original_method: str = "OpenRouter",
                               expected_word_count: Optional[int] = None) -> Dict[str, Any]:
    """
    Comprehensive validation of OpenRouter extraction output.
    
    Args:
        markdown_text: Extracted Markdown content
        page_count: Number of pages in original document
        original_method: Extraction method name
        expected_word_count: Optional expected word count from source metadata
    
    Returns:
        Comprehensive validation report
    """
    # Run all validation checks
    hallucinations = detect_hallucination_phrases(markdown_text)
    semantic_validation = validate_semantic_annotations(markdown_text)
    reading_order = validate_reading_order(markdown_text)
    completeness = estimate_completeness(markdown_text, page_count, expected_word_count)
    
    # Use existing validator for base checks
    base_validation = validator.validate_markdown(markdown_text, original_method)
    
    # Calculate enhanced quality score
    quality_penalties = 0
    
    # Penalize hallucinations heavily
    if hallucinations:
        quality_penalties += len(hallucinations) * 0.1
    
    # Penalize missing semantic annotations
    if not semantic_validation["has_page_markers"]:
        quality_penalties += 0.15
    if not semantic_validation["has_role_annotations"]:
        quality_penalties += 0.15
    
    # Penalize incompleteness
    quality_penalties += (1.0 - completeness["completeness_score"]) * 0.2
    
    # Adjust base quality score
    enhanced_quality_score = max(0.0, base_validation["quality_score"] - quality_penalties)
    
    # Compile comprehensive report
    all_issues = (
        hallucinations +
        semantic_validation["issues"] +
        reading_order["issues"] +
        completeness["issues"] +
        base_validation["issues"]
    )
    
    return {
        "quality_score": enhanced_quality_score,
        "base_quality_score": base_validation["quality_score"],
        "hallucination_count": len(hallucinations),
        "hallucinations": hallucinations,
        "semantic_annotations": semantic_validation,
        "reading_order": reading_order,
        "completeness": completeness,
        "syntax_valid": base_validation["syntax_valid"],
        "schema_compliant": base_validation["schema_compliant"],
        "issues": all_issues,
        "warnings": base_validation["warnings"],
        "metrics": {
            **base_validation["metrics"],
            "page_markers": semantic_validation["page_count"],
            "role_annotations": semantic_validation["role_count"],
            "completeness_score": completeness["completeness_score"]
        }
    }


# Example usage
if __name__ == "__main__":
    sample_output = """<!-- page:1 -->

<!-- role:heading level:1 -->
# Document Title

<!-- role:paragraph -->
This is the extracted content from the document.

<!-- role:table -->
| Column 1 | Column 2 |
|----------|----------|
| Data     | Data     |

Based on the image, this appears to be a financial report.
"""
    
    report = validate_openrouter_output(sample_output, page_count=1)
    
    print("Validation Report:")
    print(f"Quality Score: {report['quality_score']:.2f}")
    print(f"Hallucinations: {report['hallucination_count']}")
    print(f"Page Markers: {report['semantic_annotations']['page_count']}")
    print(f"Role Annotations: {report['semantic_annotations']['role_count']}")
    
    if report['hallucinations']:
        print("\nHallucination Detected:")
        for h in report['hallucinations']:
            print(f"  Line {h['line']}: {h['matched_phrase']}")
