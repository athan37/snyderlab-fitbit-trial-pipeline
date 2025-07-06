from typing import List, Dict, Any
from datetime import datetime

from .base_transformer import BaseTransformer, TransformedData
from ..extractors.base_extractor import ExtractedData
from utils.logger import logger

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
    
    def _transform_single_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a single heart rate record"""
        try:
            # Handle raw data format from extractor (dateTime + time)
            if 'dateTime' in record and 'time' in record:
                date_str = record.get('dateTime')
                time_str = record.get('time')
                if not date_str or not time_str:
                    self.transformation_stats['invalid_records'] += 1
                    return None
                timestamp_str = f"{date_str} {time_str}"
                # Remove original fields
                record.pop('dateTime', None)
                record.pop('time', None)
            else:
                self.transformation_stats['invalid_records'] += 1
                return None
            
            # Get value and handle missing values
            value = record.get('value', 0)
            if value is None:
                value = 0
                self.transformation_stats['missing_values_filled'] += 1
            
            # Convert to float
            try:
                value = float(value)
            except (ValueError, TypeError):
                value = 0.0
                self.transformation_stats['missing_values_filled'] += 1
            
            # Create database record
            db_record = {
                'timestamp': datetime.fromisoformat(timestamp_str),
                'value': value
            }
            
            return db_record
            
        except Exception as e:
            logger.debug(f"Single record transformation error: {e}")
            return None 