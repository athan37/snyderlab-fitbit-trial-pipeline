from datetime import datetime
from typing import List, Dict, Any, Tuple
from .base_extractor import BaseExtractor, DataSchema
from etl.utils.logger import logger
from etl.utils.fitbit_api import FITBIT_FIELDS
from etl.config.settings import settings

class HeartRateExtractor(BaseExtractor):
    """Heart rate data extractor - handles intraday data only"""
    
    def __init__(self):
        super().__init__(name='activities_heart_intraday')
    
    def get_schemas(self) -> List[DataSchema]:
        """Define heart rate schema"""
        return [
            DataSchema(
                name='activities_heart_intraday',
                columns=['timestamp', 'value', 'user_id'],
                primary_key_columns=['timestamp', 'user_id'],
                timestamp_column='timestamp'
            )
        ]
    
    def extract(self, target_date: str) -> List[Tuple[DataSchema, List[Dict[str, Any]]]]:
        """Extract intraday heart rate data for a target date"""
        try:
            # Get the day record using shift logic
            day_record = self.get_day_record(target_date)
            if not day_record:
                logger.warning(f"No heart rate data found for {target_date}")
                return []
            
            schema = self.get_schemas()[0]
            
            # Process intraday data
            intraday_records = self.process_day_record(day_record, target_date)
            
            if intraday_records:
                logger.info(f"Extracted {len(intraday_records)} intraday heart rate records for {target_date}")
                return [(schema, intraday_records)]
            else:
                logger.warning(f"No heart rate intraday data available for {target_date}")
                return []
            
        except Exception as e:
            logger.error(f"Error extracting heart rate data for {target_date}: {e}")
            return []
    
    def flatten_structure(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten heart rate data structure into individual records"""
        records = []
        
        try:
            # Extract heart rate day data
            hr_day = raw_data.get(FITBIT_FIELDS['HEART_RATE_DAY'], [])
            if not hr_day:
                return records
            
            # Get intraday dataset
            intraday = hr_day[0].get(FITBIT_FIELDS['ACTIVITIES_HEART_INTRADAY'], {})
            dataset = intraday.get(FITBIT_FIELDS['DATASET'], [])
            
            # Create individual records
            for record in dataset:
                if isinstance(record, dict):
                    time_str = record.get(FITBIT_FIELDS['TIME'])
                    value = record.get(FITBIT_FIELDS['VALUE'])
                    if time_str and value is not None:
                        records.append({
                            'time': time_str,
                            'value': value
                        })
            
            logger.debug(f"Flattened {len(records)} heart rate records")
            
        except Exception as e:
            logger.error(f"Error flattening heart rate data: {e}")
        
        return records
    
    def process_day_record(self, day_record: Dict[str, Any], target_date: str) -> List[Dict[str, Any]]:
        """Process a day record for a specific target date"""
        try:
            # Flatten the structure for intraday data
            records = self.flatten_structure(day_record)
            
            # Output raw data format - always use target_date for generating synthetic data
            final_records = []
            for record in records:
                final_records.append({
                    'dateTime': target_date,  # Always use target_date for avoding stale data
                    'time': record['time'],
                    'value': record['value'],
                    'user_id': settings.USER_ID
                })
            
            # Post-process the records (rotate time/value pairs)
            final_records = self.post_process_day_records(final_records, target_date)
            
            return final_records
            
        except Exception as e:
            logger.error(f"Error processing heart rate day record for {target_date}: {e}")
            return []
    
    def post_process_day_records(self, records: List[Dict[str, Any]], target_date: str) -> List[Dict[str, Any]]:
        """Post-process day records by applying seed-based value randomization while keeping time patterns consistent"""
        if not records:
            return records
        
        try:
            # Get the data seed from settings
            data_seed = settings.DATA_SEED
            
            if data_seed == 0:
                # No modification needed
                return records
            
            # Use the seed to create a deterministic random number generator
            import random
            random.seed(data_seed)
            
            # Create modified records with randomized values but consistent time patterns
            modified_records = []
            for record in records:
                # Keep the original time pattern
                original_value = record['value']
                
                # Apply seed-based randomization to the heart rate value
                # Add/subtract a small random amount (±5 BPM) to create variation
                variation = random.uniform(-5, 5)
                new_value = max(50, min(200, original_value + variation))  # Keep within realistic range
                
                # Create new record with modified value but same time
                modified_record = {
                    **record,  # Spread all original fields including user_id and time
                    'value': round(new_value, 2)  # Round to 2 decimal places
                }
                modified_records.append(modified_record)
            
            logger.debug(f"Applied seed-based value randomization to {len(records)} records (seed: {data_seed})")
            return modified_records
            
        except Exception as e:
            logger.error(f"Error in post_process_day_records: {e}")
            return records
    
    def _get_base_date_from_record(self, day_record: Dict[str, Any]) -> str:
        """Extract the base date from the heart rate day record"""
        try:
            hr_day = day_record.get(FITBIT_FIELDS['HEART_RATE_DAY'], [])
            if hr_day:
                activities_heart = hr_day[0].get(FITBIT_FIELDS['ACTIVITIES_HEART'], [])
                if activities_heart:
                    return activities_heart[0].get(FITBIT_FIELDS['DATETIME'], '2024-01-01')
            return '2024-01-01'
        except Exception as e:
            logger.error(f"Error extracting base date: {e}")
            return '2024-01-01'
    
 