import os
import traceback
from PIL import Image

# GMFT Imports
try:
    from gmft.pdf_bindings import PyPDFium2Document
    from gmft.auto import AutoTableDetector, AutoTableFormatter
    print("GMFT imported successfully.")
except ImportError:
    print("GMFT not found. Table extraction will be disabled.")
    PyPDFium2Document = None

# Surya Imports (Lazy loading handled in function, but class imports here)
SuryaRecognitionPredictor = None
SuryaDetectionPredictor = None
SuryaFoundationPredictor = None

try:
    from surya.recognition import RecognitionPredictor
    from surya.detection import DetectionPredictor
    from surya.foundation import FoundationPredictor
    SuryaRecognitionPredictor = RecognitionPredictor
    SuryaDetectionPredictor = DetectionPredictor
    SuryaFoundationPredictor = FoundationPredictor
    print("Surya OCR imported successfully.")
except ImportError:
    print("Surya OCR not found or incompatible. Scan mode disabled.")

# Initialize GMFT (Lightweight)
detector = None
formatter = None
if PyPDFium2Document:
    detector = AutoTableDetector()
    formatter = AutoTableFormatter()

# Global Surya Instances
rec_predictor = None
det_predictor = None
foundation_predictor = None

def load_surya():
    global rec_predictor, det_predictor, foundation_predictor
    if rec_predictor is None and SuryaRecognitionPredictor:
        print("Loading Surya models... (this may take a moment)")
        try:
            foundation_predictor = SuryaFoundationPredictor()
            det_predictor = SuryaDetectionPredictor()
            rec_predictor = SuryaRecognitionPredictor(foundation_predictor)
        except Exception as e:
            print(f"Failed to load Surya models: {e}")
            traceback.print_exc()

def extract_with_gmft(pdf_path):
    """
    Use GMFT to extract tables from digital PDFs.
    Returns: Markdown string of tables + text references.
    """
    if not detector:
        return "Error: GMFT not initialized."
        
    doc = PyPDFium2Document(pdf_path)
    output_md = ""
    
    try:
        for page_num, page in enumerate(doc):
            tables = detector.extract(page)
            if tables:
                output_md += f"\n## Page {page_num + 1} Tables\n"
                for table in tables:
                    # Format table to markdown (GFM)
                    try:
                        md_table = formatter.format(table, fmt="markdown")
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

def extract_with_surya(image_path_or_list):
    """
    Use Surya OCR to extract text/tables from images/scans.
    """
    if not SuryaRecognitionPredictor:
        return "Error: Surya OCR library not found or incompatible."
        
    load_surya()
    if not rec_predictor:
        return "Error: Failed to load Surya models."

    # Ensure input is list of images
    images = []
    if isinstance(image_path_or_list, list):
        images = image_path_or_list
    else:
        images = [Image.open(image_path_or_list).convert("RGB")]
        
    # Run Prediction
    # Note: Surya 0.17+ API uses rec_predictor(images, ...)
    try:
        # Default languages ["en"] for now, can be configured
        langs = ["en"] 
        # API might require task_names or other params, but defaults usually work for simple OCR
        # Based on ocr_text.py: rec_predictor(images, det_predictor=det_predictor)
        
        predictions = rec_predictor(images, det_predictor=det_predictor, math_mode=False)
        
        markdown_output = ""
        for i, pred in enumerate(predictions):
            markdown_output += f"\n## Page {i+1}\n"
            for line in pred.text_lines:
                markdown_output += line.text + "\n"
        
        return markdown_output
        
    except Exception as e:
        traceback.print_exc()
        return f"Error during Surya extraction: {e}"
