import fitz
print(f"Fitz version: {fitz.__version__}")
try:
    doc = fitz.open() 
    page = doc.new_page()
    page.insert_text((50, 50), "Hello World", fontsize=11)
    
    print("TEST: dict output...")
    d = page.get_text("dict")
    print("SUCCESS: dict output works.")
    
    print("TEST: markdown output...")
    md = page.get_text("markdown")
    print("SUCCESS: markdown output works.")
    
except Exception as e:
    print(f"FAILED: {repr(e)}")
