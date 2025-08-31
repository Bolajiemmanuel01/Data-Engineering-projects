# Data Engineering Projects

Welcome to the Data Engineering Projects repository! This repository contains a collection of end-to-end data engineering projects, each demonstrating different aspects of data ingestion, transformation, orchestration, analytics, and visualization using modern data engineering tools and best practices.

## Repository Structure

```
Data-Engineering-projects/
│
├── crypto-price-pipeline/         # Project: Crypto Price Data Pipeline
│   ├── airflow/                   # Airflow DAGs and configs
│   ├── db/                        # Database scripts and SQL
│   ├── dbt/                       # dbt transformation project
│   ├── grafana/                   # Grafana provisioning for dashboards
│   └── viz/                       # PowerBI and other visualization assets
│
├── dags/                          # Additional DAGs for various projects
│   ├── crypto-price-pipeline/
│   ├── nyc-taxi-etl/
│   └── online-retail-etl/
│
├── docs/                          # Documentation and dbt docs for each project
│
├── logs/                          # Airflow and pipeline logs
│
├── nyc-taxi-etl/                  # Project: NYC Taxi Data ETL
│   ├── dags/
│   ├── data/
│   └── README.md
│
├── online-retail-etl/             # Project: Online Retail Data ETL
│   ├── dags/
│   ├── data/
│   ├── logs/
│   ├── scripts/
│   └── online_retail_dbt/
│
├── plugins/                       # Custom Airflow plugins (if any)
│
├── docker-compose.yaml            # Main Docker Compose file for orchestration
└── README.md                      # This file
```

## Projects Overview

### 1. Crypto Price Pipeline
- **Goal:** Ingest, transform, and visualize cryptocurrency price data.
- **Tech Stack:** Airflow, dbt, PostgreSQL, Grafana, PowerBI
- **Features:**
  - Automated data ingestion with Airflow
  - Data transformation with dbt
  - Analytics and dashboards with Grafana and PowerBI

### 2. NYC Taxi ETL
- **Goal:** ETL pipeline for NYC Taxi trip data.
- **Tech Stack:** Airflow, Python, SQL
- **Features:**
  - Data extraction, cleaning, and loading
  - Modular DAGs for batch processing

### 3. Online Retail ETL
- **Goal:** ETL and analytics for online retail datasets.
- **Tech Stack:** Airflow, dbt, Python
- **Features:**
  - Data ingestion and transformation
  - dbt models for analytics

## Getting Started

### Prerequisites
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- (Optional) [PowerBI Desktop](https://powerbi.microsoft.com/)

### Setup Instructions
1. **Clone the repository:**
	```sh
	git clone https://github.com/Bolajiemmanuel01/Data-Engineering-projects.git
	cd Data-Engineering-projects
	```
2. **Start the services:**
	```sh
	docker-compose up --build
	```
	This will start Airflow, databases, and other services as defined in `docker-compose.yaml`.

3. **Access Airflow UI:**
	- Navigate to [http://localhost:8080](http://localhost:8080) (default credentials: `airflow/airflow`)

4. **Access Grafana:**
	- Navigate to [http://localhost:3000](http://localhost:3000) (default credentials: `admin/admin`)

5. **PowerBI Dashboards:**
	- Open the `.pbix` files in the `viz/` folder using PowerBI Desktop.

## Project Details

Each project folder contains its own README with specific setup, DAGs, and data sources. Refer to those for project-specific instructions.

## Contributing

Contributions are welcome! Please open issues or submit pull requests for improvements, bug fixes, or new projects.

## License

This repository is licensed under the MIT License. See the `LICENSE` file for details.

## Author

Bolaji Emmanuel
