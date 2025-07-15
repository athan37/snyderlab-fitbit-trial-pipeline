# Task 0.a: Data Volume Estimation

This task involves estimating the volume of data generated in medium to large-scale clinical trials using wearable data (e.g., Fitbit). These calculations inform design decisions and local system feasibility.

---

## Objective

Estimate:
1. The total data volume for different participant counts and durations.
2. Storage needs (both uncompressed and compressed).
3. Feasibility of querying and storing time-series data on local hardware.

---

## 1. Estimating Number of Data Points

**Assumptions**:
- 4 metrics (heart_rate, steps, distance, SpO2)
- 1-second resolution
- 1 year = 60 × 60 × 24 × 365 = 31,536,000 seconds

### a. Data Points by Participant Count

| Participants | Formula                             | Total Data Points |
|--------------|--------------------------------------|-------------------|
| 1            | 4 × 31,536,000                       | 126,144,000       |
| 1,000        | 4 × 31,536,000 × 1,000               | 126,144,000,000   |
| 10,000       | 4 × 31,536,000 × 10,000              | 1,261,440,000,000 |

### b. Data Points by Duration

| Years | n=1            | n=1,000            | n=10,000             |
|-------|----------------|--------------------|----------------------|
| 1     | 126,144,000    | 126,144,000,000    | 1,261,440,000,000    |
| 2     | 252,288,000    | 252,288,000,000    | 2,522,880,000,000    |
| 5     | 630,720,000    | 630,720,000,000    | 6,307,200,000,000    |

---

## 2. Storage Requirements

**Assumption**: Each data point = 2 bytes (PostgreSQL smallint)

### a. Uncompressed Storage

- For **n=1,000**, 2 years, **3 metrics** at 1-second resolution:

Data points = (252,288,000,000 / 4) × 3 = 189,216,000,000
Bytes = 189,216,000,000 × 2 = 378,432,000,000
= ~352.44 GB


### b. Compressed Storage (e.g. TimescaleDB)

Assuming **80% compression**:
- 352 GB × 0.20 = **70.4 GB**

Assuming **90% compression**:
- 352 GB × 0.10 = **35.2 GB**

---

### i. Why Time-Series Data Compresses Well

**Compression Techniques**:
- **Delta Encoding**: Stores difference between consecutive values.
- **Run-Length Encoding**: Compresses repeated values (e.g., zero steps).
- **Columnar Storage**: Each metric is compressed separately by time chunks.

**Fitbit Suitability**:
- High compressibility due to slow-changing values (e.g., heart rate during sleep).
- Sparse data (e.g., SpO2 or steps at rest) benefits from run-length encoding.

📘 [Timescale Compression Docs](https://docs.tigerdata.com/use-timescale/latest/hypercore/compression-methods/)

---

## 3. Fitbit Metrics

### a. Metric Frequencies

| Metric     | Max Frequency |
|------------|----------------|
| Heart Rate | 1 second       |
| SpO2       | 1 minute       |

### b. Example Volume: Heart Rate Only

- **n=1,000**, 1 year:  60 × 60 × 24 × 365 × 1,000 = 31,536,000,000 data points


### c. Compressed Volume

- Uncompressed: 31.54B × 2 bytes = 63.07 GB
- Compressed @ 80%: **12.61 GB**

---

## 4. Query Efficiency for Large Data

### Challenge:
Querying full-resolution data (e.g. per second) can be expensive.

### Solution:
- Pre-aggregate and store downsampled versions (e.g., per minute, hourly).
- Use fine-grained resolution only for recent data or critical queries.

---

## 5. Hardware Feasibility

### a. Vertical Scaling (Single Machine)

Example: Apple M1 Pro
- **Memory**: 16 GB
- **Storage**: 1 TB SSD
- **CPU**: 10-core (8P + 2E)

**Limitations**:
- I/O bottlenecks
- Limited RAM for caching/querying
- Max disk throughput

### b. Horizontal Scaling (Multiple Machines)

**Key Considerations**:
- **Sharding**: Partition by user or time.
- **Aggregation**: Distributed query engine with a master node.
- **Redundancy**: Replication for load balancing and fault tolerance.

---
