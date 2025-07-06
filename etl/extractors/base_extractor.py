from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
import os
from dataclasses import dataclass

from etl.utils.logger import logger
from etl.utils.fitbit_api import load_cached_data

@dataclass
class DataSchema:
    """Schema definition for extracted data"""
    name: str
    columns: List[str]
    primary_key_columns: List[str]  # Single composite primary key (e.g., ['timestamp', 'metric_type'])
    timestamp_column: str = 'timestamp'

@dataclass
class ExtractedData:
    """Container for extracted data with schema"""
    schema: DataSchema
    records: List[Dict[str, Any]]



class BaseExtractor(ABC):
    """Abstract base class for data extraction"""
    
    def __init__(self, name: str, cache_dir: str = "cache"):
        self.name = name
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, f"{name}_data.json")
        self.cached_data = None
        self.base_date = "2024-01-01"  # Base date for shift logic
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
    
    @abstractmethod
    def get_schemas(self) -> List[DataSchema]:
        """Define schema for this data type"""
        pass
    
    @abstractmethod
    def extract(self, target_date: str) -> List[Tuple[DataSchema, List[Dict[str, Any]]]]:
        """Extract data for a given date - returns list of (schema, records) tuples"""
        pass
    
    @abstractmethod
    def flatten_structure(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten the raw data structure into records"""
        pass
    
    @abstractmethod
    def process_day_record(self, day_record: Dict[str, Any], target_date: str) -> List[Dict[str, Any]]:
        """Process a day record for a specific target date - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def post_process_day_records(self, records: List[Dict[str, Any]], target_date: str) -> List[Dict[str, Any]]:
        """Post-process day records (e.g., rotate time/value pairs) - to be implemented by subclasses"""
        pass
    
    def calculate_shift(self, target_date: str) -> int:
        """Calculate the shift days from base date to target date"""
        target_dt = datetime.strptime(target_date, "%Y-%m-%d").date()
        base_dt = datetime.strptime(self.base_date, "%Y-%m-%d").date()
        shift = (target_dt - base_dt).days % 30
        return shift
    
    def get_day_record(self, target_date: str) -> Optional[Dict[str, Any]]:
        """Get the day record from cached data using shift logic"""
        try:
            # Load cached data if not already loaded
            if self.cached_data is None:
                self.cached_data = load_cached_data(self.cache_file, self.name)
                if self.cached_data is None:
                    logger.error(f"Failed to load cached {self.name} data")
                    return None
            
            shift = self.calculate_shift(target_date)
            day_record = self.cached_data[shift]
            return day_record
            
        except Exception as e:
            logger.error(f"Error getting day record for {target_date}: {e}")
            return None
    
    def extract_for_date(self, target_date: str) -> List[Dict[str, Any]]:
        """Extract data for a specific date using cached data and shift logic"""
        try:
            # Get the day record using shift logic
            day_record = self.get_day_record(target_date)
            if not day_record:
                return []
            
            # Process the day record (implemented by subclasses)
            records = self.process_day_record(day_record, target_date)
            
            return records
            
        except Exception as e:
            logger.error(f"Error extracting {self.name} data for {target_date}: {e}")
            return []
    
    def process_day_record(self, day_record: Dict[str, Any], target_date: str) -> List[Dict[str, Any]]:
        """Process a day record into individual data records (implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement process_day_record") 

    def get_defaulted_timestamp(self, date_str: str, user_start_date: str = None) -> str:
        """Return date_str if present, else user_start_date, else default to 2025-06-01"""
        if date_str:
            return date_str
        if user_start_date:
            return user_start_date
        return "2025-06-01" 