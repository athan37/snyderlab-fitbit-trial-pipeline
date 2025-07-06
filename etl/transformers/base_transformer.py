from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime
from dataclasses import dataclass

from ..extractors.base_extractor import ExtractedData, DataSchema
from etl.utils.logger import logger

if TYPE_CHECKING:
    from ..loaders.base_loader import BaseLoader

@dataclass
class TransformedData:
    """Container for transformed data with final schema"""
    schema: DataSchema
    records: List[Dict[str, Any]]
    transformation_stats: Dict[str, Any]

class BaseTransformer(ABC):
    """Abstract base class for data transformation"""
    
    def __init__(self, name: str):
        self.name = name
        self.transformation_stats = {
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'missing_values_filled': 0
        }
    
    @abstractmethod
    def transform_records(self, extracted_data: ExtractedData) -> TransformedData:
        """Transform extracted data into final format"""
        pass
    
    def transform_records_with_filtering(self, extracted_data: ExtractedData, 
                                       loader: Optional['BaseLoader'] = None) -> TransformedData:
        """Transform records and apply delta filtering in the correct order"""
        try:
            # Step 1: Transform the data first
            transformed_data = self.transform_records(extracted_data)
            
            # Step 2: Apply delta filtering if loader is available
            if loader and transformed_data.records:
                last_timestamp = loader.get_last_processed_timestamp()
                if last_timestamp:
                    filtered_records = self.filter_already_processed_records(
                        transformed_data.records, last_timestamp
                    )
                    # Update the transformed data with filtered records
                    transformed_data.records = filtered_records
                    logger.info(f"Filtered {len(filtered_records):,} new records from {len(transformed_data.records):,} total")
                else:
                    logger.info("No previous timestamp found, processing all records")
            else:
                logger.warning(f"No loader available for {self.name}, skipping filtering")
            
            return transformed_data
            
        except Exception as e:
            logger.error(f"Error in transform_records_with_filtering: {e}")
            return TransformedData(
                schema=extracted_data.schema,
                records=[],
                transformation_stats=self.transformation_stats.copy()
            )
    
    def filter_already_processed_records(self, records: List[Dict[str, Any]], 
                                       last_processed_timestamp: Optional[str]) -> List[Dict[str, Any]]:
        """Filter out records that have already been processed"""
        if not last_processed_timestamp:
            logger.info("No previous timestamp found, processing all records")
            return records
        
        try:
            last_timestamp = datetime.fromisoformat(last_processed_timestamp.replace('Z', '+00:00'))
            filtered_records = []
            
            for record in records:
                # Check if record has timestamp field
                if 'timestamp' not in record:
                    logger.warning(f"Record missing timestamp field: {record}")
                    continue
                
                # Get record timestamp
                record_timestamp = record['timestamp']
                if isinstance(record_timestamp, str):
                    record_timestamp = datetime.fromisoformat(record_timestamp.replace('Z', '+00:00'))
                elif isinstance(record_timestamp, datetime):
                    pass  # Already a datetime object
                else:
                    logger.warning(f"Invalid timestamp format: {record_timestamp}")
                    continue
                
                # Ensure both timestamps are timezone-aware for comparison
                if record_timestamp.tzinfo is None:
                    record_timestamp = record_timestamp.replace(tzinfo=last_timestamp.tzinfo)
                if last_timestamp.tzinfo is None:
                    last_timestamp = last_timestamp.replace(tzinfo=record_timestamp.tzinfo)
                
                # Only include records newer than the last processed timestamp
                if record_timestamp > last_timestamp:
                    filtered_records.append(record)
            
            logger.info(f"Filtered {len(filtered_records):,} new records from {len(records):,} total")
            return filtered_records
            
        except Exception as e:
            logger.error(f"Error filtering records: {e}")
            return records
    
    def reset_stats(self):
        """Reset transformation statistics"""
        self.transformation_stats = {
            'total_records': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'missing_values_filled': 0
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get transformation statistics"""
        return self.transformation_stats.copy() 