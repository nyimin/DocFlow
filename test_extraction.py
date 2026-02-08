
import sys
import os
import json

# Add local path to sys.path
sys.path.append(os.getcwd())
sys.path.append(r"d:\Triune\Stack Space - Documents\Code\DocFlow")

import structure_engine

def run_test():
    input_file = "sample_test.pdf"
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Run create_sample_pdf.py first.")
        return

    print(f"--- Running Extraction Test on {input_file} ---")
    
    # Load .env manually
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ[key] = val.strip().strip('"').strip("'")
    
    # Check for API Key
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("WARNING: OPENROUTER_API_KEY not found in environment.")
        print("Please set it or allow the script to fail gracefully.")
        # Proceeding anyway to see if it grabs it elsewhere or errors out

    # Run Extraction
    try:
        # Using 'balanced' model (Qwen 2.5-VL 32B)
        markdown_text, metadata = structure_engine.extract_with_openrouter(
            input_file, 
            model="balanced",
            api_key=api_key
        )

        if isinstance(markdown_text, str) and markdown_text.startswith("Error"):
            print(f"❌ Extraction Failed: {markdown_text}")
            return

        print("\n✅ Extraction Successful!")
        print(f"Metadata: {json.dumps(metadata, indent=2)}")
        
        print("\n--- Markdown Snippet (First 500 chars) ---")
        print(markdown_text[:500])
        print("...\n")

        print("--- Validation Check ---")
        quality_score = metadata.get('quality_score', 0)
        issues = metadata.get('validation_issues', 0)
        print(f"Quality Score: {quality_score}")
        print(f"Issues Found: {issues}")

        if quality_score > 0.8:
            print("✅ Quality Score indicates success.")
        else:
            print("⚠️ Low Quality Score.")

    except Exception as e:
        print(f"❌ Exception during extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
