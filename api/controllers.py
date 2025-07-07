"""
Heart Rate Time-Series API Controllers

This module contains all the endpoint handlers for the API.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Depends

from services import TimeSeriesService, InfoService


async def get_time_series_service() -> TimeSeriesService:
    """Dependency to get time series service"""
    # This will be injected by the main app
    from main import time_series_service
    if time_series_service is None:
        raise HTTPException(status_code=500, detail="Service not initialized")
    return time_series_service


async def root():
    """Root endpoint with API information"""
    return InfoService.get_root_info()


async def get_timeseries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user_id: Optional[str] = None,
    metric: Optional[str] = None,
    interval: Optional[str] = None,
    service: TimeSeriesService = Depends(get_time_series_service)
):
    """
    Get heart rate time-series data with automatic interval resolution.
    
    The API automatically selects the most appropriate table based on your date range:
    - < 20 minutes: Raw data (activities_heart_intraday)
    - 20 minutes - 1 hour: 1-minute aggregates (activities_heart_intraday_1m)
    - 1 - 7 days: 1-hour aggregates (activities_heart_intraday_1h)
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
    
    # Get user_id if not provided
    if not user_id:
        user_id = await service.get_default_user_id()
    
    # Get timeseries data using service
    try:
        data = await service.get_timeseries_data(
            start_date=start_dt,
            end_date=end_dt,
            user_id=user_id,
            metric=metric,
            interval=interval
        )
        
        return {
            "data": data,
            "metadata": {
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat(),
                "user_id": user_id,
                "count": len(data),
                "metric": metric,
                "interval": interval
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions from service
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 