FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API code
COPY api/ .

# Expose port
EXPOSE 8000

# Run the API
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 