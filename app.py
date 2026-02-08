
import gradio as gr
import shutil
import tempfile
import os
# import smoldocling (removed)
# import torch (removed)

import fitz # PyMuPDF
import fast_converter
import structure_engine # New table extraction engine
import warnings

# Ensure CUDA is used if available (though we default to CPU for this build)
DEVICE = "cpu"

def process_upload(file, mode, progress=gr.Progress()):
    if file is None:
        return None, None, None, "No file uploaded."
    
    input_path = file.name
    print(f"Processing input: {input_path} (Mode: {mode})")
    
    try:
        progress(0, desc="Analyzing document...")
        
        # --- AUTO DETECTION LOGIC ---
        if mode == "Auto":
            if input_path.lower().endswith(".pdf"):
                try:
                    doc = fitz.open(input_path)
                    # Check first page for text density
                    if len(doc) > 0:
                        text = doc[0].get_text()
                        if len(text.strip()) > 50: # Arbitrary threshold for "digital text"
                            print("Auto-Detect: Found significant text layer. Using FAST mode.")
                            mode = "gmft (Fast Tables)" # Upgrade auto to gmft for better tables
                        else:
                            print("Auto-Detect: Low text density. Using RapidOCR mode.")
                            mode = "RapidOCR (Images/Scans)" # Upgrade auto scan to RapidOCR
                    doc.close()
                except Exception as e:
                    print(f"Auto-detect failed: {e}. Defaulting to OCR.")
                    mode = "RapidOCR (Images/Scans)"
            else:
                # Images always need OCR
                mode = "RapidOCR (Images/Scans)"


        markdown_text = None

        # --- DISPATCHER ---
        if mode == "MarkItDown (Text Only)":
             progress(0.2, desc="Extracting text (MarkItDown)...")
             markdown_text = fast_converter.convert_fast(input_path)
             
        elif mode == "gmft (Fast Tables)":
             progress(0.2, desc="Extracting tables (gmft)...")
             if not input_path.lower().endswith(".pdf"):
                 return None, None, None, "Error: gmft only supports PDFs."
             markdown_text = structure_engine.extract_with_gmft(input_path)

        elif mode == "RapidOCR (Images/Scans)":
             progress(0.2, desc="Scanning text (RapidOCR)...")
             markdown_text = structure_engine.extract_with_rapidocr(input_path)

        else: 
            return None, None, None, "Invalid mode selected."
        
        if markdown_text is None:
            return None, None, None, "Failed to process document."
            
        progress(1.0, desc="Finalizing...")
            
        # Create a temporary file for download
        temp_dir = tempfile.mkdtemp()
        output_filename = os.path.splitext(os.path.basename(input_path))[0] + ".md"
        output_path = os.path.join(temp_dir, output_filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
             f.write(markdown_text)
            
        # Return md twice (for view and raw), then path, then error
        return markdown_text, markdown_text, output_path, None 
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, None, None, f"Error: {str(e)}"

# Minimalist Custom CSS
# Removed hardcoded colors to allow Gradio theme to handle contrast
custom_css = """
.container { max-width: 800px; margin: auto; padding-top: 2rem; }
.output-markdown { padding: 1rem; border-radius: 8px; }
footer { visibility: hidden; }
"""

# Create Gradio Interface with Soft Theme (Better contrast handling)
with gr.Blocks(theme=gr.themes.Soft(), css=custom_css, title="SmolDocling") as demo:
    
    with gr.Column(elem_classes="container"):
        gr.Markdown("# 📄 SmolDocling", elem_id="header")
        gr.Markdown("Lightweight PDF & Image to Markdown Converter")
        
        with gr.Row():
            file_input = gr.File(
                label="Upload Document",
                file_types=[".pdf", ".png", ".jpg", ".jpeg"],
                type="filepath",
                scale=2
            )
            mode_input = gr.Radio(
                ["Auto", "MarkItDown (Text Only)", "gmft (Fast Tables)", "RapidOCR (Images/Scans)"],
                label="Conversion Mode (Default: Auto)",
                value="Auto",
                scale=1
            )
            process_btn = gr.Button("Convert", variant="primary", scale=1)
            
            # Quick Tip
            gr.Markdown("ℹ️ **Tip:** 'gmft' is best for digital tables. 'RapidOCR' is best for scanned documents.")
        
        error_box = gr.Markdown(visible=True) # To show errors
        
        with gr.Tabs():
            with gr.TabItem("Preview"):
                output_md_view = gr.Markdown(elem_classes="output-markdown")
            
            with gr.TabItem("Raw Code"):
                output_raw_text = gr.TextArea(label="Markdown Source")

        download_btn = gr.File(label="Download Markdown", interactive=False)

    # Event Logic - Single handler to update all outputs
    process_btn.click(
        fn=process_upload,
        inputs=[file_input, mode_input],
        outputs=[output_md_view, output_raw_text, download_btn, error_box]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
