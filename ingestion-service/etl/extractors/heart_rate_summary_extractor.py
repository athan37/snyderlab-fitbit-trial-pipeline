from datetime import datetime
from typing import List, Dict, Any, Tuple

from .base_extractor import BaseExtractor, DataSchema, ExtractedData
from utils.logger import logger
from utils.fitbit_api import FITBIT_FIELDS

class HeartRateSummaryExtractor(BaseExtractor):
    """Heart rate summary data extractor - handles daily summary data only"""
    
    def __init__(self):
        super().__init__(name='activities_heart_summary')
    
    def get_schemas(self) -> List[DataSchema]:
        """Define heart rate summary schema"""
        return [
            DataSchema(
                name='activities_heart_summary',
                columns=['timestamp', 'resting_heart_rate', 'heart_rate_zones', 'custom_heart_rate_zones'],
                primary_key_columns=['timestamp'],
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
                    'custom_heart_rate_zones': value.get(FITBIT_FIELDS['CUSTOM_HEART_RATE_ZONES'])
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
                    'custom_heart_rate_zones': summary_record['custom_heart_rate_zones']
                }
                
                return final_record
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing heart rate summary record for {target_date}: {e}")
            return None
    
    def process_day_record(self, day_record: Dict[str, Any], target_date: str) -> List[Dict[str, Any]]:
        """Process a day record for a specific target date"""
        summary_record = self.process_summary_record(day_record, target_date)
        return [summary_record] if summary_record else [] 