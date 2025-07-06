from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List
import time

from etl.config.settings import settings
from etl.utils.logger import logger

# Import the new base classes and implementations
from .extractors.base_extractor import BaseExtractor, DataSchema
from .transformers.base_transformer import BaseTransformer, TransformedData
from .loaders.base_loader import BaseLoader

# Import specific implementations
from .extractors.heart_rate_extractor import HeartRateExtractor
from .extractors.heart_rate_summary_extractor import HeartRateSummaryExtractor
from .transformers.heart_rate_transformer import HeartRateTransformer
from .loaders.heart_rate_loader import HeartRateLoader
from .transformers.heart_rate_summary_transformer import HeartRateSummaryTransformer
from .loaders.heart_rate_summary_loader import HeartRateSummaryLoader

class ETLPipeline:
    """Main ETL pipeline orchestrator with support for multiple data types"""
    
    def __init__(self, extractors: Dict[str, BaseExtractor] = None, 
                 transformers: Dict[str, BaseTransformer] = None,
                 loaders: Dict[str, BaseLoader] = None):
        """
        Initialize ETL pipeline with components
        
        Args:
            extractors: Dictionary of extractors by table name
            transformers: Dictionary of transformers by table name  
            loaders: Dictionary of loaders by table name
        """
        # Initialize components (can be passed in or use defaults)
        self.extractors = extractors or {}
        self.transformers = transformers or {}
        self.loaders = loaders or {}
        
        # Pipeline statistics
        self.pipeline_stats = {
            'total_time': 0.0,
            'extraction_time': 0.0,
            'transformation_time': 0.0,
            'loading_time': 0.0,
            'records_processed': 0,
            'records_loaded': 0,
            'success': False
        }
    
    def run_pre_ingestion_checks(self) -> bool:
        """Run pre-ingestion checks for all data types"""
        try:
            logger.info("Running pre-ingestion checks...")
            
            # Check database connections and table setup
            logger.info("Checking database setup for all loaders...")
            for name, loader in self.loaders.items():
                logger.info(f"Setting up database for {name}...")
                if not loader.setup_database():
                    logger.error(f"❌ Database setup FAILED for {name}")
                    logger.error("Pipeline cannot continue without proper database setup")
                    return False
                else:
                    logger.info(f"✅ Database setup PASSED for {name}")
            
            # Check extractor availability
            logger.info("Checking extractor availability...")
            for name, extractor in self.extractors.items():
                if not extractor:
                    logger.error(f"❌ Extractor not available for {name}")
                    return False
                else:
                    logger.info(f"✅ Extractor available for {name}")
            
            logger.info("✅ All pre-ingestion checks passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Pre-ingestion checks error: {e}")
            logger.error("Pipeline cannot start due to pre-ingestion check failure")
            return False
    
    def determine_date_range(self) -> Tuple[str, str]:
        """Determine the date range for processing"""
        now = datetime.now()
        # Custom date range takes precedence if both are set and non-empty
        if settings.START_DATE and settings.END_DATE and settings.START_DATE.strip() and settings.END_DATE.strip():
            # Clean the date strings to remove any timezone information
            start_date_clean = settings.START_DATE.strip().split()[0]  # Take only the date part
            end_date_clean = settings.END_DATE.strip().split()[0]  # Take only the date part
            logger.info(f"Using custom date range: {start_date_clean} to {end_date_clean}")
            return start_date_clean, end_date_clean

        # Get the last processed date from all loaders to find the earliest missing date
        earliest_next_date = None
        for loader_name, loader in self.loaders.items():
            last_processed_timestamp = loader.get_last_processed_timestamp()
            if last_processed_timestamp:
                if isinstance(last_processed_timestamp, str):
                    last_processed_timestamp = datetime.fromisoformat(last_processed_timestamp.replace('Z', '+00:00'))
                next_date = last_processed_timestamp.date() + timedelta(days=1)
                if next_date > now.date():
                    logger.info(f"Next date {next_date} for {loader_name} is in the future, skipping...")
                    continue
                if earliest_next_date is None or next_date < earliest_next_date:
                    earliest_next_date = next_date
                    logger.info(f"Found missing data for {loader_name} at date: {earliest_next_date}")

        # If no data in database, start from configured start date (if any), else 30 days ago
        if earliest_next_date:
            start_date = earliest_next_date.strftime('%Y-%m-%d')
            # Process from earliest missing date up to today
            end_date = now.strftime('%Y-%m-%d')
            logger.info(f"Processing missing days from {start_date} to {end_date}")
        else:
            # No data in database, start from configured start date if provided, else 30 days ago
            if settings.START_DATE:
                start_date = settings.START_DATE
                end_date = now.strftime('%Y-%m-%d')
                logger.info(f"Starting from configured date: {start_date} to {end_date}")
            else:
                # Default to 30 days ago when no data exists
                start_date = (now - timedelta(days=30)).strftime('%Y-%m-%d')
                end_date = now.strftime('%Y-%m-%d')
                logger.info(f"No previous data found. Loading last 30 days from {start_date} to {end_date}")
        return start_date, end_date
    
    def execute_pipeline(self, start_date: str, end_date: str) -> bool:
        """Execute the ETL pipeline for all data types"""
        try:
            logger.info("Starting ETL pipeline (multi-data-type)...")
            
            # Step 1: Extract data for all data types
            start_time = time.time()
            all_schema_records: List[Tuple[DataSchema, List[Dict[str, Any]]]] = []
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            num_days = (end_dt - start_dt).days + 1
            
            for i in range(num_days):
                target_date = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
                # Extract data for each data type
                for name, extractor in self.extractors.items():
                    schema_records_list = extractor.extract(target_date)
                    all_schema_records.extend(schema_records_list)
            
            extraction_time = time.time() - start_time
            if not all_schema_records:
                logger.error("Extraction failed - no data retrieved")
                return False
            logger.info(f"Extraction completed in {extraction_time:.2f}s")
            total_records = sum(len(records) for _, records in all_schema_records)
            logger.info(f"Extracted {total_records:,} total records across {len(all_schema_records)} schema/record pairs")
            
            # Step 2: Transform data for all schema/record pairs (with built-in filtering)
            start_time = time.time()
            all_transformed_data: List[TransformedData] = []
            
            for schema, records in all_schema_records:
                # Find appropriate transformer based on schema name
                transformer_key = schema.name
                if transformer_key not in self.transformers:
                    logger.warning(f"No transformer found for {transformer_key}, skipping")
                    continue
                
                transformer = self.transformers[transformer_key]
                
                # Create extracted data object for transformation
                from .extractors.base_extractor import ExtractedData
                extracted_data = ExtractedData(
                    schema=schema,
                    records=records
                )
                
                # Transform the data (transformers now handle their own filtering)
                transformed_data = transformer.transform_records_with_filtering(
                    extracted_data, 
                    self.loaders.get(transformer_key)
                )
                
                if transformed_data.records:
                    all_transformed_data.append(transformed_data)
                else:
                    logger.info(f"No new {transformer_key} records to process after delta check")
            
            transformation_time = time.time() - start_time
            if not all_transformed_data:
                logger.info("No new records to process after delta check. Exiting.")
                # Update pipeline statistics for successful "no new data" case
                self.pipeline_stats.update({
                    'extraction_time': extraction_time,
                    'transformation_time': transformation_time,
                    'loading_time': 0.0,
                    'records_processed': total_records,
                    'records_loaded': 0,
                    'success': True
                })
                return True
            
            logger.info(f"Transformation completed in {transformation_time:.2f}s")
            
            # Step 3: Load data for all transformed data
            start_time = time.time()
            loading_success = True
            
            for transformed_data in all_transformed_data:
                name = transformed_data.schema.name
                if name not in self.loaders:
                    logger.warning(f"No loader found for {name}, skipping")
                    continue
                
                loader = self.loaders[name]
                success = loader.load_records(transformed_data, settings.UPSERT_MODE)
                if not success:
                    logger.error(f"Loading failed for {name}")
                    loading_success = False
                    break
                
                # Verify loading
                if not loader.verify_loading(len(transformed_data.records)):
                    logger.warning(f"Loading verification failed for {name}")
            
            loading_time = time.time() - start_time
            if not loading_success:
                return False
            
            logger.info(f"Loading completed in {loading_time:.2f}s")
            
            # Update pipeline statistics
            total_loaded = sum(len(data.records) for data in all_transformed_data)
            self.pipeline_stats.update({
                'extraction_time': extraction_time,
                'transformation_time': transformation_time,
                'loading_time': loading_time,
                'records_processed': total_records,
                'records_loaded': total_loaded,
                'success': True
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Pipeline execution error: {e}")
            self.pipeline_stats['success'] = False
            return False
    
    def _log_pipeline_stats(self):
        """Log pipeline statistics"""
        stats = self.pipeline_stats
        logger.info("Pipeline Statistics:")
        logger.info(f"  • Total time: {stats['total_time']:.2f}s")
        logger.info(f"  • Extraction time: {stats['extraction_time']:.2f}s")
        logger.info(f"  • Transformation time: {stats['transformation_time']:.2f}s")
        logger.info(f"  • Loading time: {stats['loading_time']:.2f}s")
        logger.info(f"  • Records processed: {stats['records_processed']:,}")
        logger.info(f"  • Records loaded: {stats['records_loaded']:,}")
        logger.info(f"  • Success: {'Yes' if stats['success'] else 'No'}")
    
    def run(self) -> bool:
        """Run the complete ETL pipeline"""
        start_time = time.time()
        
        try:
            # Run pre-ingestion checks
            if not self.run_pre_ingestion_checks():
                return False
            
            # Determine date range
            start_date, end_date = self.determine_date_range()
            
            if not start_date or not end_date:
                logger.info("No data to process. Exiting.")
                return True
            
            logger.info(f"Processing data for: {start_date} to {end_date}")
            
            # Execute the pipeline
            success = self.execute_pipeline(start_date, end_date)
            
            # Calculate total time
            total_time = time.time() - start_time
            self.pipeline_stats['total_time'] = total_time
            
            # Log final statistics
            self._log_pipeline_stats()
            
            return self.pipeline_stats['success']
            
        except Exception as e:
            logger.error(f"Pipeline execution error: {e}")
            return False 