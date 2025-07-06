FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Create log directory
RUN mkdir -p /var/log

# Create cron job file with environment variables - Run once per day at 2:00 AM
RUN echo "DB_HOST=timescaledb\nDB_PORT=5432\nDB_NAME=fitbit-hr\nDB_USER=postgres\nDB_PASSWORD=password\n0 2 * * * /usr/local/bin/python /app/main.py" > /etc/cron.d/ingestion-cron
RUN chmod 0644 /etc/cron.d/ingestion-cron

# Add cron job to crontab
RUN crontab /etc/cron.d/ingestion-cron

# No need to create log file - we'll use Docker logs

# Create startup script
RUN echo '#!/bin/bash\n\
    echo "🚀 Starting Ingestion Service..."\n\
    echo "📅 Cron job scheduled: Once per day at 2:00 AM"\n\
    echo "📊 Logs: Use 'docker logs ingestion-service' to view"\n\
    \n\
    # Start cron daemon\n\
    service cron start\n\
    echo "✅ Cron daemon started"\n\
    \n\
    # Wait for database to be ready\n\
    echo "🔄 Waiting for database to be ready..."\n\
    while ! pg_isready -h timescaledb -p 5432 -U postgres > /dev/null 2>&1; do\n\
    echo "⏳ Database not ready yet, waiting..."\n\
    sleep 2\n\
    done\n\
    echo "✅ Database is ready!"\n\
    \n\
    # Run the ingestion script once immediately for initial data\n\
    echo "🔄 Running initial ingestion..."\n\
    python /app/main.py\n\
    echo "✅ Initial ingestion completed"\n\
    \n\
    # Show cron jobs\n\
    echo "📋 Current cron jobs:"\n\
    crontab -l\n\
    \n\
    echo "📈 Container is running. Use 'docker logs ingestion-service' to view logs..."\n\
    # Keep container running\n\
    tail -f /dev/null' > /app/start.sh

RUN chmod +x /app/start.sh

# Expose port (if needed for health checks)
EXPOSE 8080

# Set the default command
CMD ["/app/start.sh"] 