
## 🎯 Software Design Decisions

Since the data are in fixed range, I modified and generate my own synthetic data so that the data for ingestion can catch up with the current date.

### **Why TimescaleDB **

**1. PostgreSQL Compatibility**

**2. Open Source Advantage**

**3. Time-Series Optimization**

- **Hypertables**: Automatic partitioning for time-series data
- **Compression**: Built-in columnar compression for storage efficiency


### **Architecture Benefits**

#### Mutiple ingestion pipeline support
Shared etl/ folder for both db-init-serice and ingestion-service. Also support mutiple ingestion.

- **db-init-service**: Uses shared ETL loaders for database schema creation
- **ingestion-service**: Uses shared ETL pipeline for data processing

### Benefits
- **Code Reuse**: Both services import from the same `etl/` folder
- **Consistency**: Ensures schema and data processing use identical logic

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
#### `activities_heart_summary` (Daily Summaries)

Optimize performance with indexing:

`CREATE UNIQUE INDEX IF NOT EXISTS idx_activities_heart_intraday_timestamp_user_id ON activities_heart_intraday (timestamp, user_id)`

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
