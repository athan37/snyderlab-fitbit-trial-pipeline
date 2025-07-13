"""
Heart Rate Time-Series API Services

This module contains the business logic for querying heart rate time-series data
from TimescaleDB with automatic interval resolution and flexible aggregation.
"""

from typing import Optional, Dict, List, Tuple
from datetime import datetime
import asyncpg
from fastapi import HTTPException
import asyncio
from contextlib import asynccontextmanager


class TimeSeriesService:
    """Service class for handling time-series data operations"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool"""
        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            await self.pool.release(conn)
    
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
        
        # Build optimized query with time_bucket aggregation
        query = f"""
            SELECT 
                time_bucket('{time_bucket_interval}', {table_config['time_column']}) as timestamp,
                ROUND(AVG({table_config['value_column']}), 2) as value,
                user_id
            FROM {table_config['table']}
            WHERE {table_config['time_column']} >= $1::timestamp 
              AND {table_config['time_column']} <= $2::timestamp
              AND user_id = $3
              AND {table_config['value_column']} IS NOT NULL
            GROUP BY time_bucket('{time_bucket_interval}', {table_config['time_column']}), user_id
            ORDER BY timestamp
        """
        
        return query, [start_date, end_date, user_id]
    
    async def get_default_user_id(self) -> str:
        """Get the first available user ID as default"""
        try:
            conn = await self.pool.acquire()
            try:
                result = await conn.fetchval("""
                    SELECT user_id 
                    FROM activities_heart_intraday 
                    WHERE user_id IS NOT NULL 
                      AND user_id != '' 
                      AND user_id != 'default_user'
                    LIMIT 1
                """)
                return result if result else 'user1'
            finally:
                await self.pool.release(conn)
        except Exception:
            return 'user1'
    
    async def execute_timeseries_query(self, query: str, params: List) -> List[Dict]:
        """Execute a timeseries query and return results"""
        try:
            conn = await self.pool.acquire()
            try:
                results = await conn.fetch(query, *params)
                return [dict(row) for row in results]
            finally:
                await self.pool.release(conn)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database query error: {str(e)}"
            )
    
    async def execute_multi_user_query(self, query: str, user_ids: List[str], 
                                     start_date: datetime, end_date: datetime, 
                                     interval: Optional[str] = None) -> Tuple[List[Dict], Dict]:
        """Execute queries for multiple users concurrently"""
        
        async def fetch_user_data(user_id: str) -> Dict:
            try:
                data, query_info = await self.get_timeseries_data(
                    start_date, end_date, user_id, interval
                )
                return {
                    "user_id": user_id,
                    "data": data,
                    "count": len(data)
                }
            except Exception as e:
                print(f"Failed to get data for user {user_id}: {e}")
                return {
                    "user_id": user_id,
                    "data": [],
                    "count": 0
                }
        
        # Execute all user queries concurrently
        tasks = [fetch_user_data(user_id) for user_id in user_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and get successful results
        successful_results = [result for result in results if isinstance(result, dict)]
        
        # Build query information for metadata (use the same table config for all users)
        table_config = self.resolve_interval(start_date, end_date)
        query_info = {
            "table_used": table_config['table'],
            "table_description": table_config['description'],
            "interval": table_config['interval']
        }
        
        return successful_results, query_info

    async def get_timeseries_data(self, start_date: datetime, end_date: datetime, 
                                user_id: str, interval: Optional[str] = None) -> Tuple[List[Dict], Dict]:
        """
        Get timeseries data with automatic interval resolution and flexible aggregation.
        
        Args:
            start_date: Start date for the query
            end_date: End date for the query
            user_id: User ID to filter data
            interval: Requested output interval (1s, 1m, 1h, 1d) (optional)
        
        Returns:
            Tuple of (data_points, query_info) where query_info contains details about the query used
        """
        
        # Always use automatic resolution based on date range
        table_config = self.resolve_interval(start_date, end_date)
        
        # Build query based on requested interval
        if interval:
            # User requested specific interval - use flexible aggregation
            query, params = self.build_flexible_query(table_config, interval, start_date, end_date, user_id)
            response_interval = interval
        else:
            # Use the table's native interval with optimized query
            query = f"""
                SELECT 
                    {table_config['time_column']} as timestamp,
                    ROUND({table_config['value_column']}, 2) as value,
                    user_id
                FROM {table_config['table']}
                WHERE {table_config['time_column']} >= $1::timestamp 
                  AND {table_config['time_column']} <= $2::timestamp
                  AND user_id = $3
                  AND {table_config['value_column']} IS NOT NULL
                ORDER BY {table_config['time_column']}
            """
            params = [start_date, end_date, user_id]
            response_interval = table_config['interval']
        
        # Execute query
        results = await self.execute_timeseries_query(query, params)
        
        # Build query information for metadata
        query_info = {
            "table_used": table_config['table'],
            "table_description": table_config['description'],
            "interval": response_interval
        }
        
        return results, query_info 