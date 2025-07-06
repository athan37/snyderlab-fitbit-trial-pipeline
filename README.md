# Heart Rate Data Pipeline with TimescaleDB

A production-ready ETL pipeline for ingesting Fitbit heart rate data using **TimescaleDB**, Docker, and Python. Features modular ETL architecture with delta processing, multi-user support, and reproducible data seeding.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  ETL Pipeline   │───▶│   TimescaleDB   │
│   (Simulated)   │    │   (Extract/     │    │   (Hypertable)  │
└─────────────────┘    │    Transform/   │    └─────────────────┘
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
```

### 2. Monitor Services
```bash
# Check service status
docker compose ps

# View logs for specific user
docker compose logs ingestion_user1
docker compose logs ingestion_user2
```

### 3. Access Data
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

## 🔍 Data Access

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

## 🛠️ Development

### **Project Structure**
```
Snyder/
├── docker-compose.yml              # Container orchestration
├── .dockerignore                   # Docker ignore patterns
├── ingestion-service/              # Ingestion service
│   ├── main.py                    # ETL pipeline entry point
│   └── Dockerfile                 # Service container
├── db-init-service/               # Database initialization
│   ├── main.py                    # Schema creation
│   └── Dockerfile                 # Service container
├── etl/                           # ETL Pipeline Components
│   ├── pipeline.py                # Main ETL orchestrator
│   ├── config/                    # Configuration
│   ├── extractors/                # Data extraction
│   ├── transformers/              # Data transformation
│   ├── loaders/                   # Data loading
│   ├── utils/                     # Utilities
│   └── requirements.txt           # Python dependencies
├── api/                           # FastAPI service
│   ├── main.py                    # API endpoints
│   ├── requirements.txt           # API dependencies
│   └── Dockerfile                 # API container
└── data/                          # Database persistence
    └── postgresql/                # TimescaleDB data
```

### **Adding New Data Types**
1. **Create Extractor**: Extend `BaseExtractor` class
2. **Create Transformer**: Extend `BaseTransformer` class  
3. **Create Loader**: Extend `BaseLoader` class
4. **Register Components**: Add to component dictionaries in `main.py`

### **Data Seeding Configuration**
- **Seed Values**: Configured per user in docker-compose.yml
- **Reproducibility**: Same seed produces identical data
- **Variation**: Different seeds create unique patterns
- **Cache**: Generated data cached in `cache/` directory

## 🎯 Key Benefits

### **✅ Multi-User Architecture**
- Separate containers for each user
- Independent processing and scheduling
- User-specific data patterns

### **✅ Reproducible Data**
- Deterministic data generation
- Cache-based performance
- Configurable seed values

### **✅ Production Ready**
- Docker containerization
- Cron-based scheduling
- Health monitoring
- Error handling

### **✅ Scalable Design**
- Modular ETL components
- Component-based architecture
- Easy to extend

## 📝 License
This project is for educational and development purposes.