import os
import traceback
from PIL import Image

# GMFT Imports
try:
    from gmft.pdf_bindings import PyPDFium2Document
    from gmft.auto import AutoTableDetector, AutoTableFormatter, TATRFormatConfig
    print("GMFT imported successfully.")
except ImportError:
    print("GMFT not found. Table extraction will be disabled.")
    PyPDFium2Document = None

# RapidOCR Imports
try:
    from rapidocr_onnxruntime import RapidOCR
    print("RapidOCR imported successfully.")
except ImportError:
    print("RapidOCR not found. Scan mode disabled.")
    RapidOCR = None

# ... (skip lines) ...

# Initialize GMFT (Lightweight)
detector = None
formatter = None
if PyPDFium2Document:
    detector = AutoTableDetector()
    formatter = AutoTableFormatter()

# Initialize RapidOCR
ocr_engine = None
if RapidOCR:
    # default_model=True downloads models to ~/.rapidocr/ by default if not present
    try:
        ocr_engine = RapidOCR() 
    except Exception as e:
        print(f"Error initializing RapidOCR: {e}")

# ... (skip lines) ...

def extract_with_gmft(pdf_path):
    """
    Use GMFT to extract tables from digital PDFs.
    Returns: Markdown string of tables + text references.
    """
    if not detector:
        return "Error: GMFT not initialized."
        
    doc = PyPDFium2Document(pdf_path)
    output_md = ""
    
    # Config for stricter row detection
    custom_config = TATRFormatConfig(
        formatter_base_threshold=0.7, # Default 0.3. Strictness to avoid extra rows.
        remove_null_rows=True
    )
    
    try:
        for page_num, page in enumerate(doc):
            tables = detector.extract(page)
            if tables:
                output_md += f"\n## Page {page_num + 1} Tables\n"
                for table in tables:
                    # Format table to markdown (GFM)
                    try:
                        ft = formatter.extract(table, config_overrides=custom_config)
                        df = ft.df()
                        md_table = df.to_markdown()
                        output_md += md_table + "\n\n"
                    except Exception as e:
                        output_md += f"[Error formatting table: {e}]\n"
            else:
                output_md += f"\n[Page {page_num + 1}: No tables detected]\n"
    except Exception as e:
         output_md += f"\nError during GMFT extraction: {e}\n"
    finally:
        doc.close()
        
    return output_md

# ... (previous imports)
from gmft.pdf_bindings.base import BasePage
from gmft.base import Rect
import numpy as np

# ... (detector/formatter setup)

class RapidOCRPage(BasePage):
    """
    Adapter to make an Image + RapidOCR result look like a PDF page to GMFT.
    """
    def __init__(self, image, ocr_result, page_num=0):
        self._image = image
        self.width = image.width
        self.height = image.height
        self._ocr_result = ocr_result
        self.page_number = page_num
        
    def get_positions_and_text(self):
        # Yields (x0, y0, x1, y1, "string")
        if not self._ocr_result:
            return
            
        for line in self._ocr_result:
            box, text, score = line
            # RapidOCR box: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            x0, y0, x1, y1 = float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))
            yield (x0, y0, x1, y1, text)
            
    def get_image(self, dpi=None, rect=None):
        # We process in native pixels, so we ignore DPI scaling requests mostly
        # or assume 72 DPI if forced? GMFT uses 72 DPI as base.
        # But here our "PDF coordinates" ARE pixels.
        if rect:
            # rect.bbox is (x0, y0, x1, y1)
            return self._image.crop(rect.bbox)
        return self._image
        
    def get_filename(self):
        return f"scan_page_{self.page_number}.png"
        
    def close(self):
        pass

def extract_with_rapidocr(input_path):
    """
    Use RapidOCR + GMFT to extract text and tables from images/scans.
    Returns: Markdown string.
    """
    if not ocr_engine:
        return "Error: RapidOCR not initialized."
        
    output_md = ""
    
    # Handle PDF input by converting to images first
    images = []
    if input_path.lower().endswith(".pdf"):
        try:
            import fitz
            doc = fitz.open(input_path)
            for page in doc:
                pix = page.get_pixmap(dpi=150) # Moderate DPI for speed/accuracy balance
                img_data = pix.tobytes("png")
                # Convert bytes to PIL Image
                import io
                img = Image.open(io.BytesIO(img_data)).convert("RGB")
                images.append(img)
            doc.close()
        except ImportError:
             return "Error: PyMuPDF (fitz) not found. Cannot process PDF for OCR."
    else:
        # It's an image file path (str)
        try:
            images = [Image.open(input_path).convert("RGB")]
        except Exception as e:
            return f"Error reading image file: {e}"

    # Process each image
    for i, image in enumerate(images):
        output_md += f"\n## Page {i + 1}\n\n"
        try:
            # 1. Run RapidOCR
            # RapidOCR expects an array or path. We pass the numpy array of the image.
            img_np = np.array(image)
            result, _ = ocr_engine(img_np)
            
            if not result:
                output_md += "[No text found]\n"
                continue
                
            # 2. Create Adapter Page
            page_wrapper = RapidOCRPage(image, result, page_num=i)
            
            # 3. Try to detect tables with GMFT
            tables = []
            if detector:
                try:
                    tables = detector.extract(page_wrapper)
                except Exception as e:
                    print(f"GMFT Scan Detection failed: {e}")
            
            # 4. Format Output - Interleaved
            # We will collect "elements" (either text line or table) with their Y-position
            elements = []
            
            table_bboxes = [t.rect.bbox for t in tables] # (x0, y0, x1, y1)
            
            # Helper: Check if box is inside any table
            def is_in_table(box):
                bx0, by0, bx1, by1 = box
                b_center_x, b_center_y = (bx0+bx1)/2, (by0+by1)/2
                for (tx0, ty0, tx1, ty1) in table_bboxes:
                    if tx0 <= b_center_x <= tx1 and ty0 <= b_center_y <= ty1:
                        return True
                return False

            # Collect non-table text
            for line in result:
                # box, text, score
                box = line[0]
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                l_box = (min(xs), min(ys), max(xs), max(ys))
                
                if not is_in_table(l_box):
                    # Store as (y0, type="text", content)
                    elements.append({
                        "y": l_box[1], 
                        "type": "text", 
                        "content": line[1]
                    })
            
            # Collect tables
            # Custom config for scans
            scan_config = TATRFormatConfig(formatter_base_threshold=0.7)
            
            if tables and formatter:
                for table in tables:
                    try:
                        ft = formatter.extract(table, config_overrides=scan_config)
                        df = ft.df()
                        md_table = df.to_markdown()
                        
                        # Store as (y0, type="table", content)
                        # table.rect.bbox is (x0, y0, x1, y1)
                        if md_table:
                            elements.append({
                                "y": table.rect.bbox[1],
                                "type": "table",
                                "content": md_table
                            })
                    except Exception as e:
                         elements.append({
                            "y": table.rect.bbox[1],
                            "type": "text",
                            "content": f"[Error formatting detected table: {e}]"
                        })

            # Sort all elements by Y position
            elements.sort(key=lambda x: x["y"])
            
            # Render logic: slightly smarter newline handling
            for elem in elements:
                if elem["type"] == "text":
                    output_md += elem["content"] + "\n"
                elif elem["type"] == "table":
                    output_md += "\n" + elem["content"] + "\n\n"

        except Exception as e:
            output_md += f"[Error during OCR/Processing: {e}]\n"
            traceback.print_exc()

    return output_md
