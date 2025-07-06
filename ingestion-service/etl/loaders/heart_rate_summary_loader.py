from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from sqlalchemy import create_engine, text

from .base_loader import BaseLoader
from ..transformers.base_transformer import TransformedData
from config.settings import settings
from utils.logger import logger

class HeartRateSummaryLoader(BaseLoader):
    """Heart rate summary data loader - handles daily summary with heart rate zones"""
    
    def setup_database(self) -> bool:
        """Setup database connection and activities_heart_summary table"""
        try:
            logger.info("Setting up activities_heart_summary database...")
            
            # Test database connection first
            self.engine = create_engine(settings.DATABASE_URL)
            with self.engine.connect() as conn:
                # Test basic connectivity
                result = conn.execute(text("SELECT 1"))
                if not result.scalar():
                    raise Exception("Database connection test failed")
                logger.info("Database connection verified")
            
            # Create activities_heart_summary table if it doesn't exist
            with self.engine.connect() as conn:
                logger.info("Creating activities_heart_summary table...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS activities_heart_summary (
                        timestamp TIMESTAMPTZ NOT NULL,
                        resting_heart_rate INTEGER,
                        heart_rate_zones JSONB,
                        custom_heart_rate_zones JSONB,
                        PRIMARY KEY (timestamp)
                    )
                """))
                conn.commit()
                logger.info("Table creation SQL executed")
            
            # Verify table was created successfully
            with self.engine.connect() as conn:
                # Check if table exists
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'activities_heart_summary'
                    )
                """))
                table_exists = result.scalar()
                
                if not table_exists:
                    raise Exception("Table creation failed - table does not exist after CREATE")
                
                # Check table schema
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'activities_heart_summary'
                    ORDER BY ordinal_position
                """))
                columns = result.fetchall()
                
                expected_columns = [
                    ('timestamp', 'timestamp with time zone', 'NO'),
                    ('resting_heart_rate', 'integer', 'YES'),
                    ('heart_rate_zones', 'jsonb', 'YES'),
                    ('custom_heart_rate_zones', 'jsonb', 'YES')
                ]
                
                if len(columns) != len(expected_columns):
                    raise Exception(f"Table schema mismatch: expected {len(expected_columns)} columns, got {len(columns)}")
                
                for i, (col_name, data_type, is_nullable) in enumerate(columns):
                    expected_name, expected_type, expected_nullable = expected_columns[i]
                    if col_name != expected_name:
                        raise Exception(f"Column name mismatch at position {i}: expected '{expected_name}', got '{col_name}'")
                    if data_type != expected_type:
                        raise Exception(f"Column type mismatch for '{col_name}': expected '{expected_type}', got '{data_type}'")
                    if is_nullable != expected_nullable:
                        raise Exception(f"Column nullable mismatch for '{col_name}': expected '{expected_nullable}', got '{is_nullable}'")
                
                logger.info("Table schema verification passed")
            
            logger.info("Activities heart summary database setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Activities heart summary database setup FAILED: {e}")
            logger.error("This is a critical error that will prevent data loading")
            return False
    
    def get_table_name(self) -> str:
        """Get the table name for this loader"""
        return 'activities_heart_summary'
    
    def load_records(self, transformed_data: TransformedData, upsert_mode: bool = True) -> bool:
        """Load heart rate summary records into the database"""
        if not transformed_data.records:
            logger.warning("No heart rate summary records to load")
            return True
        
        try:
            self.reset_stats()
            
            # Extract target date from the first record
            target_date = None
            if transformed_data.records:
                first_record = transformed_data.records[0]
                if 'timestamp' in first_record:
                    # Extract date from timestamp
                    timestamp_str = first_record['timestamp']
                    if isinstance(timestamp_str, str):
                        try:
                            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            target_date = dt.strftime('%Y-%m-%d')
                        except:
                            pass
            
            if upsert_mode:
                logger.info("Using UPSERT mode to prevent duplicates")
                return self._batch_process(transformed_data.records, 1, self._upsert_batch, target_date)
            else:
                logger.info("Using regular INSERT mode")
                return self._batch_process(transformed_data.records, 1, self._insert_batch, target_date)
                
        except Exception as e:
            logger.error(f"Heart rate summary loading error: {e}")
            return False
    
    def _upsert_batch(self, batch: List[Dict[str, Any]], batch_num: int) -> bool:
        """Insert or update a batch of heart rate summary records using UPSERT"""
        try:
            with self.atomic_operation() as conn:
                # Get initial count
                initial_count = conn.execute(text("""
                    SELECT COUNT(*) FROM activities_heart_summary
                """)).scalar()
                
                # Insert records with UPSERT
                for record in batch:
                    conn.execute(text("""
                        INSERT INTO activities_heart_summary (timestamp, resting_heart_rate, heart_rate_zones, custom_heart_rate_zones)
                        VALUES (:timestamp, :resting_heart_rate, :heart_rate_zones, :custom_heart_rate_zones)
                        ON CONFLICT (timestamp) 
                        DO UPDATE SET 
                            resting_heart_rate = EXCLUDED.resting_heart_rate,
                            heart_rate_zones = EXCLUDED.heart_rate_zones,
                            custom_heart_rate_zones = EXCLUDED.custom_heart_rate_zones
                    """), record)
                
                # Get final count
                final_count = conn.execute(text("""
                    SELECT COUNT(*) FROM activities_heart_summary
                """)).scalar()
                
                actual_increase = final_count - initial_count
                logger.debug(f"Batch {batch_num}: {len(batch)} summary records processed (UPSERT mode)")
                
                return True
                
        except Exception as e:
            logger.error(f"Batch {batch_num} UPSERT error: {e}")
            return False
    
    def _insert_batch(self, batch: List[Dict[str, Any]], batch_num: int) -> bool:
        """Insert a batch of heart rate summary records using regular INSERT"""
        try:
            with self.atomic_operation() as conn:
                # Get initial count
                initial_count = conn.execute(text("""
                    SELECT COUNT(*) FROM activities_heart_summary
                """)).scalar()
                
                # Insert records
                for record in batch:
                    conn.execute(text("""
                        INSERT INTO activities_heart_summary (timestamp, resting_heart_rate, heart_rate_zones, custom_heart_rate_zones)
                        VALUES (:timestamp, :resting_heart_rate, :heart_rate_zones, :custom_heart_rate_zones)
                    """), record)
                
                # Get final count
                final_count = conn.execute(text("""
                    SELECT COUNT(*) FROM activities_heart_summary
                """)).scalar()
                
                actual_increase = final_count - initial_count
                expected_increase = len(batch)
                
                if actual_increase != expected_increase:
                    logger.warning(f"Batch {batch_num}: Expected {expected_increase}, got {actual_increase} records")
                else:
                    logger.debug(f"Batch {batch_num}: {expected_increase} summary records inserted and verified")
                
                return True
                
        except Exception as e:
            logger.error(f"Batch {batch_num} INSERT error: {e}")
            return False
    
    def verify_loading(self, expected_count: int) -> bool:
        """Verify that the expected number of heart rate summary records were loaded"""
        try:
            with self.engine.connect() as conn:
                actual_count = conn.execute(text("""
                    SELECT COUNT(*) FROM activities_heart_summary
                """)).scalar()
                
                logger.info(f"Database verification: {actual_count:,} heart rate daily records found")
                
                if actual_count >= expected_count:
                    logger.info(f"Loading verification passed: {actual_count:,} >= {expected_count:,}")
                    return True
                else:
                    logger.warning(f"Loading verification failed: {actual_count:,} < {expected_count:,}")
                    return False
                    
        except Exception as e:
            logger.error(f"Loading verification error: {e}")
            return False 