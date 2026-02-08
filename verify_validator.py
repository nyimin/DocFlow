
import sys
import os

# Add local path to sys.path
sys.path.append(os.getcwd())
sys.path.append(r"d:\Triune\Stack Space - Documents\Code\DocFlow")

import openrouter_validator

def test_validator():
    print("--- Starting Validator Verification ---")

    # Test Case 1: New Roles (header, footer, page_number)
    print("\nTest 1: Analyzing Markdown with 'noise' roles...")
    md_with_noise = """<!-- page:1 -->
<!-- role:header -->
CONFIDENTIAL HEADER

<!-- role:paragraph -->
Some content here.

<!-- role:footer -->
Footer text.

<!-- role:page_number -->
Page 1
"""
    results = openrouter_validator.validate_semantic_annotations(md_with_noise)
    print("Issues:", results['issues'])
    
    invalid_issues = [i for i in results['issues'] if i['type'] == 'invalid_role_types']
    if not invalid_issues:
        print("✅ Success: No 'invalid_role_types' errors for header/footer/page_number.")
    else:
        print(f"❌ Failed: Found invalid role errors: {invalid_issues}")


    # Test Case 2: Completeness Check (Low Word Count vs Expected)
    print("\nTest 2: Completeness Check (Mocking 20 words, Expected 1000)...")
    short_text = "Word " * 20
    comp_report = openrouter_validator.estimate_completeness(short_text, page_count=1, expected_word_count=1000)
    print("Completeness Score:", comp_report['completeness_score'])
    print("Issues:", comp_report['issues'])

    if comp_report['completeness_score'] < 0.1 and any(i['type'] == 'possibly_incomplete' for i in comp_report['issues']):
        print("✅ Success: Detected incompleteness correctly.")
    else:
        print("❌ Failed: Did not detect incompleteness.")

    # Test Case 3: Completeness Check (Good match)
    print("\nTest 3: Completeness Check (Mocking 900 words, Expected 1000)...")
    long_text = "Word " * 900
    comp_report_good = openrouter_validator.estimate_completeness(long_text, page_count=1, expected_word_count=1000)
    print("Completeness Score:", comp_report_good['completeness_score'])
    
    if comp_report_good['completeness_score'] == 1.0 and not comp_report_good['issues']:
        print("✅ Success: Recognized good completeness.")
    else:
        print("❌ Failed: Flagged good content as incomplete/excessive.")

if __name__ == "__main__":
    test_validator()
