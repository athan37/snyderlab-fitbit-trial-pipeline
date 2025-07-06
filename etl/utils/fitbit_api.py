import os
import json
import numpy as np
from etl.utils.logger import logger

# NOTE: This implementation uses local cached files only.
# Ensure cache files exist in the cache directory before running the pipeline.

# Fitbit API Configuration
FITBIT_DEVICE_TYPE = "fitbit/fitbit_charge_6"
FITBIT_DATA_TYPE = "intraday_heart_rate"
FITBIT_SEED = 100
FITBIT_START_DATE = "2024-01-01"
FITBIT_END_DATE = "2024-01-30"

# Cache Configuration
CACHE_FILE_NAME = "fixed_heart_rate_data.json"

# Fitbit API Field Names
FITBIT_FIELDS = {
    'HEART_RATE_DAY': 'heart_rate_day',
    'ACTIVITIES_HEART': 'activities-heart',
    'ACTIVITIES_HEART_INTRADAY': 'activities-heart-intraday',
    'DATASET': 'dataset',
    'DATETIME': 'dateTime',
    'TIME': 'time',
    'VALUE': 'value',
    'RESTING_HEART_RATE': 'restingHeartRate',
    'HEART_RATE_ZONES': 'heartRateZones',
    'CUSTOM_HEART_RATE_ZONES': 'customHeartRateZones'
}


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

def get_fitbit_device():
    """Get a wearipedia Fitbit device instance"""
    try:
        import wearipedia
        device = wearipedia.get_device(FITBIT_DEVICE_TYPE)
        logger.info(f"Fitbit device initialized: {FITBIT_DEVICE_TYPE}")
        return device
    except Exception as e:
        logger.error(f"Error initializing Fitbit device: {e}")
        return None

def generate_fixed_heart_rate_data(output_file=CACHE_FILE_NAME):
    """Generate fixed 30-day heart rate data and save to JSON file"""
    try:
        logger.info("Generating fixed heart rate data...")
        
        device = get_fitbit_device()
        if not device:
            return False
        
        # Fetch the fixed 30-day data
        params = {
            "seed": FITBIT_SEED, 
            "start_date": FITBIT_START_DATE, 
            "end_date": FITBIT_END_DATE
        }
        
        raw_data = device.get_data(FITBIT_DATA_TYPE, params)
        
        # Save to JSON file
        with open(output_file, 'w') as f:
            json.dump(raw_data, f, indent=2, cls=NumpyEncoder)
        
        logger.info(f"Fixed heart rate data saved to {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error generating fixed heart rate data: {e}")
        return False

def load_cached_data(cache_file, name):
    """Load cached data from JSON file. If missing, generate it and then load."""
    try:
        if not os.path.exists(cache_file):
            logger.warning(f"Cache file {cache_file} not found. Generating new cache file...")
            if not generate_fixed_heart_rate_data(cache_file):
                logger.error(f"Failed to generate cache file {cache_file}.")
                return None
        with open(cache_file, 'r') as f:
            cached_data = json.load(f)
        logger.info(f"Loaded cached {name} data from {cache_file}")
        return cached_data
    except Exception as e:
        logger.error(f"Error loading cached data: {e}")
        return None 