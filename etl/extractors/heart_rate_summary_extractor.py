import random
from datetime import datetime
from typing import List, Dict, Any, Tuple

from .base_extractor import BaseExtractor, DataSchema, ExtractedData
from etl.utils.logger import logger
from etl.utils.fitbit_api import FITBIT_FIELDS
from etl.config.settings import settings

class HeartRateSummaryExtractor(BaseExtractor):
    """Heart rate summary data extractor - handles daily summary data only"""
    
    def __init__(self):
        super().__init__(name='activities_heart_summary')
    
    def get_schemas(self) -> List[DataSchema]:
        """Define heart rate summary schema"""
        return [
            DataSchema(
                name='activities_heart_summary',
                columns=['timestamp', 'resting_heart_rate', 'heart_rate_zones', 'custom_heart_rate_zones', 'user_id'],
                primary_key_columns=['timestamp', 'user_id'],
                timestamp_column='timestamp'
            )
        ]
    
    def extract(self, target_date: str) -> List[Tuple[DataSchema, List[Dict[str, Any]]]]:
        """Extract summary data for a target date"""
        try:
            # Get the day record using shift logic
            day_record = self.get_day_record(target_date)
            if not day_record:
                logger.warning(f"No heart rate summary data found for {target_date}")
                return []
            
            schema = self.get_schemas()[0]
            
            # Process summary data
            summary_record = self.process_summary_record(day_record, target_date)
            
            if summary_record:
                logger.info(f"Extracted heart rate summary data for {target_date}")
                return [(schema, [summary_record])]  # Summary is single record
            else:
                logger.warning(f"No heart rate summary data available for {target_date}")
                return []
            
        except Exception as e:
            logger.error(f"Error extracting heart rate summary data for {target_date}: {e}")
            return []
    
    def flatten_structure(self, raw_data: Dict[str, Any], target_date: str = None) -> List[Dict[str, Any]]:
        """Flatten heart rate summary data structure into records"""
        records = []
        
        try:
            # Extract heart rate day data
            hr_day = raw_data.get(FITBIT_FIELDS['HEART_RATE_DAY'], [])
            if not hr_day:
                return records
            
            # Get activities heart summary
            activities_heart = hr_day[0].get(FITBIT_FIELDS['ACTIVITIES_HEART'], [])
            if activities_heart:
                summary = activities_heart[0]
                value = summary.get(FITBIT_FIELDS['VALUE'], {})
                records.append({
                    'dateTime': target_date,  # Always use target_date for avoiding stale data
                    'resting_heart_rate': value.get(FITBIT_FIELDS['RESTING_HEART_RATE']),
                    'heart_rate_zones': value.get(FITBIT_FIELDS['HEART_RATE_ZONES']),
                    'custom_heart_rate_zones': value.get(FITBIT_FIELDS['CUSTOM_HEART_RATE_ZONES']),
                    'user_id': settings.USER_ID
                })
            
        except Exception as e:
            logger.error(f"Error flattening heart rate summary data: {e}")
        
        return records
    
    def process_summary_record(self, day_record: Dict[str, Any], target_date: str) -> Dict[str, Any]:
        """Process a day record for summary data"""
        try:
            # Flatten the structure for summary data
            records = self.flatten_structure(day_record, target_date)
            
            if records:
                # Summary data is a single record per day
                summary_record = records[0]
                
                # Always use target_date for stale cached data
                final_record = {
                    'dateTime': target_date,  # Always use target_date for stale data
                    'resting_heart_rate': summary_record['resting_heart_rate'],
                    'heart_rate_zones': summary_record['heart_rate_zones'],
                    'custom_heart_rate_zones': summary_record['custom_heart_rate_zones'],
                    'user_id': settings.USER_ID
                }
                
                return final_record
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing heart rate summary record for {target_date}: {e}")
            return None
    
    def process_day_record(self, day_record: Dict[str, Any], target_date: str) -> List[Dict[str, Any]]:
        """Process a day record for a specific target date"""
        summary_record = self.process_summary_record(day_record, target_date)
        records = [summary_record] if summary_record else []
        
        # Post-process the records (though summary data doesn't need rotation)
        records = self.post_process_day_records(records, target_date)
        
        return records
    
    def post_process_day_records(self, records: List[Dict[str, Any]], target_date: str) -> List[Dict[str, Any]]:
        """Post-process day records by generating random data for summary records"""
        if not records:
            return records
        
        try:
            # Get the data seed from settings for reproducible randomness
            data_seed = settings.DATA_SEED
            
            # Set random seed for reproducible generation
            random.seed(data_seed)
            
            processed_records = []
            for record in records:
                # Generate random heart rate zones (60-100)
                heart_rate_zones = {
                    'outOfRange': {'min': 60, 'max': 70, 'minutes': random.randint(30, 120)},
                    'fatBurn': {'min': 70, 'max': 85, 'minutes': random.randint(60, 180)},
                    'cardio': {'min': 85, 'max': 100, 'minutes': random.randint(20, 90)},
                    'peak': {'min': 100, 'max': 120, 'minutes': random.randint(5, 30)}
                }
                
                # Generate random resting heart rate (60-80)
                resting_heart_rate = random.randint(60, 80)
                
                # Generate custom heart rate zones (same structure as regular zones)
                custom_heart_rate_zones = {
                    'outOfRange': {'min': 60, 'max': 70, 'minutes': random.randint(20, 100)},
                    'fatBurn': {'min': 70, 'max': 85, 'minutes': random.randint(50, 160)},
                    'cardio': {'min': 85, 'max': 100, 'minutes': random.randint(15, 80)},
                    'peak': {'min': 100, 'max': 120, 'minutes': random.randint(3, 25)}
                }
                
                # Create processed record by spreading the original record and updating only the data fields
                processed_record = {
                    **record,  # Spread all original fields including user_id
                    'resting_heart_rate': resting_heart_rate,
                    'heart_rate_zones': heart_rate_zones,
                    'custom_heart_rate_zones': custom_heart_rate_zones
                }
                
                processed_records.append(processed_record)
            
            logger.debug(f"Generated random summary data for {len(processed_records)} records (seed: {data_seed})")
            return processed_records
            
        except Exception as e:
            logger.error(f"Error in post_process_day_records: {e}")
            return records 