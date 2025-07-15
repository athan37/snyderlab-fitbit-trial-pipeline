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
```

## 🎯 Software Design Decisions

### **Why TimescaleDB **

**1. PostgreSQL Compatibility**
**2. Open Source Advantage**
**3. Time-Series Optimization**
- **Hypertables**: Automatic partitioning for time-series data
- **Compression**: Built-in columnar compression for storage efficiency


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

## 🚀 Quick Start

### 1. Start All Services
```bash
# Start database and initialization
docker compose up -d db init_db

# Start ingestion services for both users
docker compose up -d ingestion_user1 ingestion_user2

# Start API and client services
docker compose up -d api client
```

### 2. Access the Application
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 3. Monitor Services
```bash
# Check service status
docker compose ps

# View logs for specific service
docker compose logs api
docker compose logs client
docker compose logs ingestion_user1
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
    value DOUBLE PRECISION NOT NULL,
    user_id TEXT NOT NULL,
    PRIMARY KEY (timestamp, user_id)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('activities_heart_intraday', 'timestamp');
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

## 🔧 Configuration

### Environment Variables
```env
# Database Configuration
DB_HOST=db
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

#### **Database Service (`db`)**
- **Image**: `timescale/timescaledb:latest-pg14`
- **Port**: 5432
- **Persistence**: `./data/postgresql`

#### **Database Initialization (`init_db`)**
- **Purpose**: Creates tables and schema
- **Dependencies**: Runs after database startup
- **Restart**: No (runs once and exits)

#### **Ingestion Services**
- **`ingestion_user1`**: Processes user1 data (seed: 23)
- **`ingestion_user2`**: Processes user2 data (seed: 37)
- **Schedule**: Daily at 2:00 AM via cron
- **Dependencies**: Database and init_db

#### **API Service (`api`)**
- **Framework**: FastAPI with CORS support
- **Port**: 8000
- **Features**: Time-series data queries, user filtering, metric selection
- **Dependencies**: Database

#### **Client Service (`client`)**
- **Framework**: React with TypeScript
- **Port**: 3000
- **Features**: Interactive dashboard, real-time data visualization
- **Dependencies**: API service

## 🔍 Data Access

### **Web Interface**
- **Dashboard**: http://localhost:3000
  - Interactive charts with user and metric selection
  - Auto-fetching data on parameter changes
  - Real-time visualization

### **API Endpoints**
```bash
# Get API information
curl http://localhost:8000/

# Get time-series data
curl "http://localhost:8000/timeseries?start_date=2025-06-29&end_date=2025-07-06&user_id=user1&metric=activities_heart_intraday"
```

### **Direct Database Access**
```bash
# Connect to TimescaleDB
docker exec -it timescaledb psql -U postgres -d fitbit-hr
```

### **Sample Queries**
```sql
-- Recent heart rate data by user
SELECT timestamp, value, user_id 
FROM activities_heart_intraday 
WHERE user_id = 'user1'
ORDER BY timestamp DESC 
LIMIT 10;

-- Daily heart rate summaries by user
SELECT timestamp, resting_heart_rate, user_id
FROM activities_heart_summary
WHERE user_id = 'user2'
ORDER BY timestamp DESC
LIMIT 7;

-- Compare data between users
SELECT 
    user_id,
    COUNT(*) as record_count,
    MIN(timestamp) as start_time,
    MAX(timestamp) as end_time
FROM activities_heart_intraday
GROUP BY user_id
ORDER BY user_id;

-- Time-based aggregations (TimescaleDB feature)
SELECT 
    time_bucket('1 hour', timestamp) as hour,
    user_id,
    AVG(value) as avg_hr
FROM activities_heart_intraday
WHERE user_id = 'user1'
GROUP BY hour, user_id
ORDER BY hour;
```
