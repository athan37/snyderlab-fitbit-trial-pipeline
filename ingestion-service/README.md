# Fitbit ETL Pipeline

A robust, production-ready ETL (Extract, Transform, Load) pipeline for processing Fitbit heart rate data into TimescaleDB.

## 🏗️ Architecture

The pipeline follows ETL best practices with separate concerns:

```
ingestion-service/
├── config/           # Configuration management
├── utils/            # Shared utilities (logging, database)
├── etl/              # Core ETL components
│   ├── extractor.py  # Data extraction from APIs
│   ├── transformer.py # Data transformation & validation
│   ├── loader.py     # Database loading operations
│   └── pipeline.py   # Main ETL orchestrator
├── tests/            # Unit tests
├── main.py           # Entry point
└── requirements.txt  # Dependencies
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file:
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=password
MAX_RECORDS=0  # 0 = no limit
BATCH_SIZE=10000
TEST_MODE=false
```

### 3. Run the Pipeline

**Test Mode (no database):**
```bash
TEST_MODE=true python main.py
```

**Production Mode:**
```bash
python main.py
```

**With Record Limit:**
```bash
MAX_RECORDS=1000 python main.py
```

## 📊 Features

### ✅ **Extract (E)**
- **API Integration**: Fetches data from wearipedia Fitbit API
- **Progress Tracking**: Real-time progress bars
- **Error Handling**: Robust error handling and retry logic
- **Data Validation**: Pre-extraction validation

### ✅ **Transform (T)**
- **Data Cleaning**: Validates heart rate ranges (30-220 BPM)
- **Type Conversion**: Handles numpy types and data formats
- **Quality Checks**: Comprehensive data quality validation
- **Delta Loading**: Filters out already processed records

### ✅ **Load (L)**
- **Batch Processing**: Efficient batch loading (10k records per batch)
- **Verification**: Each batch is verified after insertion
- **Progress Tracking**: Real-time loading progress
- **TimescaleDB**: Optimized for time-series data

### ✅ **Monitoring & Logging**
- **Comprehensive Logging**: Detailed logs at every step
- **Performance Metrics**: Timing and statistics
- **Error Reporting**: Clear error messages and debugging info

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | Database host |
| `DB_PORT` | `5432` | Database port |
| `DB_NAME` | `postgres` | Database name |
| `DB_USER` | `postgres` | Database user |
| `DB_PASSWORD` | `password` | Database password |
| `MAX_RECORDS` | `0` | Record limit (0 = no limit) |
| `BATCH_SIZE` | `10000` | Batch size for loading |
| `TEST_MODE` | `false` | Test mode (skip database) |
| `LOG_LEVEL` | `INFO` | Logging level |

## 🧪 Testing

Run unit tests:
```bash
python -m unittest discover tests/
```

Run specific test:
```bash
python -m unittest tests.test_extractor
```

## 📈 Performance

### Typical Performance Metrics:
- **Extraction**: ~5-10 seconds for 1 day of data
- **Transformation**: ~1-2 seconds for 2.6M records
- **Loading**: ~30-60 seconds for 2.6M records (with verification)
- **Total Pipeline**: ~1-2 minutes for full day ingestion

### Scalability:
- **Batch Size**: Configurable (default: 10,000 records)
- **Memory Efficient**: Processes data in chunks
- **Database Optimized**: Uses TimescaleDB hypertables

## 🔍 Monitoring

### Pipeline Statistics
The pipeline provides detailed statistics:
```
📊 Pipeline Statistics:
  • Total time: 45.23s
  • Extraction time: 8.45s
  • Transformation time: 1.23s
  • Loading time: 35.55s
  • Records processed: 2,592,000
  • Records loaded: 2,592,000
  • Success: ✅ Yes
```

### Database Verification
- Pre-loading checks
- Batch-by-batch verification
- Post-loading validation
- Record count verification

## 🛠️ Development

### Adding New Data Sources
1. Extend `DataExtractor` class
2. Add new extraction methods
3. Update configuration
4. Add tests

### Adding New Transformations
1. Extend `DataTransformer` class
2. Add validation rules
3. Update transformation logic
4. Add tests

### Adding New Destinations
1. Extend `DataLoader` class
2. Add new loading methods
3. Update configuration
4. Add tests

## 🚨 Error Handling

The pipeline includes comprehensive error handling:
- **Connection Failures**: Automatic retry logic
- **Data Validation**: Invalid records are logged and skipped
- **Batch Failures**: Failed batches are retried
- **Verification Failures**: Clear error reporting

## 📝 Logging

Log levels and formats:
- **INFO**: General progress and statistics
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures
- **DEBUG**: Detailed debugging information

## 🔄 Scheduling

For automated daily ingestion, use cron:
```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/ingestion-service && python main.py
```

## 📚 API Reference

### ETLPipeline
Main orchestrator class that coordinates the entire ETL process.

### DataExtractor
Handles data extraction from external APIs and sources.

### DataTransformer
Manages data transformation, validation, and cleaning operations.

### DataLoader
Handles database operations and batch loading with verification.

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass

## 📄 License

This project is part of the Snyder data pipeline. 