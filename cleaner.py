import re
import statistics
from collections import Counter

def merge_hyphenated_words(text):
    """
    Fixes words broken by hyphens at line ends.
    Example: "This is a bro- \n ken sentence." -> "This is a broken sentence."
    """
    # Regex for word ending with hyphen, optional whitespace/newline, starting next word
    # distinct from dashes used as punctuation. Strict: second part must be lowercase.
    pattern = r'([a-zA-Z]+)-\s*\n\s*([a-z]+)'
    return re.sub(pattern, r'\1\2', text)

def detect_and_remove_headers_footers(pages_elements, threshold=0.6):
    """
    Identifies and removes headers and footers that repeat across pages.
    
    Args:
        pages_elements: List of Lists. Each inner list contains elements for a page.
                        Element: {'y': float, 'type': 'text'|'table', 'content': str}
        threshold: Fraction of pages a text must appear in to be considered a header/footer.
                   e.g., 0.6 means if it appears in 60% of pages, it's removed.
    
    Returns:
        Cleaned pages_elements
    """
    if len(pages_elements) < 3:
        return pages_elements

    # Flatten all text elements to analyze frequency
    # We use a simplified key: rounded Y position + content content (stripped)
    # This helps catch "Page 1", "Page 2" if we mask numbers, 
    # but for now let's just look for EXACT repeating headers like "Confidential" or "Chapter X"
    
    # Improved Strategy:
    # 1. Bucketize Y positions (top 10% and bottom 10% of page roughly)
    # 2. Look for exact string matches in these regions
    
    # We don't have page height in elements, so we assume standard flow or check relative Y
    # Let's collect all text lines with their Y positions
    
    candidates = Counter()
    total_pages = len(pages_elements)
    
    for page in pages_elements:
        for elem in page:
            if elem['type'] == 'text':
                clean_text = elem['content'].strip()
                if len(clean_text) > 3: # Ignore tiny artifacts
                    candidates[clean_text] += 1
    
    # Filter for repeaters
    # Note: "Page 1", "Page 2" won't match exactly. 
    # Future improvement: Regex masking for numbers.
    repeaters = {text for text, count in candidates.items() if count / total_pages >= threshold}
    
    cleaned_pages = []
    for page in pages_elements:
        new_page = []
        for elem in page:
            if elem['type'] == 'text':
                clean_text = elem['content'].strip()
                if clean_text in repeaters:
                    continue # Skip header/footer
            new_page.append(elem)
        cleaned_pages.append(new_page)
        
    return cleaned_pages

def defragment_text(text):
    """
    Merges lines that appear to be part of the same paragraph.
    Simple heuristic: If a line doesn't end with [.!?], merge with next.
    """
    lines = text.split('\n')
    merged = []
    current_line = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            if current_line:
                merged.append(current_line)
                current_line = ""
            merged.append("") # Preserve empty lines as paragraph breaks
            continue
            
        if not current_line:
            current_line = line
        else:
            # Check if previous line ended with sentence punctuation
            if current_line.endswith(('.', '?', '!', ':')):
                merged.append(current_line)
                current_line = line
            else:
                # Merge
                current_line += " " + line
    
    if current_line:
        merged.append(current_line)
        
    return '\n'.join(merged)


def normalize_markdown(text: str) -> str:
    """
    Normalize Markdown output to ensure consistent styling and remove artifacts.
    
    Operations:
    1. Standardize line breaks (max 2 consecutive newlines)
    2. Convert asteroid bullets (*) to hyphens (-)
    3. Ensure blank lines before headers
    4. Remove empty semantic tags
    
    Args:
        text (str): Raw markdown text
        
    Returns:
        str: Normalized markdown text
    """
    if not text:
        return ""

    # 1. Standardize line breaks (max 2 newlines)
    # Replace 3 or more newlines with 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 2. Standardize list bullets (convert * start to -)
    # Only matches * at start of line or after whitespace
    text = re.sub(r'^(\s*)\* ', r'\1- ', text, flags=re.MULTILINE)
    
    # 3. Ensure blank lines before headers
    # If a header (#) is preceded by a non-newline char and a single newline, add another newline
    text = re.sub(r'([^\n])\n(#{1,6} )', r'\1\n\n\2', text)
    
    # 4. Remove empty semantic tags (e.g., <!-- role:artifact -->\n<!-- /role -->)
    # This regex looks for tags with only whitespace content
    text = re.sub(r'<!-- role:\w+ -->\s*<!-- /role -->', '', text)
    
    return text.strip()
