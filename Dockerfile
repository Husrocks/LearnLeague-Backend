FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user for Hugging Face Spaces (best practice)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Change working directory to user home
WORKDIR $HOME/app

# Copy the rest of the application code with appropriate permissions
COPY --chown=user src/ ./src/
COPY --chown=user app.py index.py ./

# Hugging Face Spaces run apps on port 7860
EXPOSE 7860

# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "7860", "--proxy-headers"]
