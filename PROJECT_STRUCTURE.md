# 📁 Project Structure

## Root Files (Essential Only)

### Core Files
- `README.md` - Main documentation
- `requirements.txt` - Python dependencies
- `requirements-dev.txt` - Development dependencies
- `requirements-minimal.txt` - Minimal dependencies

### Python Entry Points
- `main.py` - FastAPI app entry point (for debugging)
- `run.py` - Development server runner
- `migrate.py` - Database migrations
- `setup.py` - Python package setup
- `test.py` - Test runner

### Heroku Configuration
- `Procfile` - Heroku dyno configuration
- `runtime.txt` - Python version
- `app.json` - Heroku app metadata
- `.slugignore` - Files excluded from deployment
- `heroku_scheduler.py` - Heroku Scheduler tasks (if not using APScheduler)

### Shell Scripts
- `start_app.sh` - Start application
- `start_dev.sh` - Start development server
- `test_all.sh` - Run all tests

### Alembic
- `alembic.ini` - Alembic configuration

---

## Directory Structure

```
altar-trader-hub-be/
├── app/                    # Main application code
│   ├── api/                # API endpoints
│   │   └── v1/             # API v1 routes
│   ├── core/               # Core config (database, security, logging)
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── scheduler/          # ⭐ NEW - APScheduler + Celery
│   ├── services/           # Business logic
│   ├── tasks/              # Celery tasks (optional)
│   └── utils/              # Utilities
│
├── tests/                  # Pytest tests
│   ├── test_api/
│   ├── test_models/
│   └── test_services/
│
├── migrations/             # Alembic migrations
│   └── versions/
│
├── scripts/                # Utility scripts & data
│   └── download_binance_symbols.py
│
├── paper_trading/          # Paper trading module
│
├── docker/                 # Docker configs (optional for Heroku)
├── k8s/                    # Kubernetes configs (optional for Heroku)
├── helm/                   # Helm charts (optional for Heroku)
│
└── data/                   # Local data cache

```

---

## ⭐ New Additions

### Scheduler System
```
app/scheduler/
├── __init__.py
├── base.py                  # Abstract interface
├── apscheduler_backend.py   # APScheduler implementation
├── celery_backend.py        # Celery wrapper
├── factory.py               # Auto-selects backend
├── jobs.py                  # Job definitions (async)
└── manager.py               # Dynamic job management
```

### Data Collection Models
```
app/models/data_collection.py      # DataCollectionConfig, JobExecutionLog
app/schemas/data_collection.py     # Pydantic schemas
app/api/v1/data_collection_admin.py # Admin API endpoints
```

---

## 🗑️ Files Removed

### Test Files (16 removed)
All `test_*.py` one-off scripts removed from root.  
Real tests remain in `tests/` directory.

### Scripts (12 removed)
- `collect_market_data.py`
- `download_crypto_data.py`
- `fetch_crypto_data.py`
- `update_crypto_data.py`
- `fill_data_gaps.py`
- `fill_data_gaps_selective.py`
- `monitor_crypto_cronjob.py`
- `monitor_data_collection.py`
- `simple_crypto_cronjob.py`
- `start_crypto_cronjob.py`
- `run_celery.py`
- `reorganize_project.py`

All replaced by APScheduler system!

---

## ✅ Clean Root Directory

After cleanup, root contains only:
- Configuration files (.ini, .txt, .json, .yml)
- Essential Python scripts (main.py, run.py, migrate.py, test.py, setup.py)
- Heroku files (Procfile, runtime.txt, app.json, heroku_scheduler.py)
- Shell scripts (start_*.sh, test_all.sh)
- README.md

**Much cleaner!** 🧹✨

