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


def main():
    """Initialize database schema and pipeline components"""
    logger.info("🚀 Starting Database Initialization Service")
    
    # Log configuration
    logger.info("Database Configuration:")
    logger.info(f"  • Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    logger.info(f"  • User: {settings.DB_USER}")
    logger.info(f"  • User ID: {settings.USER_ID}")
    logger.info(f"  • Data Seed: {settings.DATA_SEED}")
    
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