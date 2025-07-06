from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from .base_transformer import BaseTransformer, TransformedData
from ..extractors.base_extractor import ExtractedData
from etl.utils.logger import logger
from etl.config.settings import settings

class HeartRateSummaryTransformer(BaseTransformer):
    """Heart rate summary data transformer"""
    
    def __init__(self):
        super().__init__(name='activities_heart_summary')
    
    def transform_records(self, extracted_data: ExtractedData) -> TransformedData:
        """Transform heart rate summary records into database format"""
        try:
            self.reset_stats()
            
            # For summary data, we expect a single record with summary information
            if not extracted_data.records:
                logger.warning("No heart rate summary records to transform")
                return TransformedData(
                    schema=extracted_data.schema,
                    records=[],
                    transformation_stats=self.transformation_stats.copy()
                )
            
            # Transform the summary record (should be only one)
            transformed_records = []
            target_date = None
            for record in extracted_data.records:
                self.transformation_stats['total_records'] += 1
                if not target_date:
                    target_date = record.get('dateTime')
                try:
                    transformed_record = self._transform_summary_record(record)
                    
                    if transformed_record:
                        transformed_records.append(transformed_record)
                        self.transformation_stats['valid_records'] += 1
                    else:
                        self.transformation_stats['invalid_records'] += 1
                        
                except Exception as e:
                    logger.debug(f"Summary record transformation error: {e}")
                    self.transformation_stats['invalid_records'] += 1
                    continue
            
            # Create transformed data container
            transformed_data = TransformedData(
                schema=extracted_data.schema,
                records=transformed_records,
                transformation_stats=self.transformation_stats.copy()
            )
            
            if target_date:
                logger.info(f"Summary transformation completed for {target_date}: {self.transformation_stats['valid_records']} valid, {self.transformation_stats['invalid_records']} invalid")
            else:
                logger.info(f"Summary transformation completed: {self.transformation_stats['valid_records']} valid, {self.transformation_stats['invalid_records']} invalid")
            
            return transformed_data
            
        except Exception as e:
            logger.error(f"Summary transformation error: {e}")
            return TransformedData(
                schema=extracted_data.schema,
                records=[],
                transformation_stats=self.transformation_stats.copy()
            )
    
    def _transform_summary_record(self, summary_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform a single heart rate summary record to database format"""
        try:
            # Extract timestamp
            timestamp_str = summary_data.get('dateTime')
            if not timestamp_str:
                logger.debug(f"Missing dateTime in summary record: {summary_data}")
                return None
            
            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError as e:
                logger.debug(f"Invalid timestamp format: {timestamp_str}, error: {e}")
                return None
            
            # Extract resting heart rate
            resting_hr = summary_data.get('resting_heart_rate')
            if resting_hr is not None:
                try:
                    resting_hr = int(resting_hr)
                except (ValueError, TypeError):
                    logger.debug(f"Invalid resting heart rate: {resting_hr}")
                    resting_hr = None
            
            # Extract heart rate zones
            heart_rate_zones = summary_data.get('heart_rate_zones')
            if heart_rate_zones:
                # Convert to JSONB format
                try:
                    heart_rate_zones_json = json.dumps(heart_rate_zones)
                except Exception as e:
                    logger.warning(f"Error serializing heart rate zones: {e}")
                    heart_rate_zones_json = None
            else:
                heart_rate_zones_json = None
            
            # Extract custom heart rate zones
            custom_zones = summary_data.get('custom_heart_rate_zones')
            if custom_zones:
                # Convert to JSONB format
                try:
                    custom_zones_json = json.dumps(custom_zones)
                except Exception as e:
                    logger.warning(f"Error serializing custom zones: {e}")
                    custom_zones_json = None
            else:
                custom_zones_json = None
            
            # Extract user_id
            user_id = summary_data.get('user_id', 'user1')  # Default fallback
            
            # Create database record
            db_record = {
                'timestamp': timestamp,
                'resting_heart_rate': resting_hr,
                'heart_rate_zones': heart_rate_zones_json,
                'custom_heart_rate_zones': custom_zones_json,
                'user_id': user_id
            }
            
            return db_record
            
        except Exception as e:
            logger.debug(f"Summary record transformation error: {e}")
            return None 