# Data Engineering Projects

Welcome to the Data Engineering Projects repository! This repository contains a collection of end-to-end data engineering projects, each demonstrating different aspects of data ingestion, transformation, orchestration, analytics, and visualization using modern data engineering tools and best practices.

## Repository Structure




```
Data-Engineering-projects/
│
├── crypto-price-pipeline/        # End-to-end crypto data workflows and assets
│   ├── airflow/                  # Airflow DAGs for orchestration
│   ├── db/                       # Database scripts and SQL
│   ├── dbt/                      # dbt models for transformation
│   ├── grafana/                  # Grafana dashboard provisioning
│   ├── viz/                      # PowerBI and other visualization files
│   ├── LICENSE                   # Project license
│   └── README.md                 # Project documentation
│
├── dags/                        # Centralized DAGs for all projects
│   ├── crypto-price-pipeline/    # DAGs for crypto project
│   ├── nyc-taxi-etl/            # DAGs for NYC taxi project
│   └── online-retail-etl/       # DAGs for online retail project
│
├── docs/                        # dbt and project documentation
│   ├── crypto-price-pipeline/    # dbt docs for crypto project
│   └── online-retail-etl/       # dbt docs for online retail project
│
├── earthquakes-rt/   # In Development
│   ├── airflow/                  # Airflow DAGs
│   ├── db/                       # Database scripts
│   ├── docker/                   # Docker setup
│   ├── spark/                    # Spark jobs
│   ├── .env.example              # Environment variable example
│   └── README.md                 # Project documentation
│
├── logs/                        # Pipeline and Airflow logs
│   ├── dag_id=crypto_price_pipeline/   # Logs for crypto pipeline runs
│   ├── dag_id=nyc_taxi_pipeline/       # Logs for NYC taxi pipeline runs
│   ├── dag_id=online_retail_ingest/    # Logs for online retail pipeline runs
│   ├── dag_processor_manager/          # Airflow DAG processor logs
│   └── scheduler/                      # Airflow scheduler logs
│
├── nyc-taxi-etl/                # NYC taxi ETL project
│   ├── dags/                     # Project-specific DAGs
│   ├── data/                     # Raw and processed data
│   ├── link.txt                  # Data source links/info
│   └── README.md                 # Project documentation
│
├── online-retail-etl/           # Online retail ETL project
│   ├── dags/                     # Project-specific DAGs
│   ├── data/                     # Raw and processed data
│   ├── logs/                     # Project logs
│   ├── online_retail_dbt/        # dbt models
│   ├── scripts/                  # ETL scripts
│   ├── requirements.txt          # Python dependencies
│   ├── docker-compose.yaml       # Project-specific Docker Compose
│   └── README.md                 # Project documentation
│
├── plugins/                     # Custom Airflow plugins (currently empty)
│
├── docker-compose.yaml          # Main Docker Compose for all services
├── README.md                    # Repository documentation
└── venv/                        # Python virtual environment
```



## Projects Overview
---

### crypto-price-pipeline
- **Goal:** Ingest, transform, and visualize cryptocurrency price data.
- **Tech Stack:** Airflow, dbt, PostgreSQL, Grafana, PowerBI
- **Features:**
	- Automated data ingestion with Airflow
	- Data transformation with dbt
	- Analytics and dashboards with Grafana and PowerBI

### nyc-taxi-etl
- **Goal:** ETL pipeline for NYC Taxi trip data.
- **Tech Stack:** Airflow, Python, SQL
- **Features:**
	- Data extraction, cleaning, and loading
	- Modular DAGs for batch processing

### online-retail-etl
- **Goal:** ETL and analytics for online retail datasets.
- **Tech Stack:** Airflow, dbt, Python
- **Features:**
	- Data ingestion and transformation
	- dbt models for analytics

### earthquakes-rt (In Development)
- **Goal:** Build a real-time data pipeline for earthquake events, including ingestion, processing, and analytics.
- **Tech Stack:** Airflow, Spark, Docker, SQL
- **Features:**
	- Real-time data ingestion (planned)
	- Distributed processing with Spark (planned)
	- Analytics and reporting (planned)
	- 🚧 *This project is currently in development. Features and documentation will be updated as progress is made.*

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
