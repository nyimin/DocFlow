
import sys
import os

# Add local path to sys.path to import modules
sys.path.append(os.getcwd())
sys.path.append(r"d:\Triune\Stack Space - Documents\Code\DocFlow")

from noise_filter import filter_document
from semantic_annotator import SemanticAnnotator

def test_pipeline():
    print("--- Starting Pipeline Verification ---")

    # 1. Create Sample Data (3 pages to trigger repeater detection)
    # Header "CONFIDENTIAL" repeats on all pages.
    # Page numbers repeat.
    pages_elements = [
        [
            {'type': 'text', 'content': 'CONFIDENTIAL', 'y': 10},
            {'type': 'text', 'content': '# Page 1 Content', 'y': 100, 'font_size': 18},
            {'type': 'text', 'content': 'Body text here.', 'y': 150},
            {'type': 'text', 'content': 'Page 1', 'y': 800},
        ],
        [
            {'type': 'text', 'content': 'CONFIDENTIAL', 'y': 10},
            {'type': 'text', 'content': 'Body text page 2.', 'y': 150},
            {'type': 'text', 'content': 'Page 2', 'y': 800},
        ],
        [
            {'type': 'text', 'content': 'CONFIDENTIAL', 'y': 10},
            {'type': 'text', 'content': 'Body text page 3.', 'y': 150},
            {'type': 'text', 'content': 'Page 3', 'y': 800},
        ]
    ]

    print(f"Input: {len(pages_elements)} pages.")

    # 2. Run Noise Filter (Tag Mode)
    print("\n--- Running Noise Filter (tag_mode=True) ---")
    cleaned_pages, report = filter_document(pages_elements)
    
    # Check Report
    print("Noise Report:", report)

    # Verify Header is KEPT and TAGGED
    page1 = cleaned_pages[0]
    header = next((e for e in page1 if e['content'] == 'CONFIDENTIAL'), None)
    
    if header:
        print(f"✅ Header found in output.")
        if header.get('noise_type') == 'header':
            print(f"✅ Header correctly tagged as 'header'.")
            print(f"   Element: {header}")
        else:
            print(f"❌ Header NOT tagged correctly. Tags: {header.get('noise_type')}")
    else:
        print("❌ Header REMOVED from output (Failed 'Don't-Remove' strategy).")

    # Verify Page Number
    pg_num = next((e for e in page1 if e['content'] == 'Page 1'), None)
    if pg_num:
         print(f"✅ Page number found.")
         if pg_num.get('noise_type') == 'page_number':
             print(f"✅ Page number tagged as 'page_number'.")
         else:
             print(f"❌ Page number NOT tagged. Tags: {pg_num.get('noise_type')}")
    else:
        print("❌ Page number REMOVED.")

    # 3. Run Semantic Annotator
    print("\n--- Running Semantic Annotator ---")
    annotator = SemanticAnnotator()
    markdown_output = annotator.annotate_page(page1, page_num=1)
    
    print("\nGenerated Markdown:")
    print("="*40)
    print(markdown_output)
    print("="*40)

    # Verify Annotations
    if "<!-- role:header -->" in markdown_output and "CONFIDENTIAL" in markdown_output:
        print("✅ Header correctly rendered with <!-- role:header -->")
    else:
        print("❌ Header role annotation MISSING.")

    if "<!-- role:page_number -->" in markdown_output:
        print("✅ Page number correctly rendered with <!-- role:page_number -->")
    else:
        print("❌ Page number role annotation MISSING.")

if __name__ == "__main__":
    test_pipeline()
