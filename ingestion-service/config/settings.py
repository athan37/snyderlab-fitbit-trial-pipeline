import os

class Settings:
    """Configuration settings for the ETL pipeline"""
    
    def __init__(self):
        # Database Configuration
        self.DB_HOST = os.getenv('DB_HOST', 'localhost')
        self.DB_PORT = os.getenv('DB_PORT', '5432')
        self.DB_NAME = os.getenv('DB_NAME', 'fitbit-hr')
        self.DB_USER = os.getenv('DB_USER', 'postgres')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
        
        # User Configuration
        self.USER_ID = os.getenv('USER_ID', 'default_user')
        
        # Data Configuration
        self.DATA_SEED = int(os.getenv('DATA_SEED', '0'))
        
        # ETL Configuration
        self.BATCH_SIZE = int(os.getenv('BATCH_SIZE', '10000'))
        
        # Delta Pipeline Configuration
        self.START_DATE = os.getenv('START_DATE')  # Only set if explicitly provided
        self.END_DATE = os.getenv('END_DATE')  # Only set if explicitly provided
        self.DELTA_MODE = os.getenv('DELTA_MODE', 'true').lower() == 'true'  # Enable delta loading
        self.UPSERT_MODE = os.getenv('UPSERT_MODE', 'true').lower() == 'true'  # Use UPSERT instead of INSERT
        
        # Logging
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
        self.LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
    
    @property
    def DATABASE_URL(self) -> str:
        """Get database URL for SQLAlchemy"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    def validate(self) -> bool:
        """Validate required settings"""
        required_settings = [
            self.DB_HOST,
            self.DB_NAME,
            self.DB_USER,
            self.DB_PASSWORD,
            self.USER_ID
        ]
        
        missing = [setting for setting in required_settings if not setting]
        if missing:
            raise ValueError(f"Missing required settings: {missing}")
        
        return True

# Global settings instance
settings = Settings() 