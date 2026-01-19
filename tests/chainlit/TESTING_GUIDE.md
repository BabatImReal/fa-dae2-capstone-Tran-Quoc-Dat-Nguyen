# Testing Guide - Chainlit Application

## ✅ Quick Start

### 1. **Run All Tests**
```bash
uv run pytest tests/chainlit/
```

### 2. **Run Specific Test File**
```bash
# Test authentication
uv run pytest tests/chainlit/test_auth.py -v

# Test tools
uv run pytest tests/chainlit/test_tools.py -v

# Test database
uv run pytest tests/chainlit/test_database.py -v
```

### 3. **Run Specific Test Class**
```bash
uv run pytest tests/chainlit/test_auth.py::TestPasswordHashing -v
uv run pytest tests/chainlit/test_tools.py::TestPostgreSQLTools -v
```

### 4. **Run Single Test**
```bash
uv run pytest tests/chainlit/test_auth.py::TestPasswordHashing::test_hash_password_returns_string -v
```

## 📊 Coverage Reports

### Generate Coverage Report
```bash
# Run tests with coverage
uv run pytest tests/chainlit/ --cov=ai-agent --cov-report=html --cov-report=term

# Open HTML report
start htmlcov/index.html  # Windows
```

### Coverage by Module
```bash
# Get detailed coverage with missing lines
uv run pytest tests/chainlit/ --cov=ai-agent --cov-report=term-missing
```

### Target Coverage Goals
- **auth functions**: 90%+
- **tools**: 70%+  
- **database operations**: 80%+
- **Overall**: 70%+

## 🎯 Test Organization

### By Functionality
```bash
# Authentication tests only
uv run pytest tests/chainlit/test_auth.py -v

# PostgreSQL tool tests
uv run pytest tests/chainlit/test_tools.py::TestPostgreSQLTools -v

# Snowflake tool tests  
uv run pytest tests/chainlit/test_tools.py::TestSnowflakeTools -v

# RAG tool tests
uv run pytest tests/chainlit/test_tools.py::TestRAGTools -v

# Database CRUD tests
uv run pytest tests/chainlit/test_database.py::TestUserOperations -v
```

### By Test Type
```bash
# Unit tests (fast, no database)
uv run pytest tests/chainlit/test_auth.py::TestPasswordHashing -v
uv run pytest tests/chainlit/test_tools.py -v

# Integration tests (require database)
uv run pytest tests/chainlit/test_auth.py::TestGetUserFromDB -v
uv run pytest tests/chainlit/test_database.py -v
```

## 🔍 Advanced Options

### Run with Verbose Output
```bash
uv run pytest tests/chainlit/ -vv
```

### Show Print Statements
```bash
uv run pytest tests/chainlit/ -s
```

### Run Only Failed Tests
```bash
# First run
uv run pytest tests/chainlit/

# Re-run only failures
uv run pytest tests/chainlit/ --lf
```

### Stop on First Failure
```bash
uv run pytest tests/chainlit/ -x
```

### Run Tests Matching Pattern
```bash
# Run all tests with "password" in name
uv run pytest tests/chainlit/ -k "password" -v

# Run all async tests
uv run pytest tests/chainlit/ -k "async" -v
```

## 📝 Test Status

### Current Test Coverage

**test_auth.py** ✅
- ✅ TestPasswordHashing (5 tests)
  - hash_password returns string
  - hash is consistent
  - different inputs = different hashes  
  - SHA-256 format validation
  - matches expected hash
- ✅ TestGetUserFromDB (3 tests)
  - existing user retrieval
  - nonexistent user handling
  - correct metadata parsing
- ✅ TestAuthenticationLogic (4 tests)
  - valid credentials
  - invalid password
  - nonexistent user
  - empty credentials

**test_tools.py** ⚠️ (Requires mocking)
- TestPostgreSQLTools (3 tests)
- TestSnowflakeTools (2 tests)
- TestRAGTools (3 tests)
- TestToolInputValidation (3 tests)

**test_database.py** ⚠️ (Requires database)
- TestUserOperations (3 tests)
- TestThreadOperations (2 tests)
- TestStepOperations (1 test)
- TestDataIntegrity (2 tests)

## 🛠️ Prerequisites

### Required Packages
```bash
uv pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### Environment Variables
Ensure these are set in `.env`:
```env
CHAINLIT_POSTGRES_URL=postgresql+asyncpg://chainlit:chainlit_password@localhost:5434/chainlit_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=staging_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

### Database Setup
```bash
# Ensure chainlit database is running
docker-compose -f docker-compose-chainlit-db.yml up -d
```

## 🐛 Troubleshooting

### Import Errors
If you see `ModuleNotFoundError`:
```bash
# Verify __init__.py files exist
ls ai-agent/__init__.py
ls ai-agent/tools/__init__.py
ls ai-agent/chainlit/__init__.py
```

### Database Connection Errors
```bash
# Check database is running
docker ps | grep chainlit-postgres

# Test connection
uv run python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('postgresql://chainlit:chainlit_password@localhost:5434/chainlit_db'))"
```

### Async Test Failures
Make sure test functions are marked with `@pytest.mark.asyncio`:
```python
@pytest.mark.asyncio
async def test_my_async_function():
    result = await my_async_function()
    assert result is not None
```

## 📈 Continuous Integration

### Pre-commit Checks
```bash
# Run before committing
uv run pytest tests/chainlit/ --cov=ai-agent --cov-report=term
```

### Coverage Threshold
```bash
# Fail if coverage below 70%
uv run pytest tests/chainlit/ --cov=ai-agent --cov-fail-under=70
```

## 🎨 Output Examples

### Successful Test Run
```
========== test session starts ==========
tests/chainlit/test_auth.py::TestPasswordHashing::test_hash_password_returns_string PASSED [ 20%]
tests/chainlit/test_auth.py::TestPasswordHashing::test_hash_password_consistent PASSED [ 40%]
...
========== 12 passed in 0.50s ==========
```

### With Coverage
```
---------- coverage: ----------
Name                          Stmts   Miss  Cover   Missing
---------------------------------------------------------
ai-agent/chainlit/auth.py        45      5    89%   23-25
ai-agent/tools/postgre_tools.py  32      8    75%   45-52
---------------------------------------------------------
TOTAL                           180     25    86%
```

## 🚀 Next Steps

1. **Run all unit tests** (no database needed):
   ```bash
   uv run pytest tests/chainlit/test_auth.py::TestPasswordHashing -v
   ```

2. **Run tool tests** (with mocking):
   ```bash
   uv run pytest tests/chainlit/test_tools.py -v
   ```

3. **Run integration tests** (requires database):
   ```bash
   docker-compose -f docker-compose-chainlit-db.yml up -d
   uv run pytest tests/chainlit/test_auth.py::TestGetUserFromDB -v
   ```

4. **Generate coverage report**:
   ```bash
   uv run pytest tests/chainlit/ --cov=ai-agent --cov-report=html
   start htmlcov/index.html
   ```

## 📚 Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [pytest-mock](https://pytest-mock.readthedocs.io/)
