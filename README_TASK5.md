# Task 5: Monitoring & Alerting System

## Quick Start Guide

### 1. Start All Services
```bash
docker compose up -d
```

### 2. Verify Services Are Running
```bash
docker compose ps
```

### 3. Access Monitoring Interfaces

| Service | URL | Username | Password | Port |
|---------|-----|----------|----------|------|
| **Grafana Dashboard** | http://localhost:3001 | admin | admin | 3001 |
| **Prometheus** | http://localhost:9090 | - | - | 9090 |
| **AlertManager** | http://localhost:9093 | - | - | 9093 |
| **API Service** | http://localhost:8000 | - | - | 8000 |
| **Frontend** | http://localhost:3000 | - | - | 3000 |
| **API Docs** | http://localhost:8000/docs | - | - | 8000 |

### 4. Database Access
```bash
# Connect to TimescaleDB
docker exec -it timescaledb psql -U postgres -d fitbit-hr

# Database credentials:
# Host: localhost
# Port: 5432
# Database: fitbit-hr
# Username: postgres
# Password: password
```

### 5. View Service Logs
```bash
# View logs for specific service
docker compose logs api
docker compose logs client
docker compose logs ingestion_user1
docker compose logs ingestion_user2
docker compose logs grafana
docker compose logs prometheus
```

### 6. Stop All Services
```bash
docker compose down
```

## Service Overview

### Core Services
- **API Service**: FastAPI backend serving heart rate data
- **Frontend**: React dashboard for data visualization
- **Database**: TimescaleDB for time-series data storage
- **Ingestion Services**: ETL pipelines for user1 and user2 data

### Monitoring Services
- **Grafana**: Dashboard visualization and metrics
- **Prometheus**: Metrics collection and storage
- **AlertManager**: Alert routing and notifications
- **Node Exporter**: Host system metrics
- **cAdvisor**: Container metrics
- **PostgreSQL Exporter**: Database metrics

## Environment Variables

### Database Configuration
```env
DB_HOST=db
DB_PORT=5432
DB_NAME=fitbit-hr
DB_USER=postgres
DB_PASSWORD=password
```

### Ingestion Service Configuration
```env
USER_ID=user1  # or user2
DATA_SEED=23   # random seed for data generation
START_DATE=2025-06-15  # start date for data ingestion
END_DATE=2025-07-15    # end date for data ingestion
```

### Grafana Configuration
```env
GF_SECURITY_ADMIN_PASSWORD=admin
```

## Troubleshooting

### Check Service Status
```bash
docker compose ps
```

### Restart Specific Service
```bash
docker compose restart api
docker compose restart client
docker compose restart ingestion_user1
```

### View Real-time Logs
```bash
docker compose logs -f api
```

### Access Container Shell
```bash
docker exec -it api-service /bin/bash
docker exec -it client-service /bin/bash
```

## Data Access

### API Endpoints
```bash
# Get time-series data
curl "http://localhost:8000/timeseries?start_date=2025-06-23&end_date=2025-06-24&user_id=user1"

# Get API information
curl http://localhost:8000/

# Get metrics
curl http://localhost:8000/metrics
```

## Monitoring Dashboards

### Grafana Dashboards Available
- **API Performance**: Monitor API response times and request rates
- **Heart Rate Pipeline**: System health and data processing metrics

## Alerts

The system includes automated alerts for:
- **Service Down**: API, ingestion, or database services unavailable
- **High Resource Usage**: CPU > 80%, Memory > 85%, Disk > 85%
- **Performance Issues**: Response time > 30 seconds

Alerts are sent to: admin@wearipedia.com

## Quick Commands Reference

### Start/Stop Services
```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Restart specific service
docker compose restart <service-name>
```

### Check System Health
```bash
# Check all services status
docker compose ps

# Check specific service logs
docker compose logs <service-name>

# Follow logs in real-time
docker compose logs -f <service-name>
```

### Database Operations
```bash
# Connect to database
docker exec -it timescaledb psql -U postgres -d fitbit-hr

# Check data counts
SELECT COUNT(*) FROM activities_heart_intraday;

# Check continuous aggregates
SELECT * FROM activities_heart_intraday_1h LIMIT 10;
```

### Monitoring Access
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check API health
curl http://localhost:8000/health

# Get API metrics
curl http://localhost:8000/metrics
```

## Common Issues & Solutions

### Services Not Starting
```bash
# Check if ports are in use
lsof -i :3000,3001,8000,9090,9093

# Restart Docker
docker system prune -f
docker compose up -d
```

### No Data in Dashboards
```bash
# Check if metrics are being collected
curl http://localhost:8000/metrics

# Verify Prometheus targets
curl http://localhost:9090/api/v1/targets
```

### Database Connection Issues
```bash
# Check database container
docker compose logs timescaledb

# Restart database
docker compose restart timescaledb
```

## Performance Monitoring

### Key Metrics to Watch
- **API Response Time**: Should be under 1 second
- **Database Connections**: Should be under 20 active connections
- **Container CPU Usage**: Should be under 80%
- **Memory Usage**: Should be under 85%

### Monitoring Commands
```bash
# Check container resource usage
docker stats

# Check system resources
docker exec -it timescaledb psql -U postgres -d fitbit-hr -c "SELECT * FROM pg_stat_activity;"
``` 