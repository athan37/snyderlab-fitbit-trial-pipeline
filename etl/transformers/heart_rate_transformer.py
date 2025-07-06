from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_transformer import BaseTransformer, TransformedData
from ..extractors.base_extractor import ExtractedData
from etl.utils.logger import logger
from etl.config.settings import settings

class HeartRateTransformer(BaseTransformer):
    """Heart rate data transformer"""
    
    def __init__(self):
        super().__init__(name='activities_heart_intraday')
    
    def transform_records(self, extracted_data: ExtractedData) -> TransformedData:
        """Transform heart rate records into database format"""
        try:
            self.reset_stats()
            
            transformed_records = []
            target_date = None
            if extracted_data.records:
                # Try to get the date from the first record
                target_date = extracted_data.records[0].get('dateTime')
            
            for record in extracted_data.records:
                self.transformation_stats['total_records'] += 1
                
                try:
                    # Transform record to database format
                    transformed_record = self._transform_single_record(record)
                    
                    if transformed_record:
                        transformed_records.append(transformed_record)
                        self.transformation_stats['valid_records'] += 1
                    else:
                        self.transformation_stats['invalid_records'] += 1
                        
                except Exception as e:
                    logger.debug(f"Record transformation error: {e}")
                    self.transformation_stats['invalid_records'] += 1
                    continue
            
            # Create transformed data container
            transformed_data = TransformedData(
                schema=extracted_data.schema,
                records=transformed_records,
                transformation_stats=self.transformation_stats.copy()
            )
            
            if target_date:
                logger.info(f"Transformation completed for {target_date}: {self.transformation_stats['valid_records']} valid, {self.transformation_stats['invalid_records']} invalid")
            else:
                logger.info(f"Transformation completed: {self.transformation_stats['valid_records']} valid, {self.transformation_stats['invalid_records']} invalid")
            
            return transformed_data
            
        except Exception as e:
            logger.error(f"Transformation error: {e}")
            return TransformedData(
                schema=extracted_data.schema,
                records=[],
                transformation_stats=self.transformation_stats.copy()
            )
    
    def _transform_single_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform a single heart rate record to database format"""
        try:
            # Extract timestamp from dateTime and time fields
            date_time = record.get('dateTime')
            time_str = record.get('time')
            
            if not date_time or not time_str:
                logger.debug(f"Missing dateTime or time in record: {record}")
                return None
            
            # Combine date and time
            timestamp_str = f"{date_time}T{time_str}"
            
            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError as e:
                logger.debug(f"Invalid timestamp format: {timestamp_str}, error: {e}")
                return None
            
            # Extract value
            value = record.get('value')
            if value is None:
                logger.debug(f"Missing value in record: {record}")
                return None
            
            # Extract user_id
            user_id = record.get('user_id', 'user1')  # Default fallback
            
            # Create database record
            db_record = {
                'timestamp': timestamp,
                'value': float(value),
                'user_id': user_id
            }
            
            return db_record
            
        except Exception as e:
            logger.debug(f"Record transformation error: {e}")
            return None 