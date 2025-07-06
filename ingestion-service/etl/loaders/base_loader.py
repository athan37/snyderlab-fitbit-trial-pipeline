from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from sqlalchemy import create_engine, text
from contextlib import contextmanager

from ..transformers.base_transformer import TransformedData
from config.settings import settings
from utils.logger import logger

class BaseLoader(ABC):
    """Abstract base class for data loading"""
    
    def __init__(self):
        self.engine = None
        self.loading_stats = {
            'total_records': 0,
            'inserted_records': 0,
            'failed_records': 0,
            'batches_processed': 0,
            'batches_failed': 0
        }
    
    @abstractmethod
    def setup_database(self) -> bool:
        """Setup database connection and tables"""
        pass
    
    def get_last_processed_timestamp(self) -> Optional[str]:
        """Get the last processed timestamp from the database"""
        try:
            with self.engine.connect() as conn:
                # Get the table name from the loader
                table_name = self.get_table_name()
                result = conn.execute(
                    text(f"SELECT MAX(timestamp) FROM {table_name}")
                )
                last_timestamp = result.scalar()
                
                if last_timestamp:
                    logger.info(f"Last processed timestamp from {table_name}: {last_timestamp}")
                    return last_timestamp.isoformat()
                else:
                    logger.info(f"No previous data found in {table_name}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting last processed timestamp: {e}")
            return None
    
    @abstractmethod
    def get_table_name(self) -> str:
        """Get the table name for this loader"""
        pass
    
    @abstractmethod
    def load_records(self, transformed_data: TransformedData, upsert_mode: bool = True) -> bool:
        """Load transformed records into the database"""
        pass
    
    @abstractmethod
    def verify_loading(self, expected_count: int) -> bool:
        """Verify that the expected number of records were loaded"""
        pass
    
    def get_loading_stats(self) -> Dict[str, int]:
        """Get loading statistics"""
        return self.loading_stats.copy()
    
    def reset_stats(self):
        """Reset loading statistics"""
        self.loading_stats = {
            'total_records': 0,
            'inserted_records': 0,
            'failed_records': 0,
            'batches_processed': 0,
            'batches_failed': 0
        }
    
    @contextmanager
    def atomic_operation(self):
        """Context manager for atomic database operations"""
        if not self.engine:
            logger.error("❌ Database engine not initialized - setup_database() must be called first")
            yield False
            return
        
        connection = self.engine.connect()
        transaction = connection.begin()
        
        try:
            yield connection
            transaction.commit()
            logger.debug("Atomic operation committed successfully")
        except Exception as e:
            transaction.rollback()
            logger.error(f"❌ Atomic operation failed, rolled back: {e}")
            raise
        finally:
            connection.close()
    
    def _batch_process(self, records: List[Dict[str, Any]], 
                      batch_size: int, 
                      process_batch_func,
                      target_date: str = None) -> bool:
        """Generic batch processing with progress tracking"""
        if not records:
            logger.warning("No records to process")
            return True
        
        try:
            total_records = len(records)
            date_info = f" for {target_date}" if target_date else ""
            logger.info(f"Processing {total_records:,} records in batches of {batch_size:,}{date_info}")
            
            for i in range(0, total_records, batch_size):
                batch = records[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                try:
                    # Process batch
                    result = process_batch_func(batch, batch_num)
                    
                    if result:
                        self.loading_stats['batches_processed'] += 1
                        self.loading_stats['inserted_records'] += len(batch)
                    else:
                        self.loading_stats['batches_failed'] += 1
                        self.loading_stats['failed_records'] += len(batch)
                    
                    # Log progress with date info
                    progress_pct = ((i + len(batch)) / total_records) * 100
                    date_suffix = f" ({target_date})" if target_date else ""
                    logger.info(f"Progress: {progress_pct:.1f}% ({i + len(batch):,}/{total_records:,} records){date_suffix}")
                    
                except Exception as e:
                    logger.error(f"Batch {batch_num} processing error: {e}")
                    self.loading_stats['batches_failed'] += 1
                    self.loading_stats['failed_records'] += len(batch)
                    return False
            
            date_suffix = f" for {target_date}" if target_date else ""
            logger.info(f"Batch processing completed: {self.loading_stats['batches_processed']} batches processed, "
                       f"{self.loading_stats['batches_failed']} failed{date_suffix}")
            return True
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            return False 