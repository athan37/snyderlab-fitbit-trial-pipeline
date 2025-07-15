# Task 3: Optimizing Design for Multi-Year / Multi-User Queries

## Overview

This task focused on optimizing the Heart Rate Time-Series API for efficient handling of multi-year and multi-user queries while maintaining excellent performance across all time ranges. I implemented a comprehensive API with dynamic query ranges, multi-user support, and real-time monitoring capabilities with 1m, 1h, 1d aggregate views in addition to the 1s raw data.

## 🚀 Key Optimizations Implemented

### 1. **Dynamic Query Range System**

We implemented a smart query routing system that automatically selects the most appropriate table/view based on the time range:

| Query Range | Table/View Used | Record Estimate | Performance | Use Case |
|-------------|-----------------|-----------------|-------------|----------|
| **< 2 minutes** | `activities_heart_intraday` | Up to 120 (1/sec) | ⚡️ Instant | High-resolution zoom-in analysis |
| **2 min – 2 hours** | `activities_heart_intraday_1m` | 120 – 7,200 (1/min) | ⚡️ Instant | Short to medium timeframes |
| **2+ hours – 7 days** | `activities_heart_intraday_1h` | 2 – 168 (1/hour) | ⚡️ Instant | Daily/weekly trend analysis |
| **7+ days** | `activities_heart_intraday_1d` | 7+ (1/day) | ⚡️ Instant | Long-range analytics |

### 2. **TimescaleDB Continuous Aggregates**

Leveraged TimescaleDB's continuous aggregate views for optimal performance:

```sql
-- 1-minute aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS activities_heart_intraday_1m
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

-- 1-hour aggregates  
CREATE MATERIALIZED VIEW IF NOT EXISTS activities_heart_intraday_1h
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

-- 1-day aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS activities_heart_intraday_1d
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

### 3. **Intelligent Interval Resolution Algorithm**

The API automatically selects the optimal table based on query duration:

```python
def resolve_interval(self, start_date: datetime, end_date: datetime) -> Dict:
    """
    Automatically resolve the appropriate interval and table based on date range.
    
    Rules:
    - < 2 minutes: Use raw data (activities_heart_intraday)
    - 2 minutes - 2 hours: Use minute-level aggregates (activities_heart_intraday_1m)
    - 2+ hours - 7 days: Use hour-level aggregates (activities_heart_intraday_1h)
    - 7+ days: Use day-level aggregates (activities_heart_intraday_1d)
    """
    duration = end_date - start_date
    hours = duration.total_seconds() / 3600
    days = duration.total_seconds() / 86400
    
    if hours < (2/60):  # < 2 minutes
        return {
            "table": "activities_heart_intraday",
            "interval": "raw",
            "time_column": "timestamp",
            "value_column": "value",
            "description": "Raw heart rate data (per second)"
        }
    elif hours <= 2:  # 2 minutes - 2 hours
        return {
            "table": "activities_heart_intraday_1m",
            "interval": "1m",
            "time_column": "minute",
            "value_column": "avg_heart_rate",
            "description": "1-minute aggregated heart rate data"
        }
    elif days <= 7:  # 2+ hours - 7 days
        return {
            "table": "activities_heart_intraday_1h",
            "interval": "1h",
            "time_column": "hour",
            "value_column": "avg_heart_rate",
            "description": "1-hour aggregated heart rate data"
        }
    else:  # 7+ days
        return {
            "table": "activities_heart_intraday_1d",
            "interval": "1d",
            "time_column": "day",
            "value_column": "avg_heart_rate",
            "description": "1-day aggregated heart rate data"
        }
```

### 4. **Comprehensive API Endpoints**

Implemented a complete RESTful API with multiple endpoints:

#### **Single User Time-Series Endpoint**
```bash
GET /timeseries?start_date=2025-06-29&end_date=2025-07-06&user_id=user1&metric=activities_heart_intraday
```

#### **Multi-User Time-Series Endpoint**
```bash
GET /multi-user/timeseries?start_date=2025-06-29&end_date=2025-07-06&metric=activities_heart_intraday
```

#### **Available Users Endpoint**
```bash
GET /users
```

### 5. **Flexible Aggregation System**

The API supports both automatic interval resolution and manual interval specification:

```python
def build_flexible_query(self, table_config: Dict, requested_interval: str, 
                       start_date: datetime, end_date: datetime, user_id: str):
    # Map intervals to TimescaleDB time_bucket intervals
    interval_map = {
        "1s": "1 second",
        "1m": "1 minute", 
        "1h": "1 hour",
        "1d": "1 day"
    }
    
    # Build query with time_bucket aggregation
    query = f"""
        SELECT 
            time_bucket('{time_bucket_interval}', {table_config['time_column']}) as timestamp,
            ROUND(AVG({table_config['value_column']}), 2) as value,
            user_id
        FROM {table_config['table']}
        WHERE {table_config['time_column']} >= $1::timestamp 
          AND {table_config['time_column']} <= $2::timestamp
          AND user_id = $3
        GROUP BY time_bucket('{time_bucket_interval}', {table_config['time_column']}), user_id
        ORDER BY timestamp
    """
```

### 6. **Multi-User Data Support**

- **User Isolation:** All queries filter by `user_id` for data security
- **Multi-User Endpoints:** Dedicated endpoints for comparing data across users
- **Concurrent Processing:** Multi-user queries execute concurrently for optimal performance
- **User Management:** Support for multiple users with separate data ingestion pipelines
- **Data Verification:** 2 users with comprehensive data sets for testing
