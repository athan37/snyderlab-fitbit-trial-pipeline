"""
Heart Rate Time-Series API

FastAPI application for querying Fitbit heart rate time-series data from TimescaleDB
with automatic interval resolution and flexible aggregation.
"""

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services import TimeSeriesService
from controllers import root, get_timeseries

# Initialize FastAPI app
app = FastAPI(
    title="Heart Rate Time-Series API",
    description="API for querying Fitbit heart rate time-series data from TimescaleDB",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection pool
pool: asyncpg.Pool = None

# Service instances
time_series_service: TimeSeriesService = None


@app.on_event("startup")
async def startup_event():
    """Initialize database connection pool and services on startup"""
    global pool, time_series_service
    
    try:
        # Create connection pool
        pool = await asyncpg.create_pool(
            host="db",
            port=5432,
            user="postgres",
            password="password",
            database="fitbit-hr",
            min_size=1,
            max_size=10
        )
        
        # Initialize services
        time_series_service = TimeSeriesService(pool)
        
        print("✅ Database connection pool and services initialized successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize database connection: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connection pool on shutdown"""
    global pool
    if pool:
        await pool.close()
        print("✅ Database connection pool closed")


# Register routes
app.get("/")(root)
app.get("/timeseries")(get_timeseries)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 