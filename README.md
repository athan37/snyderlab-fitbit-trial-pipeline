# Heart Rate Data Pipeline with TimescaleDB

A production-ready ETL pipeline for ingesting Fitbit heart rate data using **TimescaleDB**, Docker, and Python. Features modular ETL architecture with delta processing and multi-data-type support.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Fitbit API    │───▶│  ETL Pipeline   │───▶│   TimescaleDB   │
│   (wearipedia)  │    │   (Extract/     │    │   (Hypertable)  │
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

### 1. Start Services
```bash
docker-compose up -d
```

### 2. Run ETL Pipeline
```bash
docker-compose up --build ingestion-service
```

### 3. Analyze Data
```bash
python show_table.py
```

## 📊 Data Schema

### TimescaleDB Tables

#### `activities_heart_intraday` (Intraday Heart Rate)
```sql
CREATE TABLE activities_heart_intraday (
    timestamp TIMESTAMPTZ NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (timestamp)
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
    PRIMARY KEY (timestamp)
);
```

## 🔧 Configuration

### Environment Variables
```env
# Database Configuration
DB_HOST=timescaledb
DB_PORT=5432
DB_NAME=fitbit-hr
DB_USER=postgres
DB_PASSWORD=password

# ETL Configuration
START_DATE=2025-06-01
END_DATE=2025-06-30
BATCH_SIZE=1000
UPSERT_MODE=true
DELTA_MODE=true
```

## 🔍 Data Access

### **Direct Database Access**
```bash
# Connect to TimescaleDB
psql -h localhost -p 5432 -U postgres -d fitbit-hr
```

### **Sample Queries**
```sql
-- Recent heart rate data
SELECT timestamp, value 
FROM activities_heart_intraday 
ORDER BY timestamp DESC 
LIMIT 10;

-- Daily heart rate summaries
SELECT timestamp, resting_heart_rate, heart_rate_zones
FROM activities_heart_summary
ORDER BY timestamp DESC
LIMIT 7;

-- Time-based aggregations (TimescaleDB feature)
SELECT 
    time_bucket('1 hour', timestamp) as hour,
    AVG(value) as avg_hr
FROM activities_heart_intraday
GROUP BY hour
ORDER BY hour;
```

## 🛠️ Development

### **Adding New Data Types**
1. **Create Extractor**: Extend `BaseExtractor` class
2. **Create Transformer**: Extend `BaseTransformer` class  
3. **Create Loader**: Extend `BaseLoader` class
4. **Register Components**: Add to component dictionaries

### **Project Structure**
```
Snyder/
├── docker-compose.yml              # Main Docker orchestration
├── ingestion-service/
│   ├── main.py                     # ETL pipeline entry point
│   ├── config/settings.py         # Configuration management
│   └── etl/                       # ETL Pipeline Components
│       ├── pipeline.py            # Main ETL orchestrator
│       ├── extractors/            # Data extraction
│       ├── transformers/          # Data transformation
│       └── loaders/               # Data loading
└── data/                          # TimescaleDB persistent storage
```

## 🎯 Key Features

### **✅ Modular Architecture**
- Separate extractors, transformers, and loaders
- Single responsibility principle
- Easy to test and maintain

### **✅ Delta Processing**
- Automatic detection of new records
- Database-based timestamp tracking
- Idempotent operations

### **✅ Extensible Design**
- Key-based component relationships
- Configuration-driven architecture

## 📝 License
This project is for educational and development purposes.