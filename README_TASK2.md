# Task 2: API & Frontend Setup

## Overview
Build a data flow model from a locally hosted time-series database (e.g. TimescaleDB) into a local dashboard app for analysis and visualization. 

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   TimescaleDB   │───▶│   FastAPI       │───▶│   React App     │
│   (Data Store)  │    │   (Backend)     │    │   (Frontend)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

1. **React**: Rapid UI development with excellent state management
2. **FastAPI**: Quick backend with automatic validation and docs
3. **Docker**: Consistent environment and easy deployment
4. **Single Endpoint**: Simple API design with comprehensive functionality
5. **Auto-fetching on State Change**: Dashboard updates automatically when user changes any parameter (user, metric, dates)

## Single Query Endpoint

```python
@app.get("/timeseries")
async def get_timeseries(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None), 
    user_id: Optional[str] = Query(None),
    metric: Optional[str] = Query("activities_heart_intraday")
):
    # Returns time-series data with comprehensive error handling
```

**Features:**
- **Flexible Parameters**: All optional with smart defaults
- **Fallback Logic**: Auto-selects first available user if none specified
- **Error Handling**: Validates dates, metrics, database connections
- **CORS Enabled**: Frontend can call from different origin

## Monorepo with Docker

### **Service Architecture**
```yaml
services:
  db:          # TimescaleDB
  api:         # FastAPI backend  
  client:      # React frontend
```

### **Benefits**
- **Single Command**: `docker compose up` starts everything
- **Network Isolation**: Services communicate via Docker network
- **Environment Consistency**: Same setup across development/production
- **Easy Deployment**: All services containerized

## Key Implementation Details

### **Frontend State Flow**
```typescript
// Auto-fetch on parameter change
useEffect(() => {
  if (startDate && endDate && userId && metric) {
    fetchData();
  }
}, [startDate, endDate, userId, metric]);
```

### **CORS Configuration**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
)
```

## Usage

```bash
# Start all services
docker compose up -d

# Access points
Frontend: http://localhost:3000
API: http://localhost:8000
API Docs: http://localhost:8000/docs
```


