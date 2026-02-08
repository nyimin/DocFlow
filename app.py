
import gradio as gr
import shutil
import tempfile
import os
import smoldocling
import torch

# Ensure CUDA is used if available
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

def process_upload(file, progress=gr.Progress()):
    if file is None:
        return None, None, "No file uploaded."
    
    input_path = file.name
    print(f"Processing input: {input_path}")
    
    try:
        progress(0, desc="Starting conversion...")
        
        # Callback wrapper for Gradio Progress
        def update_progress(p, desc):
            progress(p, desc=desc)

        markdown_text = smoldocling.process_document(
            input_path, 
            output_path=None, 
            device=DEVICE,
            progress_callback=update_progress
        )
        
        if markdown_text is None:
            return None, None, "Failed to process document."
            
        progress(1.0, desc="Structuring document...")
            
        # Create a temporary file for download
        temp_dir = tempfile.mkdtemp()
        output_filename = os.path.splitext(os.path.basename(input_path))[0] + ".md"
        output_path = os.path.join(temp_dir, output_filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
            
        return markdown_text, output_path, None # None = No error
        
    except Exception as e:
        return None, None, f"Error: {str(e)}"

# Minimalist Custom CSS
custom_css = """
body { background-color: #f8f9fa; }
.container { max-width: 800px; margin: auto; padding-top: 2rem; }
.output-markdown { border: 1px solid #e0e0e0; padding: 1rem; border-radius: 8px; background: white; }
footer { visibility: hidden; }
"""

# Create Gradio Interface with Monochrome Theme
with gr.Blocks(theme=gr.themes.Monochrome(), css=custom_css, title="SmolDocling") as demo:
    
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
            process_btn = gr.Button("Convert", variant="primary", scale=1)
        
        error_box = gr.Markdown(visible=True) # To show errors
        
        with gr.Tabs():
            with gr.TabItem("Preview"):
                output_md_view = gr.Markdown(elem_classes="output-markdown")
            
            with gr.TabItem("Raw Code"):
                output_raw_text = gr.TextArea(show_copy_button=True, label="Markdown Source")

        download_btn = gr.File(label="Download Markdown", interactive=False)

    # Event Logic
    process_btn.click(
        fn=process_upload,
        inputs=[file_input],
        outputs=[output_md_view, download_btn, error_box]
    ).success(
        fn=lambda x: x[0], # Just to populate raw text area from the first output
        inputs=[output_md_view],  # Note: logic might need adjusting depending on gradio version, simplified here
        outputs=[output_raw_text]
    )
    
    # Sync visual markdown to raw text area directly
    process_btn.click(
        fn=process_upload, 
        inputs=[file_input], 
        outputs=[output_raw_text, download_btn, error_box]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
