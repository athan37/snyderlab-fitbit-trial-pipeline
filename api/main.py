from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import asyncpg
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(
    title="Heart Rate Time-Series API",
    description="API for querying Fitbit heart rate time-series data from TimescaleDB",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection settings
DB_HOST = os.getenv('DB_HOST', 'timescaledb')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME', 'fitbit-hr')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')

DSN = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

class TimeSeriesResponse(BaseModel):
    timestamp: datetime
    value: float
    user_id: str

@app.on_event("startup")
async def startup():
    app.state.pool = await asyncpg.create_pool(dsn=DSN, min_size=1, max_size=5)

@app.on_event("shutdown")
async def shutdown():
    await app.state.pool.close()

@app.get("/", response_model=dict)
async def root():
    """Root endpoint providing API information"""
    return {
        "message": "Heart Rate Time-Series API", 
        "version": "1.0.0",
        "description": "API for querying Fitbit heart rate time-series data from TimescaleDB",
        "endpoints": {
            "/": "API information",
            "/timeseries": "Get time-series data with parameters: start_date, end_date, user_id, metric"
        }
    }

@app.get("/timeseries", response_model=list[TimeSeriesResponse])
async def get_timeseries(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    user_id: Optional[str] = Query(None, description="User ID to filter data"),
    metric: Optional[str] = Query("activities_heart_intraday", description="Metric type (activities_heart_intraday or activities_heart_summary)")
):
    """
    Single endpoint for fetching time-series data with comprehensive error/fallback flows.
    
    **Parameters:**
    - start_date: Start date for the query (defaults to 7 days ago if not provided)
    - end_date: End date for the query (defaults to today if not provided)
    - user_id: User ID to filter data (defaults to first available user if not provided)
    - metric: Metric type to query (defaults to activities_heart_intraday if not provided)
    
    **Error/Fallback Flows:**
    - If start_date not provided: uses 7 days ago
    - If end_date not provided: uses today
    - If user_id not provided: uses first available user from database
    - If metric not provided: uses activities_heart_intraday
    - If invalid date format: returns 400 error
    - If invalid metric: returns 400 error
    - If database error: returns 500 error
    - If no data found: returns empty array
    """
    from datetime import datetime as dt, timedelta
    
    # FALLBACK FLOW 1: Set default dates if not provided
    if not start_date:
        start_date = (dt.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = dt.now().strftime("%Y-%m-%d")
    
    # ERROR FLOW 1: Validate date format and convert to date objects
    try:
        start_date_obj = dt.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = dt.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail="Invalid date format. Use YYYY-MM-DD format for start_date and end_date."
        )
    
    # ERROR FLOW 2: Validate metric
    valid_metrics = ["activities_heart_intraday", "activities_heart_summary"]
    if metric not in valid_metrics:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid metric '{metric}'. Must be one of: {valid_metrics}"
        )
    
    # FALLBACK FLOW 2: Get default user_id if not provided
    if not user_id:
        try:
            async with app.state.pool.acquire() as conn:
                result = await conn.fetchval("""
                    SELECT user_id 
                    FROM activities_heart_intraday 
                    WHERE user_id IS NOT NULL
                    LIMIT 1
                """)
                if result:
                    user_id = result
                else:
                    user_id = "user1"  # Fallback default
        except Exception:
            user_id = "user1"  # Fallback default
    
    # Build query based on metric type
    if metric == "activities_heart_intraday":
        query = """
            SELECT 
                DATE(timestamp) as timestamp,
                AVG(value) as value,
                user_id
            FROM activities_heart_intraday
            WHERE timestamp >= $1::date AND timestamp < ($2::date + interval '1 day')
            AND user_id = $3
            GROUP BY DATE(timestamp), user_id
            ORDER BY DATE(timestamp)
        """
    elif metric == "activities_heart_summary":
        query = """
            SELECT timestamp, resting_heart_rate as value, user_id
            FROM activities_heart_summary
            WHERE timestamp >= $1::date AND timestamp < ($2::date + interval '1 day')
            AND user_id = $3
            AND resting_heart_rate IS NOT NULL
            ORDER BY timestamp
        """
    else:
        # This should never happen due to validation above, but included for completeness
        raise HTTPException(status_code=400, detail="Invalid metric type")
    
    # ERROR FLOW 3: Execute query with database error handling
    try:
        async with app.state.pool.acquire() as conn:
            rows = await conn.fetch(query, start_date_obj, end_date_obj, user_id)
            return [
                TimeSeriesResponse(
                    timestamp=row['timestamp'], 
                    value=row['value'], 
                    user_id=row['user_id']
                ) for row in rows
            ]
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database error: {str(e)}"
        ) 