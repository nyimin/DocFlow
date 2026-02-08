
import fitz
import os

source_path = r"d:\Triune\Stack Space - Documents\Data\IFC - Utility Scale Solar Handbook.pdf"
dest_path = "sample_test.pdf"

if not os.path.exists(source_path):
    print(f"Error: Source file not found: {source_path}")
    exit(1)

doc = fitz.open(source_path)
print(f"Original Pages: {len(doc)}")

# Create new doc with first 2 pages
new_doc = fitz.open()
new_doc.insert_pdf(doc, from_page=0, to_page=1)
new_doc.save(dest_path)
print(f"Created sample PDF: {dest_path} with {len(new_doc)} pages")
