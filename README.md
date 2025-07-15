# Heart Rate Data Pipeline with TimescaleDB

A production-ready ETL pipeline for ingesting Fitbit heart rate data using **TimescaleDB**, Docker, and Python. Features modular ETL architecture with delta processing, multi-user support, and reproducible data seeding. Includes a FastAPI backend and React frontend for data visualization.


# Dynamic query range support
<img width="1547" height="899" alt="image" src="https://github.com/user-attachments/assets/91859beb-5297-4339-a627-a04d2c8316ff" />

<img width="1547" height="899" alt="image" src="https://github.com/user-attachments/assets/7344b1ce-b26d-4925-b8b2-13b69a4984c3" />

<img width="1547" height="899" alt="image" src="https://github.com/user-attachments/assets/ddffa823-41cd-414f-9f22-0ea738b31f1e" />

<img width="1547" height="899" alt="image" src="https://github.com/user-attachments/assets/6314e1ab-e927-46bc-9c92-dd8a1d930056" />


# Detailed Monitoring
<img width="1381" height="828" alt="image" src="https://github.com/user-attachments/assets/bf15481f-2a94-4818-afdb-77b2e5b1dd8b" />
<img width="1381" height="828" alt="image" src="https://github.com/user-attachments/assets/8af50b2a-810f-4617-8945-21b97348a0de" />

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  ETL Pipeline   │───▶│   TimescaleDB   │───▶│   FastAPI +     │
│   (Simulated)   │    │   (Extract/     │    │   (Hypertable)  │    │   React App     │
└─────────────────┘    │    Transform/   │    └─────────────────┘    └─────────────────┘
                       │     Load)       │             
                       |─────────────────|
                                │
                                ▼
                       ┌─────────────────┐
                       │   Monitoring    │
                       │  (Prometheus/   │
                       │   Grafana/      │
                       │   cAdvisor)     │
                       └─────────────────┘
```

## 📁 Project Structure

```
Snyder/
├── api/                          # FastAPI backend service
│   ├── controllers.py            # API endpoint handlers
│   ├── main.py                   # FastAPI application
│   ├── services.py               # Business logic
│   ├── requirements.txt          # Python dependencies
│   └── Dockerfile               # API service container
│
├── client/                       # React frontend application
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── DateRangePicker.tsx
│   │   │   ├── HeartRateDashboard.tsx
│   │   │   └── TimeSeriesChart.tsx
│   │   ├── services/            # API client services
│   │   │   └── api.ts
│   │   ├── utils/               # Utility functions
│   │   │   └── dashboardUtils.ts
│   │   ├── App.tsx             # Main application component
│   │   └── constants.ts         # Application constants
│   ├── package.json             # Node.js dependencies
│   └── Dockerfile              # Client service container
│
├── etl/                         # Shared ETL pipeline code
│   ├── extractors/              # Data extraction modules
│   │   ├── base_extractor.py
│   │   ├── heart_rate_extractor.py
│   │   └── heart_rate_summary_extractor.py
│   ├── transformers/            # Data transformation modules
│   │   ├── base_transformer.py
│   │   ├── heart_rate_transformer.py
│   │   └── heart_rate_summary_transformer.py
│   ├── loaders/                 # Data loading modules
│   │   ├── base_loader.py
│   │   ├── heart_rate_loader.py
│   │   └── heart_rate_summary_loader.py
│   ├── utils/                   # Utility modules
│   │   ├── fitbit_api.py        # Fitbit API simulation
│   │   └── logger.py            # Logging configuration
│   ├── pipeline.py              # Main ETL pipeline orchestration
│   └── requirements.txt         # ETL dependencies
│
├── ingestion-service/            # Data ingestion service
│   ├── config/
│   │   └── settings.py          # Configuration management
│   ├── main.py                  # Ingestion service entry point
│   ├── requirements.txt          # Service dependencies
│   ├── Dockerfile              # Ingestion service container
│   └── README.md               # Service documentation
│
├── db-init-service/             # Database initialization service
│   ├── main.py                  # Schema creation and setup
│   ├── requirements.txt          # Dependencies
│   └── Dockerfile              # Init service container
│
├── monitoring/                  # Monitoring stack configuration
│   ├── prometheus/
│   │   ├── prometheus.yml       # Prometheus configuration
│   │   └── rules.yml           # Alerting rules
│   ├── grafana/
│   │   └── provisioning/
│   │       ├── dashboards/      # Grafana dashboard definitions
│   │       │   ├── api-performance.json
│   │       │   ├── heart-rate-pipeline-fixed.json
│   │       │   └── dashboard.yml
│   │       └── datasources/     # Data source configurations
│   │           └── prometheus.yml
│   ├── alertmanager/
│   │   └── alertmanager.yml     # Alert manager configuration
│   └── README.md               # Monitoring documentation
│
├── data/                        # Persistent data storage
│   └── postgresql/             # TimescaleDB data files
│
├── docker-compose.yml           # Multi-service orchestration
├── README.md                   # This file
├── README_TASK2.md             # Task-specific documentation
├── README_TASK3.md
├── README_TASK4.md
└── README_TASK5.md
```

## 🎯 Software Design Decisions

### **Why TimescaleDB?**

**1. PostgreSQL Compatibility**
- Full SQL support with time-series optimizations
- Existing PostgreSQL knowledge transferable
- Rich ecosystem of tools and libraries

**2. Open Source Advantage**
- No licensing costs for production deployment
- Community-driven development and support
- Transparent codebase and security

**3. Time-Series Optimization**
- **Hypertables**: Automatic partitioning for time-series data
- **Compression**: Built-in columnar compression for storage efficiency
- **Continuous Aggregates**: Pre-computed aggregations for fast queries
- **Time Bucketing**: Native time-based grouping functions

### **Architecture Benefits**

#### **Modular ETL Design**
```python
# Key-based component mapping for extensibility
extractors = {
    'heart_rate': HeartRateExtractor(),
    'heart_rate_summary': HeartRateSummaryExtractor()
}

transformers = {
    'heart_rate': HeartRateTransformer(),
    'heart_rate_summary': HeartRateSummaryTransformer()
}

loaders = {
    'heart_rate': HeartRateLoader(),
    'heart_rate_summary': HeartRateSummaryLoader()
}
```
#### **Delta Processing**
- **Incremental Loading**: Only processes new records using `MAX(timestamp)`
- **Idempotent Operations**: Safe to run multiple times with UPSERT
- **Automatic Filtering**: Filters already processed records
- **Continuous Aggregate Refresh**: Auto-refreshes aggregates after data ingestion

## 🚀 Quick Start

### 1. Start All Services
```bash
# Start all services including monitoring stack
docker compose up -d

# Or start services in stages:
# Start database and initialization
docker compose up -d timescaledb db-init-service

# Start ingestion services for both users
docker compose up -d ingestion-user1 ingestion-user2

# Start API and client services
docker compose up -d api-service client-service

# Start monitoring stack
docker compose up -d prometheus grafana alertmanager cadvisor node-exporter postgres-exporter
```

### 2. Access the Application
- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Base URL**: http://localhost:8000
- **Grafana Monitoring**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **cAdvisor**: http://localhost:8080

### 3. Monitor Services
```bash
# Check service status
docker compose ps

# View logs for specific service
docker compose logs api-service
docker compose logs client-service
docker compose logs ingestion-user1
```

### 4. Access Data
```bash
# Connect to TimescaleDB
docker exec -it timescaledb psql -U postgres -d fitbit-hr

# Query data by user
SELECT user_id, COUNT(*) FROM activities_heart_intraday GROUP BY user_id;
```

## 📊 Data Schema

### TimescaleDB Tables

#### `activities_heart_intraday` (Intraday Heart Rate)
```sql
CREATE TABLE activities_heart_intraday (
    timestamp TIMESTAMPTZ NOT NULL,
    value NUMERIC(5,2) NOT NULL,
    user_id TEXT NOT NULL,
    PRIMARY KEY (timestamp, user_id)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('activities_heart_intraday', 'timestamp', if_not_exists => TRUE);

-- Create unique index for UPSERT operations
CREATE UNIQUE INDEX IF NOT EXISTS idx_activities_heart_intraday_timestamp_user_id 
ON activities_heart_intraday (timestamp, user_id);
```

#### `activities_heart_summary` (Daily Summaries)
```sql
CREATE TABLE activities_heart_summary (
    timestamp TIMESTAMPTZ NOT NULL,
    resting_heart_rate INTEGER,
    heart_rate_zones JSONB,
    custom_heart_rate_zones JSONB,
    user_id TEXT NOT NULL,
    PRIMARY KEY (timestamp, user_id)
);
```

### Continuous Aggregate Views

The system automatically creates three continuous aggregate views for optimized time-series queries:

#### `activities_heart_intraday_1m` (1-Minute Aggregates)
```sql
CREATE MATERIALIZED VIEW activities_heart_intraday_1m
WITH (timescaledb.continuous) AS
SELECT
  user_id,
  time_bucket('1 minute', timestamp) as minute,
  ROUND(MIN(value)::numeric, 2) AS min_heart_rate,
  ROUND(MAX(value)::numeric, 2) AS max_heart_rate,
  ROUND(AVG(value)::numeric, 2) AS avg_heart_rate,
  COUNT(*) AS record_count
FROM activities_heart_intraday
GROUP BY user_id, minute;
```

#### `activities_heart_intraday_1h` (1-Hour Aggregates)
```sql
CREATE MATERIALIZED VIEW activities_heart_intraday_1h
WITH (timescaledb.continuous) AS
SELECT
  user_id,
  time_bucket('1 hour', timestamp) as hour,
  ROUND(MIN(value)::numeric, 2) AS min_heart_rate,
  ROUND(MAX(value)::numeric, 2) AS max_heart_rate,
  ROUND(AVG(value)::numeric, 2) AS avg_heart_rate,
  COUNT(*) AS record_count
FROM activities_heart_intraday
GROUP BY user_id, hour;
```

#### `activities_heart_intraday_1d` (1-Day Aggregates)
```sql
CREATE MATERIALIZED VIEW activities_heart_intraday_1d
WITH (timescaledb.continuous) AS
SELECT
  user_id,
  time_bucket('1 day', timestamp) as day,
  ROUND(MIN(value)::numeric, 2) AS min_heart_rate,
  ROUND(MAX(value)::numeric, 2) AS max_heart_rate,
  ROUND(AVG(value)::numeric, 2) AS avg_heart_rate,
  COUNT(*) AS record_count
FROM activities_heart_intraday
GROUP BY user_id, day;
```

### Schema Features

- **Hypertables**: Both tables are converted to TimescaleDB hypertables for automatic partitioning
- **Continuous Aggregates**: Pre-computed aggregations at 1-minute, 1-hour, and 1-day intervals
- **Auto-Refresh**: Continuous aggregates are automatically refreshed after data ingestion
- **UPSERT Support**: Unique indexes enable efficient upsert operations
- **Multi-User**: All tables support multiple users with composite primary keys

## 🔧 Configuration

### Environment Variables
```env
# Database Configuration
DB_HOST=timescaledb
DB_PORT=5432
DB_NAME=fitbit-hr
DB_USER=postgres
DB_PASSWORD=password

# User Configuration
USER_ID=user1          # or user2
DATA_SEED=23          # or 37 for user2

# ETL Configuration
START_DATE=2025-06-01  # Optional: custom start date
END_DATE=2025-06-30    # Optional: custom end date
BATCH_SIZE=10000
UPSERT_MODE=true
DELTA_MODE=true
```

### Service Configuration

#### **Database Service (`timescaledb`)**
- **Image**: `timescale/timescaledb:latest-pg14`
- **Port**: 5432
- **Persistence**: `./data/postgresql`
- **Features**: TimescaleDB extensions, continuous aggregates

#### **Database Initialization (`db-init-service`)**
- **Purpose**: Creates tables, hypertables, and continuous aggregates
- **Dependencies**: Runs after database startup
- **Restart**: No (runs once and exits)

#### **Ingestion Services**
- **`ingestion-user1`**: Processes user1 data (seed: 23)
- **`ingestion-user2`**: Processes user2 data (seed: 37)
- **Schedule**: Daily at 2:00 AM via cron
- **Features**: Delta processing, continuous aggregate refresh
- **Dependencies**: Database and init_db

#### **API Service (`api-service`)**
- **Framework**: FastAPI with CORS support
- **Port**: 8000
- **Features**: 
  - Time-series data queries
  - User filtering
  - Metric selection
  - Multi-user endpoints
  - Prometheus metrics
- **Dependencies**: Database

#### **Client Service (`client-service`)**
- **Framework**: React with TypeScript
- **Port**: 3000
- **Features**: 
  - Interactive dashboard
  - Real-time data visualization
  - Dynamic query ranges
  - Multi-user data comparison
- **Dependencies**: API service

#### **Monitoring Stack**
- **Prometheus**: Metrics collection and storage
- **Grafana**: Dashboard visualization (admin/admin)
- **cAdvisor**: Container metrics
- **Node Exporter**: Host system metrics
- **Postgres Exporter**: Database metrics
- **Alertmanager**: Alert management

## 🔍 Data Access

### **Web Interface**
- **Dashboard**: http://localhost:3000
  - Interactive charts with user and metric selection
  - Auto-fetching data on parameter changes
  - Real-time visualization
  - Multi-user data comparison

### **API Endpoints**
```bash
# Get API information
curl http://localhost:8000/

# Get time-series data for single user
curl "http://localhost:8000/timeseries?start_date=2025-06-29&end_date=2025-07-06&user_id=user1&metric=activities_heart_intraday"

# Get multi-user time-series data
curl "http://localhost:8000/multi-user/timeseries?start_date=2025-06-29&end_date=2025-07-06&metric=activities_heart_intraday"

# Get API health status
curl http://localhost:8000/health
```

### **Direct Database Access**
```bash
# Connect to TimescaleDB
docker exec -it timescaledb psql -U postgres -d fitbit-hr
```

## 📈 Monitoring & Observability

### **Grafana Dashboards**
- **API Performance**: Monitor API response times and throughput
- **Heart Rate Pipeline**: Track ETL pipeline performance and data freshness
- **Container Metrics**: Monitor resource usage across all services
- **Database Performance**: Track TimescaleDB query performance

### **Prometheus Metrics**
- **API Metrics**: Request counts, response times, error rates
- **Container Metrics**: CPU, memory, network usage
- **Database Metrics**: Connection counts, query performance
- **System Metrics**: Host resource utilization

### **Alerting**
- **Service Health**: Alerts for service failures
- **Performance**: Alerts for high response times
- **Resource Usage**: Alerts for high CPU/memory usage
- **Data Freshness**: Alerts for stale data

## 🔄 Continuous Integration

### **Automated Data Refresh**
- **Daily Ingestion**: Scheduled data processing for both users
- **Continuous Aggregates**: Auto-refresh after data ingestion
- **Delta Processing**: Only processes new data for efficiency
- **Idempotent Operations**: Safe to run multiple times

## 🛠️ Development

### **Local Development**
```bash
# Start development environment
docker compose up -d

# View logs
docker compose logs -f

# Restart specific service
docker compose restart api-service

# Rebuild and restart
docker compose up -d --build
```

## 📚 Documentation
- **README.md**: Project's README.md
- **README_TASK1.md**: General answer for task 0 questions
- **README_TASK1.md**: Ingestion Service
- **README_TASK2.md**: ETL pipeline implementation details
- **README_TASK3.md**: API and frontend development
- **README_TASK4.md**: Multi-user support implementation
- **README_TASK5.md**: Monitoring stack setup and configuration

