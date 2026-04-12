FROM python:3.10-slim

# Create a non-root user required by Hugging Face Spaces
RUN useradd -m -u 1000 user

# Install essential system dependencies for OpenCV and MediaPipe
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the backend requirements first for better caching
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy all the project files (frontend is filtered by .dockerignore)
COPY . .

# Fix permissions so reports can be generated
RUN chown -R user:user /app
RUN mkdir -p /app/backend/session_reports && chmod -R 777 /app/backend/session_reports

# Switch to the non-root user
USER user

# Hugging Face exposes port 7860
EXPOSE 7860

# Start the FastAPI server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
