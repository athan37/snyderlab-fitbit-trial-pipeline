"""
Heart Rate Time-Series API Controllers

This module contains all the endpoint handlers for the API with optimized performance.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import HTTPException, Depends
from pydantic import BaseModel
import logging

from services import TimeSeriesService

logger = logging.getLogger(__name__)

# Global service instance
_time_series_service = None

def get_time_series_service() -> TimeSeriesService:
    """Get the global time series service instance"""
    if _time_series_service is None:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return _time_series_service

def set_time_series_service(service: TimeSeriesService):
    """Set the global time series service instance"""
    global _time_series_service
    _time_series_service = service

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    response_time_seconds: float
    database_connected: bool
    performance_optimizations: List[str]

class UserResponse(BaseModel):
    users: List[str]
    total_count: int
    last_updated: str

async def get_available_users(service: TimeSeriesService = Depends(get_time_series_service)) -> UserResponse:
    """Get list of available users from the database"""
    
    try:
        async with service.get_connection() as conn:
            # Query to get distinct user_ids with some basic stats, excluding default_user
            query = """
            SELECT DISTINCT user_id,
                   COUNT(*) as record_count,
                   MIN(timestamp) as first_record,
                   MAX(timestamp) as last_record
            FROM activities_heart_intraday 
            WHERE user_id IS NOT NULL 
            AND user_id != '' 
            AND user_id != 'default_user'
            GROUP BY user_id
            ORDER BY last_record DESC, user_id ASC
            """
            
            rows = await conn.fetch(query)
            
            users = [row['user_id'] for row in rows]
            
            return UserResponse(
                users=users,
                total_count=len(users),
                last_updated=datetime.now().isoformat()
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch available users: {str(e)}"
        )

async def health_check(service: TimeSeriesService = Depends(get_time_series_service)) -> HealthResponse:
    """Health check endpoint to verify API and database connectivity"""
    start_time = datetime.now()
    
    try:
        # Test database connection
        async with service.get_connection() as conn:
            await conn.fetchval("SELECT 1")
        
        response_time = (datetime.now() - start_time).total_seconds()
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            response_time_seconds=response_time,
            database_connected=True,
            performance_optimizations=[
                "Automatic interval resolution",
                "Connection pooling",
                "Prepared statements",
                "Concurrent multi-user queries"
            ]
        )
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds()
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now().isoformat(),
            response_time_seconds=response_time,
            database_connected=False,
            performance_optimizations=[]
        )

async def root():
    """Root endpoint with API information"""
    return {
        "message": "Heart Rate Time-Series API",
        "version": "2.0.0",
        "description": "Optimized API for querying Fitbit heart rate time-series data from TimescaleDB",
        "endpoints": {
            "/": "API information",
            "/timeseries": "Get time-series data with automatic interval resolution",
            "/multi-user/timeseries": "Get time-series data for multiple users",
            "/users": "Get list of available users",
            "/health": "Health check endpoint"
        },
        "performance_features": [
            "Automatic data decimation for large datasets",
            "Concurrent multi-user queries",
            "Optimized database queries with prepared statements",
            "Intelligent caching",
            "Connection pool management"
        ]
    }

async def get_timeseries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: Optional[str] = None,
    interval: Optional[str] = None,
    service: TimeSeriesService = Depends(get_time_series_service)
):
    """
    Get heart rate time-series data with automatic interval resolution.
    
    The API automatically selects the most appropriate table based on your date range:
    - < 2 minutes: Raw data (activities_heart_intraday)
    - 2 minutes - 2 hours: 1-minute aggregates (activities_heart_intraday_1m)
    - 2+ hours - 7 days: 1-hour aggregates (activities_heart_intraday_1h)
    - 7+ days: 1-day aggregates (activities_heart_intraday_1d)
    
    You can also request specific intervals (1s, 1m, 1h, 1d) for flexible aggregation.
    """
    
    # Parse and validate dates
    try:
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        else:
            start_dt = datetime.now() - timedelta(days=7)
            
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        else:
            end_dt = datetime.now()
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    
    # Validate date range
    if start_dt >= end_dt:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    
    # Validate date range size for performance
    max_days = 365
    if (end_dt - start_dt).days > max_days:
        raise HTTPException(
            status_code=400, 
            detail=f"Date range too large. Maximum {max_days} days allowed for optimal performance."
        )
    
    # Get user_id if not provided
    if not user_id:
        user_id = await service.get_default_user_id()
    
    # Get timeseries data using service
    try:
        data, query_info = await service.get_timeseries_data(
            start_date=start_dt,
            end_date=end_dt,
            user_id=user_id,
            interval=interval
        )
        
        # Build metadata with only the fields used by frontend
        metadata = {
            "query_info": query_info
        }
            
        return {
            "data": data,
            "metadata": metadata
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions from service
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def get_multi_user_timeseries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_ids: Optional[str] = None,  # Comma-separated list of user IDs
    interval: Optional[str] = None,
    service: TimeSeriesService = Depends(get_time_series_service)
):
    """
    Get heart rate time-series data for multiple users for comparison.
    Uses concurrent processing for optimal performance.
    
    Args:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        user_ids: Comma-separated list of user IDs (e.g., "user1,user2")
        interval: Optional interval override
    """
    
    # Parse and validate dates
    try:
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        else:
            start_dt = datetime.now() - timedelta(days=7)
            
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        else:
            end_dt = datetime.now()
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    
    # Validate date range
    if start_dt >= end_dt:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    
    # Validate date range size for performance
    max_days = 180  # Reduced for multi-user queries
    if (end_dt - start_dt).days > max_days:
        raise HTTPException(
            status_code=400, 
            detail=f"Date range too large for multi-user queries. Maximum {max_days} days allowed."
        )
    
    # Parse user IDs
    if user_ids:
        user_id_list = [uid.strip() for uid in user_ids.split(',') if uid.strip()]
    else:
        # Default to available users
        user_id_list = ['user1', 'user2']
    
    # Validate user count
    if len(user_id_list) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 users allowed for comparison")
    
    if len(user_id_list) == 0:
        raise HTTPException(status_code=400, detail="At least one user ID must be provided")
    
    # Get data for all users using concurrent processing
    try:
        multi_user_data, query_info = await service.execute_multi_user_query(
            query="", # Not used in the new implementation
            user_ids=user_id_list,
            start_date=start_dt,
            end_date=end_dt,
            interval=interval
        )
        
        # Build metadata with only the fields used by frontend
        metadata = {
            "query_info": query_info
        }
            
        return {
            "data": multi_user_data,
            "metadata": metadata
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 