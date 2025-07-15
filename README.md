# Heart Rate Data Pipeline with TimescaleDB

A production-ready ETL pipeline for ingesting Fitbit heart rate data using **TimescaleDB**, Docker, and Python. Features modular ETL architecture with delta processing, multi-user support, and reproducible data seeding. Includes a FastAPI backend and React frontend for data visualization.


# Dynamic query range support
<img width="1547" height="899" alt="image" src="https://github.com/user-attachments/assets/91859beb-5297-4339-a627-a04d2c8316ff" />

<img width="1547" height="899" alt="image" src="https://github.com/user-attachments/assets/7344b1ce-b26d-4925-b8b2-13b69a4984c3" />

<img width="1547" height="899" alt="image" src="https://github.com/user-attachments/assets/ddffa823-41cd-414f-9f22-0ea738b31f1e" />

<img width="1547" height="899" alt="image" src="https://github.com/user-attachments/assets/6314e1ab-e927-46bc-9c92-dd8a1d930056" />


# Detailed Monitoring
<img width="1381" height="828" alt="image" src="https://github.com/user-attachments/assets/bf15481f-2a94-4818-afdb-77b2e5b1dd8b" />
<img width="1381" height="828" alt="image" src="https://github.com/user-attachments/assets/8af50b2a-810f-4617-8945-21b97348a0de" />




## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  ETL Pipeline   │───▶│   TimescaleDB   │───▶│   FastAPI +     │
│   (Simulated)   │    │   (Extract/     │    │   (Hypertable)  │    │   React App     │
└─────────────────┘    │    Transform/   │    └─────────────────┘    └─────────────────┘
                       │     Load)       │             
                       |─────────────────|
```
