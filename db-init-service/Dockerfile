FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy etl requirements and install Python dependencies
COPY etl/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the etl code
COPY etl ./etl

# Copy the application code
COPY . .

# Set PYTHONPATH so etl imports work
ENV PYTHONPATH=/app

# Create startup script
RUN echo '#!/bin/bash\n\
    echo "🚀 Starting Database Initialization Service..."\n\
    echo "📊 This service will initialize database schema without inserting data"\n\
    \n\
    # Wait for database to be ready\n\
    echo "🔄 Waiting for database to be ready..."\n\
    while ! pg_isready -h db -p 5432 -U postgres > /dev/null 2>&1; do\n\
    echo "⏳ Database not ready yet, waiting..."\n\
    sleep 2\n\
    done\n\
    echo "✅ Database is ready!"\n\
    \n\
    # Run the initialization script\n\
    echo "🔄 Running database initialization..."\n\
    python db-init-service/main.py\n\
    echo "✅ Database initialization completed"\n\
    \n\
    echo "📋 Service completed successfully. Exiting..."\n\
    exit 0' > /app/start.sh

RUN chmod +x /app/start.sh

# Set the default command
CMD ["/app/start.sh"] 