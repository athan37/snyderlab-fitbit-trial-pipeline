"""
Heart Rate Time-Series API

FastAPI application for querying Fitbit heart rate time-series data from TimescaleDB
with automatic interval resolution.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncpg
import os

from controllers import root, get_timeseries, get_multi_user_timeseries, get_time_series_service, health_check, get_available_users, set_time_series_service
from services import TimeSeriesService
from prometheus_fastapi_instrumentator import Instrumentator

# Global service instance
time_series_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup database connections"""
    global time_series_service
    
    # Initialize database connection pool
    try:
        # Get database connection details from environment variables
        db_host = os.getenv('DB_HOST', 'postgresql')
        db_port = int(os.getenv('DB_PORT', '5432'))
        db_name = os.getenv('DB_NAME', 'fitbit_data')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', 'password')
        
        # Create connection pool
        pool = await asyncpg.create_pool(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
            min_size=5,
            max_size=20
        )
        
        # Initialize service with connection pool
        time_series_service = TimeSeriesService(pool)
        set_time_series_service(time_series_service)
        
        print("✅ Database connection pool and services initialized successfully")
        
        yield
        
    except Exception as e:
        print(f"❌ Failed to initialize database connection: {e}")
        raise
    finally:
        # Cleanup
        if time_series_service and hasattr(time_series_service, 'pool'):
            await time_series_service.pool.close()
            print("✅ Database connection pool closed")

# Create FastAPI app
app = FastAPI(
    title="Heart Rate Time-Series API",
    description="Optimized API for querying Fitbit heart rate time-series data from TimescaleDB",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus Instrumentator middleware
Instrumentator().instrument(app).expose(app)

# Root endpoint
app.get("/")(root)

# Health check endpoint
app.get("/health")(health_check)

# API endpoints
app.get("/users")(get_available_users)
app.get("/timeseries")(get_timeseries)
app.get("/multi-user/timeseries")(get_multi_user_timeseries)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 