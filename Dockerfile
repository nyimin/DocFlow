
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
# PyMuPDF usually has wheels, but for safety in slim image we update apt
# Git might be needed if installing from repo, but we use pip.
RUN apt-get update && apt-get install -y \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-Only PyTorch first to avoid downloading CUDA bundles
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and directories
COPY *.py ./
COPY docs/ ./docs/

# Create a non-root user for security (optional but good practice)
RUN useradd -m appuser
USER appuser

# Expose Gradio port
EXPOSE 7860

# Default command runs the UI
CMD ["python", "app.py"]
