FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for SUMO
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    libxerces-c-dev \
    libproj-dev \
    libgdal-dev \
    libfox-1.6-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    && rm -rf /var/lib/apt/lists/*

# Install SUMO from package manager
RUN apt-get update && apt-get install -y sumo sumo-tools && \
    rm -rf /var/lib/apt/lists/*

# Add SUMO to PATH
ENV PATH="/usr/local/share/sumo/bin:${PATH}"
ENV SUMO_HOME="/usr/local/share/sumo"

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
