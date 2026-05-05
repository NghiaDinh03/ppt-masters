FROM python:3.12-slim

# Install system dependencies for CairoSVG, Pandoc, and general tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    pandoc \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Optional: Install Node.js for WeChat fallback
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for Docker layer caching
COPY requirements.txt .
COPY skills/ppt-master/requirements.txt skills/ppt-master/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Create directories for projects and exports
RUN mkdir -p projects exports

# Default command: show help
CMD ["python3", "skills/ppt-master/scripts/project_manager.py", "--help"]
