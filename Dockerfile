FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy backend only
COPY backend/ /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Railway port
EXPOSE 8080

# Start FastAPI with Gunicorn
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app"]
