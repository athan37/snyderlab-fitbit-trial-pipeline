"""
Heart Rate Time-Series API Services

This module contains the business logic for querying heart rate time-series data
from TimescaleDB with automatic interval resolution and flexible aggregation.
"""

from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import asyncpg
from fastapi import HTTPException


class TimeSeriesService:
    """Service class for handling time-series data queries"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    def resolve_interval(self, start_date: datetime, end_date: datetime) -> Dict:
        """
        Automatically resolve the appropriate interval and table based on date range.
        
        Rules:
        - < 20 minutes: Use raw data (activities_heart_intraday)
        - 20 minutes - 1 hour: Use 1-minute aggregates (activities_heart_intraday_1m)
        - 1 - 7 days: Use 1-hour aggregates (activities_heart_intraday_1h)
        - 7+ days: Use 1-day aggregates (activities_heart_intraday_1d)
        """
        duration = end_date - start_date
        minutes = duration.total_seconds() / 60
        hours = duration.total_seconds() / 3600
        days = duration.total_seconds() / 86400
        
        if minutes < 20:  # < 20 minutes
            return {
                "table": "activities_heart_intraday",
                "interval": "raw",
                "time_column": "timestamp",
                "value_column": "value",
                "description": "Raw heart rate data (per second)"
            }
        elif hours < 1:  # 20 minutes - 1 hour
            return {
                "table": "activities_heart_intraday_1m",
                "interval": "1m",
                "time_column": "minute",
                "value_column": "avg_heart_rate",
                "description": "1-minute aggregated heart rate data"
            }
        elif days <= 7:  # 1 - 7 days
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
    
    def build_flexible_query(self, table_config: Dict, requested_interval: str, 
                           start_date: datetime, end_date: datetime, user_id: str) -> Tuple[str, List]:
        """
        Build a flexible query that can aggregate data to any interval regardless of the source table.
        
        Args:
            table_config: Configuration for the source table
            requested_interval: The desired output interval (1s, 1m, 1h, 1d)
            start_date: Start date for the query
            end_date: End date for the query
            user_id: User ID to filter data
        
        Returns:
            Tuple of (query_string, query_parameters)
        """
        
        # Map intervals to TimescaleDB time_bucket intervals
        interval_map = {
            "1s": "1 second",
            "1m": "1 minute", 
            "1h": "1 hour",
            "1d": "1 day"
        }
        
        if requested_interval not in interval_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid interval '{requested_interval}'. Valid options: 1s, 1m, 1h, 1d"
            )
        
        time_bucket_interval = interval_map[requested_interval]
        
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
        
        return query, [start_date, end_date, user_id]
    
    def get_table_config_for_metric(self, metric: str) -> Dict:
        """Get table configuration for a specific metric"""
        if metric == "activities_heart_summary":
            return {
                "table": "activities_heart_summary",
                "interval": "summary",
                "time_column": "timestamp",
                "value_column": "resting_heart_rate",
                "description": "Daily summary data (resting heart rate)"
            }
        elif metric in ["activities_heart_intraday", "activities_heart_intraday_1m", "activities_heart_intraday_1h", "activities_heart_intraday_1d"]:
            # Map manual metric to table config
            interval_map = {
                "activities_heart_intraday": {"interval": "raw", "time_column": "timestamp", "value_column": "value"},
                "activities_heart_intraday_1m": {"interval": "1m", "time_column": "minute", "value_column": "avg_heart_rate"},
                "activities_heart_intraday_1h": {"interval": "1h", "time_column": "hour", "value_column": "avg_heart_rate"},
                "activities_heart_intraday_1d": {"interval": "1d", "time_column": "day", "value_column": "avg_heart_rate"}
            }
            config = interval_map[metric]
            return {
                "table": metric,
                "interval": config["interval"],
                "time_column": config["time_column"],
                "value_column": config["value_column"],
                "description": f"{config['interval']} aggregated heart rate data"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metric '{metric}'. Valid options: activities_heart_intraday, activities_heart_intraday_1m, activities_heart_intraday_1h, activities_heart_intraday_1d, activities_heart_summary"
            )
    
    async def get_default_user_id(self) -> str:
        """Get the first available user ID from the database"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("""
                    SELECT user_id 
                    FROM activities_heart_intraday 
                    WHERE user_id IS NOT NULL
                    LIMIT 1
                """)
                if result:
                    return result
                else:
                    return "user1"  # Fallback default
        except Exception:
            return "user1"  # Fallback default
    
    async def execute_timeseries_query(self, query: str, params: List) -> List[Dict]:
        """Execute a timeseries query and return the results"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [
                    {
                        "timestamp": row['timestamp'],
                        "value": float(row['value']),
                        "user_id": row['user_id']
                    } for row in rows
                ]
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Database error: {str(e)}"
            )
    
    async def get_timeseries_data(self, start_date: datetime, end_date: datetime, 
                                user_id: str, metric: Optional[str] = None, 
                                interval: Optional[str] = None) -> List[Dict]:
        """
        Get timeseries data with automatic interval resolution and flexible aggregation.
        
        Args:
            start_date: Start date for the query
            end_date: End date for the query
            user_id: User ID to filter data
            metric: Override automatic resolution with specific table (optional)
            interval: Requested output interval (1s, 1m, 1h, 1d) (optional)
        
        Returns:
            List of timeseries data points with timestamp, value, user_id, and interval
        """
        
        # Determine table configuration
        if metric:
            table_config = self.get_table_config_for_metric(metric)
        else:
            table_config = self.resolve_interval(start_date, end_date)
        
        # Build query based on requested interval
        if interval:
            # User requested specific interval - use flexible aggregation
            query, params = self.build_flexible_query(table_config, interval, start_date, end_date, user_id)
            response_interval = interval
        else:
            # Use the table's native interval
            query = f"""
                SELECT 
                    {table_config['time_column']} as timestamp,
                    {table_config['value_column']} as value,
                    user_id
                FROM {table_config['table']}
                WHERE {table_config['time_column']} >= $1::timestamp 
                  AND {table_config['time_column']} <= $2::timestamp
                  AND user_id = $3
                ORDER BY {table_config['time_column']}
            """
            params = [start_date, end_date, user_id]
            response_interval = table_config['interval']
        
        # Execute query and add interval to results
        results = await self.execute_timeseries_query(query, params)
        for result in results:
            result['interval'] = response_interval
        
        return results


class InfoService:
    """Service class for providing API information"""
    
    @staticmethod
    def get_api_info() -> Dict:
        """Get API information and documentation"""
        return {
            "automatic_interval_resolution": {
                "rules": {
                    "< 20 minutes": "Raw data (activities_heart_intraday)",
                    "20 minutes - 1 hour": "1-minute aggregates (activities_heart_intraday_1m)",
                    "1 - 7 days": "1-hour aggregates (activities_heart_intraday_1h)",
                    "7+ days": "1-day aggregates (activities_heart_intraday_1d)"
                },
                "description": "The API automatically selects the most appropriate table based on your date range"
            },
            "flexible_aggregation": {
                "description": "You can request any interval (1s, 1m, 1h, 1d) regardless of the source table",
                "supported_intervals": {
                    "1s": "1 second intervals",
                    "1m": "1 minute intervals", 
                    "1h": "1 hour intervals",
                    "1d": "1 day intervals"
                }
            },
            "available_tables": {
                "activities_heart_intraday": "Raw heart rate data (per second)",
                "activities_heart_intraday_1m": "1-minute aggregated data",
                "activities_heart_intraday_1h": "1-hour aggregated data", 
                "activities_heart_intraday_1d": "1-day aggregated data",
                "activities_heart_summary": "Daily summary data (resting heart rate)"
            },
            "parameters": {
                "start_date": "Start date (YYYY-MM-DD) - defaults to 7 days ago",
                "end_date": "End date (YYYY-MM-DD) - defaults to today",
                "user_id": "User ID to filter data - defaults to first available user",
                "metric": "Specific metric type (optional override)",
                "interval": "Requested output interval (1s, 1m, 1h, 1d) - overrides automatic resolution"
            }
        }
    
    @staticmethod
    def get_root_info() -> Dict:
        """Get root endpoint information"""
        return {
            "message": "Heart Rate Time-Series API", 
            "version": "1.0.0",
            "description": "API for querying Fitbit heart rate time-series data from TimescaleDB",
            "endpoints": {
                "/": "API information",
                "/timeseries": "Get time-series data with automatic interval resolution"
            }
        } 