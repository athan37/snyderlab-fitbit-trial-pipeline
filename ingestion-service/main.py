#!/usr/bin/env python3
"""
Fitbit ETL Pipeline - Main Entry Point

This module provides the main entry point for the Fitbit ETL pipeline.
It orchestrates the extraction, transformation, and loading of heart rate data.

Usage:
    python main.py                    # Run with default settings
    START_DATE=2025-06-01 END_DATE=2025-06-05 python main.py  # Run with custom date range
"""

import sys
import os

# Add the etl directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'etl'))

from etl.pipeline import ETLPipeline
from etl.extractors.heart_rate_extractor import HeartRateExtractor
from etl.extractors.heart_rate_summary_extractor import HeartRateSummaryExtractor
from etl.transformers.heart_rate_transformer import HeartRateTransformer
from etl.transformers.heart_rate_summary_transformer import HeartRateSummaryTransformer
from etl.loaders.heart_rate_loader import HeartRateLoader
from etl.loaders.heart_rate_summary_loader import HeartRateSummaryLoader
from etl.config.settings import settings
from etl.utils.logger import logger


def main():
    """Main ETL pipeline execution"""
    logger.info("Multi-Data-Type ETL Pipeline Started")
    
    # Log configuration
    logger.info("Pipeline Configuration:")
    logger.info(f"  • Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    logger.info(f"  • User ID: {settings.USER_ID}")
    logger.info(f"  • Batch Size: {settings.BATCH_SIZE:,}")
    logger.info(f"  • Delta Mode: {'Enabled' if settings.DELTA_MODE else 'Disabled'}")
    logger.info(f"  • UPSERT Mode: {'Enabled' if settings.UPSERT_MODE else 'Disabled'}")
    
    # Create ETL components directly
    extractors = {
        'activities_heart_intraday': HeartRateExtractor(),
        'activities_heart_summary': HeartRateSummaryExtractor()
    }
    
    transformers = {
        'activities_heart_intraday': HeartRateTransformer(),
        'activities_heart_summary': HeartRateSummaryTransformer()
    }
    
    loaders = {
        'activities_heart_intraday': HeartRateLoader(),
        'activities_heart_summary': HeartRateSummaryLoader()
    }
    
    logger.info(f"Created {len(extractors)} extractors, {len(transformers)} transformers, {len(loaders)} loaders")
    
    # Create and run pipeline with components
    pipeline = ETLPipeline(extractors=extractors, transformers=transformers, loaders=loaders)
    success = pipeline.run()
    
    if success:
        # Check if any records were actually loaded
        if pipeline.pipeline_stats['records_loaded'] > 0:
            logger.info("ETL pipeline completed successfully")
        else:
            logger.info("ETL pipeline completed successfully - no new data to process")
        sys.exit(0)
    else:
        logger.error("ETL pipeline failed")
        sys.exit(1)


if __name__ == "__main__":
    main() 