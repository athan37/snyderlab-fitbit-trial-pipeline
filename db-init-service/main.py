#!/usr/bin/env python3
"""
Database Initialization Service

This service initializes the database schema and pipeline components
without inserting any data. It's designed to run before the ingestion service.
"""

import sys
import os
from sqlalchemy import text

# Add the etl directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'etl'))

from etl.loaders.heart_rate_loader import HeartRateLoader
from etl.loaders.heart_rate_summary_loader import HeartRateSummaryLoader
from etl.config.settings import settings
from etl.utils.logger import logger


def get_1m_view_sql():
    return '''
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
    '''

def get_1h_view_sql():
    return '''
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
    '''

def get_1d_view_sql():
    return '''
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
    '''

def create_continuous_aggregate_view(engine):
    """Create continuous aggregate views for heart rate data (1m, 1h, 1d)"""
    try:
        logger.info("📊 Creating continuous aggregate views (1m, 1h, 1d)...")
        
        # Use autocommit mode to avoid transaction block issues
        with engine.connect() as conn:
            conn.execute(text("COMMIT"))  # End any existing transaction
            conn.connection.autocommit = True
            
            # Create 1-minute view
            logger.info("Creating 1-minute view...")
            conn.execute(text(get_1m_view_sql()))
            logger.info("✅ 1-minute view created")
            
            # Create 1-hour view
            logger.info("Creating 1-hour view...")
            conn.execute(text(get_1h_view_sql()))
            logger.info("✅ 1-hour view created")
            
            # Create 1-day view
            logger.info("Creating 1-day view...")
            conn.execute(text(get_1d_view_sql()))
            logger.info("✅ 1-day view created")
            
            conn.connection.autocommit = False  # Reset autocommit
            
        logger.info("✅ All continuous aggregate views created successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to create continuous aggregate views: {e}")
        raise e


def create_indexes(engine):
    """Create additional indexes for performance optimization"""
    try:
        logger.info("📊 Creating additional indexes...")
        
        with engine.connect() as conn:
            # Create unique index for UPSERT operations (composite key)
            logger.info("Creating unique index for (timestamp, user_id)...")
            conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_activities_heart_intraday_timestamp_user_id 
                ON activities_heart_intraday (timestamp, user_id)
            """))
            logger.info("✅ Unique index created successfully")
            
            conn.commit()
            
        logger.info("✅ All indexes created successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to create indexes: {e}")
        raise e


def main():
    """Initialize database schema and pipeline components"""
    logger.info("🚀 Starting Database Initialization Service")
    
    # Log configuration
    logger.info("Database Configuration:")
    logger.info(f"  • Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    logger.info(f"  • User: {settings.DB_USER}")
    logger.info(f"  • User ID: {settings.USER_ID}")
    
    try:
        # Initialize heart rate loader
        logger.info("📊 Initializing activities_heart_intraday table...")
        heart_rate_loader = HeartRateLoader()
        if heart_rate_loader.setup_database():
            logger.info("✅ activities_heart_intraday table initialized successfully")
        else:
            logger.error("❌ Failed to initialize activities_heart_intraday table")
            sys.exit(1)
        
        # Initialize heart rate summary loader
        logger.info("📊 Initializing activities_heart_summary table...")
        heart_rate_summary_loader = HeartRateSummaryLoader()
        if heart_rate_summary_loader.setup_database():
            logger.info("✅ activities_heart_summary table initialized successfully")
        else:
            logger.error("❌ Failed to initialize activities_heart_summary table")
            sys.exit(1)
        
        # Create additional indexes
        logger.info("📊 About to create additional indexes...")
        try:
            create_indexes(heart_rate_loader.engine)
            logger.info("✅ Index creation completed")
        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            # Don't exit here, continue with the rest of the initialization
        
        # Create continuous aggregate view for analytics
        logger.info("📊 About to create continuous aggregate views...")
        try:
            create_continuous_aggregate_view(heart_rate_loader.engine)
            logger.info("✅ Continuous aggregate views creation completed")
        except Exception as e:
            logger.error(f"❌ Failed to create continuous aggregate views: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            # Don't exit here, continue with the rest of the initialization
        
        # Verify database connection
        logger.info("🔍 Verifying database connection...")
        try:
            with heart_rate_loader.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("✅ Database connection verified")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            sys.exit(1)
        
        # Check existing data
        logger.info("📈 Checking existing data...")
        try:
            with heart_rate_loader.engine.connect() as conn:
                # Check intraday data
                intraday_count = conn.execute(text("SELECT COUNT(*) FROM activities_heart_intraday")).scalar()
                logger.info(f"  • activities_heart_intraday: {intraday_count:,} records")
                
                # Check summary data
                summary_count = conn.execute(text("SELECT COUNT(*) FROM activities_heart_summary")).scalar()
                logger.info(f"  • activities_heart_summary: {summary_count:,} records")
                
                # Check users
                users = conn.execute(text("SELECT DISTINCT user_id FROM activities_heart_intraday")).fetchall()
                user_count = len(users)
                logger.info(f"  • Unique users: {user_count}")
                if users:
                    user_list = [user[0] for user in users]
                    logger.info(f"  • Users: {', '.join(user_list)}")
                
                # Check continuous aggregate view
                view_count = conn.execute(text("SELECT COUNT(*) FROM activities_heart_intraday_1d")).scalar()
                logger.info(f"  • Continuous aggregate view: {view_count:,} daily records")
                
        except Exception as e:
            logger.error(f"❌ Error checking existing data: {e}")
            sys.exit(1)
        
        logger.info("🎉 Database initialization completed successfully!")
        logger.info("📋 Ready for ingestion service to start")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 