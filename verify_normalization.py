
import sys
import os

# Add local path to sys.path
sys.path.append(os.getcwd())
sys.path.append(r"d:\Triune\Stack Space - Documents\Code\DocFlow")

import cleaner

def test_normalization():
    print("--- Starting Normalization Verification ---")

    # input: Messy markdown
    # 1. Asterisk bullets
    # 2. 4 newlines
    # 3. Header without preceding blank line
    messy_text = """# Title
* Item 1
* Item 2



# Section 2
Some text.
<!-- role:artifact -->
<!-- /role -->
Final line."""

    print("RAW INPUT:")
    print(repr(messy_text))

    normalized = cleaner.normalize_markdown(messy_text)

    print("\nNORMALIZED OUTPUT:")
    print(repr(normalized))

    # Assertions
    if "- Item 1" in normalized and "* Item 1" not in normalized:
        print("✅ Bullet points normalized to hyphen.")
    else:
        print("❌ Bullet points failed.")

    if "\n\n\n" not in normalized:
        print("✅ Excess newlines removed.")
    else:
        print("❌ Excess newlines remain.")

    if "\n\n# Section 2" in normalized:
        print("✅ Header spacing correct.")
    else:
        print("❌ Header spacing failed.")
        
    if "<!-- role:artifact -->" not in normalized:
        print("✅ Empty artifact tags removed.")
    else:
        print("❌ Empty artifact tags remain.")

if __name__ == "__main__":
    test_normalization()
