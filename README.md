# 🎵 AI Music Recommender Agent - Data Engineering Capstone

## 🎯 Project Overview

This capstone project builds a comprehensive **AI Music Recommender Agent** that provides personalized music recommendations using modern data engineering practices. The system implements an end-to-end ELT (Extract, Load, Transform) pipeline that collects music data from multiple sources, processes it through cloud infrastructure, and serves AI-powered recommendations.

### 🎼 What We're Building
- **AI-powered music recommendation engine** using collaborative filtering and content-based algorithms
- **Multi-source data integration** from Last.fm API, Spotify API, and Kaggle datasets
- **Scalable cloud architecture** with PostgreSQL (local) and Snowflake (cloud)
- **Real-time and batch processing** capabilities for music analytics
- **Production-ready pipeline** with orchestration, monitoring, and quality checks

### 🎯 Success Metrics
- **Performance**: < 2 seconds recommendation response time
- **Quality**: > 95% data completeness and accuracy
- **Scale**: Support 1000+ concurrent users
- **Coverage**: 6+ music genres and 1000+ artists

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

#### [`architecture.md`](docs/architecture.md)
Complete system architecture overview with 8-layer design, from data sources to AI recommendations. Includes visual Mermaid diagrams and component relationships.

#### [`DATA_FLOW.md`](docs/DATA_FLOW.md)
Simple ELT (Extract, Load, Transform) data flow documentation explaining the journey from music APIs to AI recommendations, including technologies and processes at each stage.

#### [`TECHNOLOGY_CHOICES.md`](docs/architecture/TECHNOLOGY_CHOICES.md)
Architecture Decision Records (ADRs) documenting technology choices with rationale:
- **PostgreSQL** for local development
- **Snowflake** for cloud data warehouse
- **Python 3.10+** for data processing
- **dbt** for data transformation
- **Apache Airflow** for orchestration

### 🔍 Data Source Documentation (`docs/data-source/`)

#### [`batch-source-validation.md`](docs/data-source/batch-source-validation.md)
Validation and evaluation of batch data sources including Kaggle music datasets.

#### [`stream-source-validation.md`](docs/data-source/stream-source-validation.md)
Analysis of real-time data sources like Last.fm and Spotify APIs with rate limiting and reliability considerations.

### 📋 Project Specification

#### [`project-spec.md`](docs/project-spec.md)
Comprehensive project specification including scope, success metrics, implementation timeline, and recommendations for building the AI Music Recommender Agent.

## 🔧 Data Collection Scripts (`scripts/data_collection/`)

### 🎵 [`lastfm_api_collector.py`](scripts/data_collection/lastfm_api_collector.py)
**Primary music data collector** for Last.fm API integration:
- ✅ **Top tracks and artists** collection
- ✅ **User listening history** and recent tracks
- ✅ **Genre-based recommendations** with tag filtering
- ✅ **Rate limiting and retry logic** (5 req/sec)
- ✅ **Comprehensive error handling** with fallback strategies
- ✅ **JSON data export** to `data/external/`

### 🎧 [`spotify_api_collector.py`](scripts/data_collection/spotify_api_collector.py)
**Secondary music data source** for Spotify API integration:
- ✅ **Track audio features** (valence, energy, danceability)
- ✅ **Artist and album metadata** collection
- ✅ **OAuth authentication** handling
- ✅ **Batch processing** capabilities

### 🌐 [`api_collector.py`](scripts/data_collection/api_collector.py)
**Generic API collector framework** with reusable patterns:
- ✅ **Environment-driven configuration**
- ✅ **Pagination and batch processing**
- ✅ **Exponential backoff retry logic**
- ✅ **Timestamped JSON file output**

### 🎲 [`fake_data_generator.py`](scripts/data_collection/fake_data_generator.py)
**Synthetic data generator** for development and testing:
- ✅ **Realistic music metadata** using Faker library
- ✅ **User listening patterns** simulation
- ✅ **CSV and JSON output formats**
- ✅ **Fallback data source** for API unavailability

### 🧪 [`test_api_collector.py`](scripts/data_collection/test_api_collector.py)
**API testing utilities** for validation and debugging:
- ✅ **Connection testing** for music APIs
- ✅ **Data quality validation**
- ✅ **Response format verification**

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

### 🔄 ELT Pipeline
```
Music APIs → Python Collectors → PostgreSQL (staging) → Snowflake (cloud) → dbt (transform) → AI Models
```

### 🛠️ Technology Stack
- **Languages**: Python 3.10+, SQL
- **Databases**: PostgreSQL (local), Snowflake (cloud)
- **Processing**: dbt, pandas, polars
- **Orchestration**: Apache Airflow
- **APIs**: Last.fm, Spotify, Kaggle
- **Infrastructure**: Docker, UV package manager

## 📈 Development Roadmap

- **Week 1-2**: ✅ Data collection and local staging
- **Week 3-4**: ⏳ Cloud warehouse and dbt transformations
- **Week 5-6**: 📋 Real-time streaming and orchestration
- **Week 7-8**: 🤖 AI recommendation engine
- **Week 9-10**: 🚀 Testing, optimization, and demo

## 🤝 Contributing

This is a capstone project demonstrating modern data engineering practices for music recommendation systems. The codebase follows industry standards with comprehensive documentation, testing, and architectural decision records.

---

**Built with ❤️ for music lovers and data engineers**