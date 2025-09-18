# 🎵 Music Pipeline - Data Engineering Capstone

## 🎯 Project Overview

This capstone project is a data engineering initiative to build a robust pipeline for music data, enabling personalized music recommendations through modern ELT (Extract, Load, Transform) practices. The system integrates music data from multiple sources, processes it via cloud infrastructure, and supports AI-powered analytics and recommendations.

### 🎼 What We're Building
- **Multi-source data integration** from Last.fm API, Spotify API, and Kaggle datasets
- **Scalable cloud architecture** with PostgreSQL (local) and Snowflake (cloud)
- **Real-time and batch processing** capabilities for music analytics
- **Production-ready pipeline** with orchestration, monitoring, and quality checks

### 🎯 Success Metrics
- **Pipeline Reliability**: Smooth, uninterrupted data flow across all stages
- **Data Quality**: Clean, accurate, and well-validated data throughout the pipeline
- **Analysis Outcomes**: Results from analytics and AI processes are actionable and trustworthy
- **Usability**: Processed data is ready for further activities such as reporting, modeling, and recommendations

## 📁 Project Structure

```
fa-dae2-capstone/
├── 📄 .env                     # Environment configuration
├── 📄 main.py                  # Main pipeline orchestrator
├── 📁 scripts/
│   └── 📁 data_collection/     # Music data collectors
├── 📁 data/
│   └── 📁 external/            # Raw music data files
├── 📁 docs/                    # Project documentation
│   ├── 📁 architecture/        # System design documents
│   ├── 📁 data-source/         # Data source validation
│   └── 📄 project-spec.md      # Project specification
├── 📁 tests/                   # Unit and integration tests
├── 📄 pyproject.toml           # UV project configuration
└── 📄 requirements.txt         # Python dependencies
```

## 📚 Documentation

### 🏗️ Architecture Documentation (`docs/architecture/`)

#### [`data-engineering-fundamentals.md`](docs/architecture/data-engineering-fundamentals.md)
**NEW**: Foundational concepts for modern data systems, answering the five core questions: Where does data come from? How does it move? Where do we store it? How do we process it? How do we use it?

#### [`architecture.md`](docs/architecture/architecture.md)
Complete system architecture overview with 8-layer design, from data sources to AI recommendations. Includes visual Mermaid diagrams and component relationships.

#### [`data-flow.md`](docs/architecture/data-flow.md)
Simple ELT (Extract, Load, Transform) data flow documentation explaining the journey from music APIs to AI recommendations, including technologies and processes at each stage.

#### [`technology-decision.md`](docs/architecture/technology-decision.md)
Architecture Decision Records (ADRs) documenting technology choices with rationale:
- **PostgreSQL** for local development (OLTP)
- **Snowflake** for cloud data warehouse (OLAP)
- **Python 3.10+** for data processing
- **dbt** for data transformation (ELT)
- **Apache Airflow** for orchestration

### 🔍 Data Source Documentation (`docs/data-source/`)

#### [`batch-source-validation.md`](docs/data-source/batch-source-validation.md)
Validation and evaluation of batch data sources including Kaggle music datasets.

#### [`stream-source-validation.md`](docs/data-source/stream-source-validation.md)
Analysis of real-time data sources like Last.fm and Spotify APIs with rate limiting and reliability considerations.

### 📋 Project Specification

#### [`project-spec.md`](docs/project-spec.md)
Comprehensive project specification including scope, success metrics, implementation timeline, and recommendations for building the AI Music Recommender Agent.


## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- UV package manager
- Docker (for PostgreSQL)
- Music API keys (Last.fm, Spotify)

### Setup

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Configure environment**:
   ```bash
   cp env_example.txt .env
   # Add your API keys to .env file
   ```

3. **Run data collection**:
   ```bash
   # Collect Last.fm data
   uv run python scripts/data_collection/lastfm_api_collector.py
   
   # Run full pipeline
   uv run python main.py
   ```

4. **Run tests**:
   ```bash
   pytest tests/test_data_pipeline.py
   ```

## 🛠️ Environment Setup Scripts

### 1️⃣ Python Environment & Dependencies

#### Using UV (recommended)
```bash
uv sync
```

#### Using pip (alternative)
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2️⃣ Docker Setup for PostgreSQL

#### 1. Configure `.env` for Docker Compose
Set your PostgreSQL settings in `.env`:
```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=musicdb
POSTGRES_PORT=5432
POSTGRES_HOST=localhost
```
- Replace `yourpassword` with a secure password.
- You can change `POSTGRES_DB`, `POSTGRES_PORT`, and `POSTGRES_HOST` as needed.

#### 2. Start PostgreSQL with Docker Compose
```bash
docker-compose up -d
```

#### 3. Check container status
```bash
docker ps
```

#### 4. Stop containers
```bash
docker-compose down
```

#### 5. Remove containers and volumes (WARNING: this deletes all database data!)
```bash
docker-compose down -v
```
> ⚠️ **Warning:** Only use `docker-compose down -v` if you want to permanently delete all database data.

#### 6. View logs
```bash
docker-compose logs postgres
```

#### 7. Connect to PostgreSQL inside the container
```bash
docker exec -it music-postgres psql -U $POSTGRES_USER -d $POSTGRES_DB
```
- You can now run SQL commands directly in the container.

### 3️⃣ Running Scripts

#### Run a data collector (example: Last.fm)
```bash
uv run python scripts/data_collection/lastfm_api_collector.py
# Or with pip:
python scripts/data_collection/lastfm_api_collector.py
```

#### Run the main pipeline
```bash
uv run python main.py
# Or with pip:
python main.py
```

#### Run tests
```bash
pytest tests/test_data_pipeline.py
```

## 🎵 Data Sources

### 🎤 Primary Sources
- **[Last.fm API](https://www.last.fm/api)**: User scrobbles, track metadata, listening history
- **[Spotify API](https://developer.spotify.com/documentation/web-api)**: Audio features, artist data, track popularity
- **[Kaggle Music Datasets](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset)**: Historical music data (~230k tracks)

### 🔄 Fallback Strategy
- **API Rate Limits**: Automatic fallback between Last.fm and Spotify
- **Data Unavailability**: Synthetic data generation with Faker
- **Quality Issues**: Multi-source validation and reconciliation

## 🏗️ Architecture Highlights

### 🔄 ELT Pipeline (Based on Data Engineering Fundamentals)
Answering the five core questions of data systems:
```
1. Sources: Music APIs → 
2. Ingestion: Python Collectors → 
3. Storage: PostgreSQL (staging) → Snowflake (cloud) → 
4. Transform: dbt (transform) → 
5. Analysis: AI Models
```

### 🛠️ Technology Stack
- **Languages**: Python 3.10+, SQL
- **Databases**: PostgreSQL (OLTP staging), Snowflake (OLAP analytics)
- **Processing**: dbt, pandas, polars
- **Orchestration**: Apache Airflow
- **APIs**: Last.fm, Spotify, Kaggle
- **Infrastructure**: Docker, UV package manager

### 🎯 Design Patterns
- **ELT over ETL**: Load raw data first, transform in warehouse
- **OLTP vs OLAP**: PostgreSQL for staging, Snowflake for analytics
- **Batch + Real-Time**: Daily training, real-time inference
- **Multi-Source**: Redundancy with fallback mechanisms

## 🗓️ Capstone Module Structure

This capstone project is organized into 5 modules, each representing one month of work. Each module contains 4 weeks, with focused labs and deliverables:

- **Module 01: Foundations & Local ELT**
  - Week 1: Project setup, repo structure, environment configuration
  - Week 2: Data collection scripts and ingestion pipeline
  - Week 3: Local PostgreSQL database setup and staging
  - Week 4: Python database connectivity and local ELT validation

- **Module 02: Cloud Data Warehouse & dbt**
  - Week 1: Snowflake setup and infrastructure
  - Week 2: Data loading and transformation with dbt
  - Week 3: Dimensional modeling and analytics-ready schemas
  - Week 4: Testing, documentation, and review

- **Module 03: Real-time Streaming & Orchestration**
  - Week 1: Kafka streaming infrastructure
  - Week 2: Producer/consumer pipeline and Airflow orchestration
  - Week 3: Production orchestration and batch pipeline
  - Week 4: Integration planning and review

- **Module 04: AI Agent Building**
  - Week 1: LLM API integration and agent foundation
  - Week 2: Agent tools and tool-using agent
  - Week 3: RAG system and vector store
  - Week 4: Data integration planning

- **Module 05: Data Architecture & Finalization**
  - Week 1: Agent-data integration and warehouse query tools
  - Week 2: Safety, observability, and documentation
  - Week 3: Final integration, testing, and demo practice
  - Week 4: Final review, polish, and presentation prep

---

## 📈 Development Roadmap

- **Module 01 (Month 1): Foundations & Local ELT**
  - Week 1: Project setup & repo structure
  - Week 2: Data collection scripts
  - Week 3: Local PostgreSQL setup
  - Week 4: Python DB connectivity & ELT validation

- **Module 02 (Month 2): Cloud DWH & dbt**
  - Week 1: Snowflake setup
  - Week 2: dbt project & transformations
  - Week 3: Dimensional modeling
  - Week 4: Testing & documentation

- **Module 03 (Month 3): Streaming & Orchestration**
  - Week 1: Kafka setup
  - Week 2: Producer/consumer & Airflow
  - Week 3: Batch orchestration
  - Week 4: Integration planning

- **Module 04 (Month 4): AI Agent**
  - Week 1: LLM API & agent foundation
  - Week 2: Agent tools
  - Week 3: RAG system
  - Week 4: Data integration planning

- **Module 05 (Month 5): Finalization & Presentation**
  - Week 1: Agent-data integration
  - Week 2: Safety & documentation
  - Week 3: Final integration & demo
  - Week 4: Final review & presentation

---

## 🤝 Contributing

This is a capstone project demonstrating modern data engineering practices for music recommendation systems. The codebase follows industry standards with comprehensive documentation, testing, and architectural decision records.

---

**Built with ❤️ for music lovers and data engineers**