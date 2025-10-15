# 📅 Scheduler Guide - APScheduler vs Celery

Guida completa al sistema di scheduling per background tasks.

## 🎯 Overview

Altar Trader Hub supporta **due backend per lo scheduling**:

| Backend | Quando Usarlo | Costo | Complessità |
|---------|---------------|-------|-------------|
| **APScheduler** (default) | App piccole/medie, sempre attiva | $7/mese (Basic dyno) | Bassa |
| **Celery** | App grandi, distributed tasks | $14/mese (2 dyno) | Alta |

### Cambio Backend

Modifica la variabile d'ambiente:

```bash
# APScheduler (default)
heroku config:set SCHEDULER_BACKEND=apscheduler

# Celery
heroku config:set SCHEDULER_BACKEND=celery
```

---

## 🔹 APScheduler (Default - Consigliato)

### Caratteristiche

✅ **Tutto nel web dyno** - nessun worker separato  
✅ **Jobs asincroni** - non bloccano l'applicazione  
✅ **Persistenza PostgreSQL** - jobs sopravvivono ai restart  
✅ **Gestibile da API** - start/stop strategie via endpoint  
✅ **Costo minimo** - solo $7/mese (Basic dyno)  

### Architettura

```
┌──────────────────────────┐
│     Basic Dyno ($7)      │
│  ┌────────────────────┐  │
│  │   FastAPI Web      │  │
│  │   (Port $PORT)     │  │
│  └────────────────────┘  │
│  ┌────────────────────┐  │
│  │   APScheduler      │  │
│  │  (Background       │  │
│  │   Thread Pool)     │  │
│  └────────────────────┘  │
└──────────────────────────┘
           │
           ├─> PostgreSQL (jobs persistence)
           └─> Redis (optional, cache)
```

### Setup Heroku

```bash
# 1. Deploy con APScheduler
heroku config:set SCHEDULER_BACKEND=apscheduler

# 2. Usa Basic dyno (non Eco - mai sleep!)
heroku ps:scale web=1:basic  # $7/mese

# 3. Deploy
git push heroku main

# 4. Verifica
heroku logs --tail
# Dovresti vedere: "Background scheduler started, backend=apscheduler"
```

### Jobs Automatici

Jobs registrati automaticamente all'avvio:

| Job | Frequenza | Descrizione |
|-----|-----------|-------------|
| `collect_crypto_data` | Ogni 10 minuti | Raccolta dati mercato |
| `cleanup_old_data` | Giornaliero (3 AM) | Pulizia dati vecchi |
| `health_check` | Ogni ora | Health check sistema |
| `update_exchange_symbols` | Giornaliero (1 AM) | Aggiorna simboli disponibili |

### Jobs Dinamici (Strategie)

```python
# Quando utente attiva strategia:
POST /api/v1/strategies/123/start

# APScheduler automaticamente:
# 1. Crea job "strategy_123"
# 2. Schedule con intervallo della strategia
# 3. Esegue strategia in modo asincrono

# Quando utente disattiva:
POST /api/v1/strategies/123/stop

# APScheduler automaticamente:
# 1. Rimuove job "strategy_123"
# 2. Ferma esecuzione
```

### Limitazioni

⚠️ **Single Instance** - Se scali a `web=2`, i job si duplicano  
⚠️ **Dyno Eco** - Con Eco dyno ($5), se va in sleep i job si fermano  
✅ **Soluzione** - Usa Basic dyno ($7) che MAI va in sleep

---

## 🔸 Celery (Opzionale)

### Caratteristiche

✅ **Distributed** - Multi-worker support  
✅ **Scalabile** - Può gestire migliaia di jobs  
✅ **Robusto** - Retry automatici, routing complesso  
❌ **Costo alto** - Richiede worker dyno separato (+$7)  
❌ **Complessità** - Setup più complesso

### Architettura

```
┌─────────────────┐         ┌──────────────────┐
│  Web Dyno ($7)  │         │ Worker Dyno ($7) │
│                 │         │                  │
│   FastAPI       │         │  Celery Worker   │
│                 │         │  + Beat          │
└─────────────────┘         └──────────────────┘
         │                           │
         └──────┬───────────────────┘
                │
         ┌──────▼──────┐
         │   Redis     │ (Celery broker)
         │  (Upstash)  │
         └─────────────┘
```

### Setup Heroku

```bash
# 1. Configura Celery backend
heroku config:set SCHEDULER_BACKEND=celery

# 2. Aggiungi Redis (per Celery broker)
heroku config:set REDIS_URL="redis://..."  # Upstash URL

# 3. Abilita worker dyno in Procfile
# Decommenta la riga "worker:" nel Procfile

# 4. Scale dyno
heroku ps:scale web=1:basic worker=1:basic  # $14/mese totale

# 5. Deploy
git push heroku main
```

### Quando Usare Celery

Usa Celery se:
- Hai bisogno di scalare a molti worker
- Vuoi distributed task processing
- Hai task molto pesanti (>1 minuto)
- Vuoi task routing complesso

---

## 📝 Uso nell'Applicazione

### Aggiungere Nuovo Job Fisso

```python
# In app/scheduler/jobs.py

async def my_custom_job() -> None:
    """
    My custom background job.
    
    Must be async to avoid blocking the web application.
    """
    logger.info("Running my custom job...")
    
    try:
        # Your async logic here
        await some_async_function()
        
        logger.info("My custom job completed")
        
    except Exception as e:
        logger.error(f"Error in my_custom_job: {e}")
        raise


# In app/scheduler/factory.py, _register_default_jobs():

scheduler.add_job(
    func=my_custom_job,
    job_id="my_custom_job",
    trigger="interval",
    minutes=15  # Ogni 15 minuti
)
```

### Gestire Job Strategie

```python
from app.scheduler import (
    add_strategy_job,
    remove_strategy_job,
    update_strategy_job
)

# Aggiungere strategia
add_strategy_job(
    strategy_id=123,
    interval_seconds=300,  # 5 minuti
    start_immediately=True
)

# Aggiornare intervallo
update_strategy_job(
    strategy_id=123,
    interval_seconds=600  # 10 minuti
)

# Rimuovere strategia
remove_strategy_job(strategy_id=123)
```

### Verificare Job Attivi

```python
from app.scheduler import get_scheduler

scheduler = get_scheduler()
jobs = scheduler.get_jobs()

for job in jobs:
    print(f"Job: {job.id}, Next run: {job.next_run_time}")
```

---

## 🔧 Configurazione Avanzata

### APScheduler Settings

```python
# app/scheduler/apscheduler_backend.py

executors = {
    'default': ThreadPoolExecutor(max_workers=20)  # Max 20 job paralleli
}

job_defaults = {
    'coalesce': True,       # Combina run multipli mancati
    'max_instances': 3,     # Max 3 istanze stesso job
    'misfire_grace_time': 60  # Tolleranza 60s per missed jobs
}
```

### Celery Settings

```python
# app/tasks/celery_app.py

celery_app.conf.update(
    task_serializer="json",
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_time_limit=30 * 60,  # 30 minuti max
)
```

---

## 🐛 Troubleshooting

### APScheduler

**Jobs non partono:**
```bash
# Verifica scheduler sia partito
heroku logs --tail | grep "Background scheduler started"

# Verifica jobs registrati
heroku logs --tail | grep "Registered job"

# Controlla errori
heroku logs --tail | grep "ERROR"
```

**Jobs si fermano:**
```bash
# Probabilmente dyno Eco in sleep
# Upgrade a Basic dyno:
heroku ps:scale web=1:basic
```

**Jobs si duplicano:**
```bash
# Hai più dyno attivi
heroku ps
# Output: web.1: up (se vedi web.2, riduci a 1)
heroku ps:scale web=1
```

### Celery

**Worker non si connette:**
```bash
# Verifica worker dyno attivo
heroku ps

# Verifica Redis URL
heroku config:get REDIS_URL

# Test connessione Redis
heroku run python -c "import redis; r=redis.from_url('$REDIS_URL'); r.ping()"
```

**Tasks non eseguiti:**
```bash
# Verifica worker logs
heroku logs --tail --dyno worker

# Controlla Celery beat schedule
heroku run python -c "from app.tasks.celery_app import celery_app; print(celery_app.conf.beat_schedule)"
```

---

## 💡 Best Practices

### 1. Sempre Async
```python
# ✅ GOOD
async def my_job():
    await async_operation()

# ❌ BAD (blocca il web dyno!)
def my_job():
    time.sleep(60)  # Blocca tutto!
```

### 2. Gestione Errori
```python
async def my_job():
    try:
        await risky_operation()
    except Exception as e:
        logger.error(f"Job failed: {e}")
        # Non ri-raise se vuoi che il job continui
        # raise se vuoi che il job fallisca
```

### 3. Timeout
```python
# Per operazioni lunghe, usa timeout
import asyncio

async def my_job():
    try:
        await asyncio.wait_for(
            long_operation(),
            timeout=300  # 5 minuti max
        )
    except asyncio.TimeoutError:
        logger.error("Job timeout")
```

### 4. Database Sessions
```python
async def my_job():
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Use db
        pass
    finally:
        db.close()  # Sempre chiudere!
```

---

## 📊 Monitoring

### Logs

```bash
# APScheduler logs
heroku logs --tail | grep APScheduler

# Job execution logs
heroku logs --tail | grep "strategy_"

# Errors
heroku logs --tail | grep ERROR
```

### Metrics

```python
# In un job
from prometheus_client import Counter

job_executions = Counter('job_executions', 'Job executions', ['job_name'])

async def my_job():
    job_executions.labels(job_name='my_job').inc()
    # ...
```

---

## 🎯 Raccomandazione Finale

**Per la maggior parte dei casi:**

✅ **Usa APScheduler** con **Basic dyno** ($7/mese)

Questo ti dà:
- Scheduler sempre attivo (mai sleep)
- Jobs gestibili da API
- Tutto asincrono (non blocca web)
- Setup semplice
- Costo minimo

**Passa a Celery solo se:**
- Hai bisogno di distributed processing
- Vuoi scalare a molti worker
- Hai task molto pesanti
- Budget per $14+/mese

---

📚 **Vedi anche:**
- [HEROKU_DEPLOYMENT.md](HEROKU_DEPLOYMENT.md) - Guida deployment
- [QUICKSTART_HEROKU.md](QUICKSTART_HEROKU.md) - Quick start
- [README.md](README.md) - Documentazione generale

