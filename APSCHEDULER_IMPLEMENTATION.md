# ✅ APScheduler Implementation - Complete

Implementazione completa di APScheduler con supporto Celery opzionale.

## 🎯 Cosa È Stato Implementato

### 1. Sistema di Scheduler Modulare

✅ **Interface comune** - `BaseScheduler` astratta  
✅ **Due backend** - APScheduler (default) e Celery  
✅ **Switch via env** - `SCHEDULER_BACKEND=apscheduler` o `celery`  
✅ **Factory pattern** - Auto-creazione backend corretto  

### 2. APScheduler Backend

✅ **Completamente asincrono** - Tutti i job sono async  
✅ **Non bloccante** - ThreadPool executor (20 worker)  
✅ **Persistenza PostgreSQL** - Jobs salvati nel database  
✅ **Auto-recovery** - Ricarica job attivi dopo restart  

### 3. Celery Backend (Opzionale)

✅ **Wrapper esistente** - Integrato con Celery attuale  
✅ **Beat schedule dinamico** - Jobs aggiungibili runtime  
✅ **Compatibilità** - Stessa interface di APScheduler  

### 4. Job Manager

✅ **Strategy jobs** - Start/stop/update strategie  
✅ **Reload automatico** - Ricarica strategie attive all'avvio  
✅ **Status monitoring** - Verifica stato job  

### 5. Jobs Predefiniti

Tutti **completamente asincroni**:

- ✅ `collect_crypto_data` - Raccolta dati crypto (ogni 10min)
- ✅ `cleanup_old_data` - Pulizia database (daily 3AM)
- ✅ `health_check` - System health check (ogni ora)
- ✅ `update_exchange_symbols` - Aggiorna simboli (daily 1AM)
- ✅ `execute_single_strategy` - Esecuzione strategia singola
- ✅ `sync_user_balances` - Sincronizza bilanci utenti

### 6. Integrazione FastAPI

✅ **Startup automatico** - Scheduler parte con l'app  
✅ **Shutdown graceful** - Chiusura pulita  
✅ **Backward compatible** - Legacy scheduler supportato  
✅ **Error handling** - App non crasha se scheduler fallisce  

---

## 📁 File Creati

```
app/scheduler/
├── __init__.py              # Public API
├── base.py                  # Abstract base class
├── apscheduler_backend.py   # APScheduler implementation
├── celery_backend.py        # Celery wrapper
├── factory.py               # Factory + lifecycle
├── jobs.py                  # Async job definitions
└── manager.py               # Strategy job management
```

---

## 📝 File Modificati

### `requirements.txt`
```diff
+ APScheduler==3.10.4  # Default scheduler
  celery==5.3.4  # Optional: use when SCHEDULER_BACKEND=celery
```

### `app/core/config.py`
```python
scheduler_backend: str = "apscheduler"  # Options: "apscheduler" or "celery"
```

### `app/main.py`
```python
@app.on_event("startup")
async def startup_event():
    from app.scheduler import start_scheduler
    start_scheduler()  # Auto-selects backend

@app.on_event("shutdown")
async def shutdown_event():
    from app.scheduler import shutdown_scheduler
    shutdown_scheduler()
```

### `Procfile`
```procfile
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
# Optional Celery worker (uncomment if using Celery):
# worker: celery -A app.tasks.celery_app worker --loglevel=info
```

### `env.example`
```env
# Scheduler Backend
SCHEDULER_BACKEND=apscheduler  # or "celery"
```

---

## 🚀 Come Usare

### Setup APScheduler (Default)

```bash
# 1. Deploy su Heroku
heroku create your-app

# 2. Configura database
heroku config:set DATABASE_URL="postgresql://..."

# 3. APScheduler è già default
heroku config:set SCHEDULER_BACKEND=apscheduler  # Opzionale, è default

# 4. Usa Basic dyno per evitare sleep
heroku ps:scale web=1:basic  # $7/mese

# 5. Deploy
git push heroku main
```

**Costo: $7/mese** (solo Basic dyno)

### Setup Celery (Opzionale)

```bash
# 1. Configura Celery
heroku config:set SCHEDULER_BACKEND=celery

# 2. Aggiungi Redis
heroku config:set REDIS_URL="redis://..."

# 3. Decommenta worker in Procfile
# 4. Scale worker dyno
heroku ps:scale web=1:basic worker=1:basic

# 5. Deploy
git push heroku main
```

**Costo: $14/mese** (2 dyno Basic)

---

## 🔧 API Usage

### Gestire Strategie

```python
from app.scheduler import (
    add_strategy_job,
    remove_strategy_job,
    update_strategy_job
)

# Start strategy
add_strategy_job(
    strategy_id=123,
    interval_seconds=300,  # 5 minuti
    start_immediately=True
)

# Update interval
update_strategy_job(
    strategy_id=123,
    interval_seconds=600  # 10 minuti
)

# Stop strategy
remove_strategy_job(strategy_id=123)
```

### Esempio in Endpoint

```python
@router.post("/{strategy_id}/start")
async def start_strategy(
    strategy_id: int,
    db: Session = Depends(get_db)
):
    strategy = db.query(Strategy).get(strategy_id)
    strategy.is_active = True
    db.commit()
    
    # Add scheduler job
    add_strategy_job(
        strategy_id=strategy.id,
        interval_seconds=strategy.execution_interval,
        start_immediately=True
    )
    
    return strategy
```

---

## ✨ Features Principali

### 1. Jobs Completamente Asincroni

```python
async def collect_crypto_data():
    """
    Async job - non blocca il web dyno!
    """
    tasks = [
        collect_data('BTC/USDT'),
        collect_data('ETH/USDT'),
    ]
    
    # Esegue in parallelo
    await asyncio.gather(*tasks)
```

### 2. Persistenza Automatica

```python
# Jobs salvati in PostgreSQL
# Se dyno riavvia:
# 1. App si avvia
# 2. APScheduler legge jobs da DB
# 3. Ricarica automaticamente
# 4. Continua esecuzione
```

### 3. Switch Backend Senza Codice

```bash
# Passa a APScheduler
heroku config:set SCHEDULER_BACKEND=apscheduler
heroku restart

# Passa a Celery
heroku config:set SCHEDULER_BACKEND=celery
heroku ps:scale worker=1:basic
heroku restart
```

### 4. Backward Compatible

```python
# Codice Celery esistente continua a funzionare!
from app.tasks.celery_app import celery_app

# Nuovo codice usa interface comune
from app.scheduler import get_scheduler
scheduler = get_scheduler()  # APScheduler o Celery
```

---

## 📊 Monitoring

### Logs Scheduler

```bash
# Startup
heroku logs --tail | grep "scheduler"
# Output: "Background scheduler started, backend=apscheduler"

# Job registrations
heroku logs --tail | grep "Registered job"
# Output: "Registered job: collect_crypto_data"

# Job executions
heroku logs --tail | grep "strategy_"
# Output: "Executing strategy 123..."
```

### Status Check

```python
from app.scheduler import get_scheduler

scheduler = get_scheduler()
jobs = scheduler.get_jobs()

print(f"Active jobs: {len(jobs)}")
for job in jobs:
    print(f"- {job.id}: next run at {job.next_run_time}")
```

---

## ⚠️ Importante

### 1. Dyno Type

❌ **Eco dyno** ($5) - Va in sleep → scheduler si ferma  
✅ **Basic dyno** ($7) - Mai sleep → scheduler sempre attivo  

```bash
# Upgrade a Basic
heroku ps:scale web=1:basic
```

### 2. Single Instance

APScheduler funziona meglio con **1 dyno**.

❌ Non scalare: `heroku ps:scale web=2` → job duplicati  
✅ Usa: `heroku ps:scale web=1:basic`

### 3. Jobs Pesanti

Se hai job che impiegano >30 secondi:

```python
# Usa timeout
import asyncio

async def heavy_job():
    try:
        await asyncio.wait_for(
            long_operation(),
            timeout=300  # 5min max
        )
    except asyncio.TimeoutError:
        logger.error("Job timeout!")
```

---

## 🎯 Testing

### Test Locale

```python
# test_scheduler.py
import pytest
from app.scheduler import get_scheduler, add_strategy_job

def test_add_job():
    scheduler = get_scheduler()
    
    success = add_strategy_job(
        strategy_id=999,
        interval_seconds=60
    )
    
    assert success == True
    
    job = scheduler.get_job("strategy_999")
    assert job is not None
```

### Test Heroku

```bash
# Deploy
git push heroku main

# Verifica logs
heroku logs --tail

# Dovresti vedere:
# - "Background scheduler started"
# - "Registered job: collect_crypto_data"
# - "Reloaded X active strategies"
```

---

## 📚 Documentazione

- **[SCHEDULER_GUIDE.md](SCHEDULER_GUIDE.md)** - Guida completa scheduler
- **[HEROKU_DEPLOYMENT.md](HEROKU_DEPLOYMENT.md)** - Guida deployment
- **[QUICKSTART_HEROKU.md](QUICKSTART_HEROKU.md)** - Quick start

---

## ✅ Checklist Post-Implementazione

- [x] APScheduler backend implementato
- [x] Celery backend wrapper implementato
- [x] Factory pattern con auto-selection
- [x] Jobs asincroni creati
- [x] Strategy manager implementato
- [x] Integrazione in FastAPI (startup/shutdown)
- [x] Configurazione environment variables
- [x] Procfile aggiornato
- [x] requirements.txt aggiornato
- [x] Documentazione completa

---

## 🚦 Next Steps

1. **Deploy su Heroku**
   ```bash
   git push heroku main
   ```

2. **Scala a Basic dyno**
   ```bash
   heroku ps:scale web=1:basic
   ```

3. **Verifica funzionamento**
   ```bash
   heroku logs --tail
   ```

4. **Testa API strategie**
   ```bash
   curl -X POST https://your-app.herokuapp.com/api/v1/strategies/1/start
   ```

5. **Monitor jobs**
   ```bash
   heroku logs --tail | grep "strategy_"
   ```

---

**✨ Implementazione completata con successo!**

Sistema di scheduling flessibile, scalabile e completamente asincrono pronto per la produzione.

