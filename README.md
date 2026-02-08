# Walkthrough: SmolDocling on Windows (Docker & CLI)

I have created a lightweight application to run the **SmolDocling-256M** model on Windows to convert PDFs and images to Markdown. You can run it either directly via Python or as a Docker container with a web UI.

## Option 1: Docker (Recommended for UI)

Build and run the application in a container. This ensures all dependencies are isolated.

1.  **Build the Image**:

    ```bash
    docker build -t smol-docling .
    ```

2.  **Run the Container**:

    ```bash
    docker run -p 7860:7860 smol-docling
    ```

    _(If you have a GPU, add `--gpus all` to the run command for faster processing)_

3.  **Open the UI**:
    Go to `http://localhost:7860` in your browser.

---

## Option 2: Python CLI (Direct Usage)

Run the script directly in your terminal.

**Prerequisites**:

```bash
pip install -r requirements.txt
```

**Usage**:

```bash
# Process a PDF
python smoldocling.py my_document.pdf -o output.md

# Process an Image
python smoldocling.py scanned_page.jpg -o output.md
```

## Key Features

- **Lightweight**: Uses `slim` python image and avoids full Docling suite.
- **Scalable**: Handles 100+ page PDFs sequentially.
- **Cross-Platform**: Docker works on Windows, Mac, and Linux.
