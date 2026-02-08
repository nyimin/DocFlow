import fitz
print(f"Fitz version: {fitz.__version__}")
try:
    doc = fitz.open() 
    page = doc.new_page()
    # Draw a simple table
    page.draw_rect(fitz.Rect(50, 50, 200, 200))
    page.insert_text((60, 70), "Col1")
    page.insert_text((110, 70), "Col2")
    page.draw_line((50, 80), (200, 80))
    
    print("TEST: find_tables...")
    tabs = page.find_tables()
    print(f"Found {len(tabs.tables)} tables.")
    if tabs.tables:
        print("Table MD:")
        print(tabs[0].to_markdown())
    print("SUCCESS: find_tables works.")
    
except Exception as e:
    print(f"FAILED: {repr(e)}")
