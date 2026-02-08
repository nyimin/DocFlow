"""
DocFlow REST API
Provides programmatic access to PDF/Image to Markdown conversion.

Usage:
    python api.py

Endpoints:
    POST /api/convert - Convert a file to markdown
    GET /api/health - Health check
    GET /api/stats - Get usage statistics
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

import app as docflow_app

api = FastAPI(
    title="DocFlow API",
    description="Convert PDFs and images to Markdown via REST API",
    version="1.0.0"
)

# Enable CORS
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "DocFlow API"}

@api.get("/api/stats")
async def get_stats():
    """Get usage statistics."""
    stats = docflow_app.load_stats()
    return stats

@api.post("/api/convert")
async def convert_file(
    file: UploadFile = File(...),
    dpi: int = Form(300),
    ocr_lang: str = Form("en"),
    export_format: str = Form("markdown"),
    page_start: int = Form(None),
    page_end: int = Form(None),
    use_cache: bool = Form(True)
):
    """
    Convert a PDF or image to markdown.
    
    Parameters:
    - file: The PDF or image file to convert
    - dpi: DPI for rendering (150-600, default 300)
    - ocr_lang: OCR language (en, ch_sim, ch_tra, ja, ko, ru)
    - export_format: Output format (markdown, html, txt, docx)
    - page_start: Optional start page for PDFs
    - page_end: Optional end page for PDFs
    - use_cache: Whether to use caching (default True)
    
    Returns:
    - JSON with markdown text, metadata, and statistics
    """
    
    # Validate inputs
    if dpi < 150 or dpi > 600:
        raise HTTPException(status_code=400, detail="DPI must be between 150 and 600")
    
    if ocr_lang not in ["en", "ch_sim", "ch_tra", "ja", "ko", "ru"]:
        raise HTTPException(status_code=400, detail="Invalid OCR language")
    
    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process the file
        markdown_text, method_used = docflow_app.process_single_file(
            temp_path, dpi, ocr_lang, page_start, page_end, use_cache
        )
        
        if not markdown_text:
            raise HTTPException(status_code=500, detail="Failed to extract content from file")
        
        # Get metadata if PDF
        metadata = {}
        if temp_path.lower().endswith(".pdf"):
            metadata_str = docflow_app.get_pdf_metadata(temp_path)
            metadata = {"info": metadata_str}
        
        # Calculate stats
        words, chars = docflow_app.count_stats(markdown_text)
        
        # Convert to requested format
        output_text = markdown_text
        if export_format == "html":
            output_text = docflow_app.markdown_to_html(markdown_text)
        elif export_format == "txt":
            output_text = docflow_app.markdown_to_txt(markdown_text)
        
        return JSONResponse({
            "success": True,
            "filename": file.filename,
            "method": method_used,
            "format": export_format,
            "content": output_text,
            "metadata": metadata,
            "stats": {
                "words": words,
                "characters": chars
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("DocFlow API Server")
    print("=" * 60)
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check: http://localhost:8000/api/health")
    print("=" * 60)
    uvicorn.run(api, host="0.0.0.0", port=8000)
