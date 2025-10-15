# 📊 Data Collection Admin - Guida Completa

Sistema completo per gestire dinamicamente la raccolta dati crypto con tracking delle esecuzioni.

## ✨ Features

✅ **Gestione Completa da API** - Aggiungi/rimuovi/modifica simboli da raccogliere  
✅ **Configurazione Flessibile** - Scegli exchange, timeframes, intervallo  
✅ **Tracking Esecuzioni** - Ogni job tracciato con start/end time  
✅ **Statistiche Real-time** - Success rate, durata media, records raccolti  
✅ **Job Asincroni** - Non bloccano l'applicazione web  
✅ **Persistenza DB** - Jobs sopravvivono ai restart  

---

## 🎯 Architettura

```
┌────────────────────────────────────────────────┐
│           Frontend Dashboard                    │
│  (visualizza status, logs, statistiche)        │
└────────────────┬───────────────────────────────┘
                 │ API Calls
┌────────────────▼───────────────────────────────┐
│           API Endpoints                         │
│  /api/v1/admin/data-collection/*               │
└────────────────┬───────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────┐
│         APScheduler Manager                     │
│  Gestisce jobs dinamici                        │
└────────────────┬───────────────────────────────┘
                 │
┌────────────────▼───────────────────────────────┐
│         Database Tables                         │
│  - data_collection_configs (cosa raccogliere)  │
│  - job_execution_logs (tracking esecuzioni)    │
└────────────────────────────────────────────────┘
```

---

## 📁 File Creati

### Models
- `app/models/data_collection.py`
  - `DataCollectionConfig` - Configurazione raccolta dati
  - `JobExecutionLog` - Log esecuzioni job

### Schemas
- `app/schemas/data_collection.py`
  - Request/Response schemas per API
  - Stats e status schemas

### API
- `app/api/v1/data_collection_admin.py`
  - CRUD completo per configurazioni
  - Endpoints per logs e statistiche

### Scheduler
- `app/scheduler/jobs.py` - `collect_data_for_config()`
- `app/scheduler/manager.py` - Funzioni gestione data collection jobs

### Migration
- `migrations/versions/add_data_collection_tables.py`

---

## 🔧 API Endpoints

### Configurazioni

#### `GET /api/v1/admin/data-collection/configs`
Lista tutte le configurazioni di raccolta dati.

**Query params:**
- `enabled`: bool (filtra per enabled/disabled)
- `exchange`: str (filtra per exchange)
- `skip`: int (pagination)
- `limit`: int (max 100)

**Response:**
```json
[
  {
    "id": 1,
    "symbol": "BTC/USDT",
    "exchange": "binance",
    "timeframes": ["1m", "5m", "1h"],
    "interval_minutes": 10,
    "enabled": true,
    "job_id": "collect_data_1",
    "created_at": "2025-01-15T10:00:00Z",
    "description": "Bitcoin data collection"
  }
]
```

#### `POST /api/v1/admin/data-collection/configs`
Crea nuova configurazione raccolta dati.

**Request:**
```json
{
  "symbol": "ETH/USDT",
  "exchange": "binance",
  "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
  "interval_minutes": 10,
  "enabled": true,
  "description": "Ethereum data collection"
}
```

**Response:** Config creata con `id` e `job_id`

✨ **Il job scheduler viene creato automaticamente!**

#### `PUT /api/v1/admin/data-collection/configs/{config_id}`
Aggiorna configurazione esistente.

**Request:**
```json
{
  "interval_minutes": 5,
  "timeframes": ["1m", "1h"]
}
```

✨ **Il job scheduler viene aggiornato automaticamente!**

#### `DELETE /api/v1/admin/data-collection/configs/{config_id}`
Elimina configurazione.

✨ **Il job scheduler viene rimosso automaticamente!**

#### `POST /api/v1/admin/data-collection/configs/{config_id}/enable`
Abilita configurazione e avvia job.

#### `POST /api/v1/admin/data-collection/configs/{config_id}/disable`
Disabilita configurazione e ferma job.

#### `POST /api/v1/admin/data-collection/configs/{config_id}/trigger`
Trigger manuale - esegue raccolta dati immediatamente.

---

### Job Execution Logs

#### `GET /api/v1/admin/data-collection/execution-logs`
Lista log delle esecuzioni job.

**Query params:**
- `job_name`: str
- `job_type`: str
- `symbol`: str
- `status`: str (running, success, failed)
- `start_date`: datetime
- `end_date`: datetime
- `skip`: int
- `limit`: int (max 1000)

**Response:**
```json
[
  {
    "id": 1234,
    "job_name": "collect_data_1",
    "job_type": "data_collection",
    "symbol": "BTC/USDT",
    "exchange": "binance",
    "timeframe": null,
    "started_at": "2025-01-15T10:00:00Z",
    "finished_at": "2025-01-15T10:00:03Z",
    "duration_seconds": 3.2,
    "status": "success",
    "records_collected": 6,
    "error_message": null,
    "metadata": {
      "timeframes_collected": 6,
      "timeframes_failed": 0,
      "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"]
    }
  }
]
```

#### `GET /api/v1/admin/data-collection/execution-logs/{log_id}`
Dettagli log specifico.

#### `GET /api/v1/admin/data-collection/stats`
Statistiche esecuzioni job.

**Query params:**
- `job_type`: str (filtra per tipo)
- `hours`: int (default 24, ultime N ore)

**Response:**
```json
{
  "total_executions": 144,
  "successful_executions": 142,
  "failed_executions": 2,
  "running_executions": 0,
  "success_rate": 98.61,
  "average_duration_seconds": 3.5,
  "total_records_collected": 864,
  "last_execution": "2025-01-15T14:30:00Z"
}
```

#### `GET /api/v1/admin/data-collection/status`
Dashboard completo - overview generale.

**Response:**
```json
{
  "total_configs": 5,
  "enabled_configs": 4,
  "disabled_configs": 1,
  "active_jobs": 4,
  "recent_executions": [...],  // Ultimi 10 log
  "stats": {
    "total_executions": 144,
    "success_rate": 98.61,
    ...
  }
}
```

---

## 💻 Esempi d'Uso

### Aggiungere Simbolo da Raccogliere

```bash
curl -X POST https://your-app.herokuapp.com/api/v1/admin/data-collection/configs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "SOL/USDT",
    "exchange": "binance",
    "timeframes": ["1m", "5m", "1h", "1d"],
    "interval_minutes": 10,
    "enabled": true,
    "description": "Solana price tracking"
  }'
```

**Risultato:** Job scheduler creato automaticamente! SOL/USDT verrà raccolto ogni 10 minuti.

### Modificare Intervallo

```bash
curl -X PUT https://your-app.herokuapp.com/api/v1/admin/data-collection/configs/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "interval_minutes": 5
  }'
```

**Risultato:** Job aggiornato! Ora raccoglie ogni 5 minuti invece che 10.

### Trigger Manuale

```bash
curl -X POST https://your-app.herokuapp.com/api/v1/admin/data-collection/configs/1/trigger \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Risultato:** Raccolta dati eseguita immediatamente (non aspetta il prossimo scheduler run).

### Visualizzare Log Ultimi 7 Giorni

```bash
curl "https://your-app.herokuapp.com/api/v1/admin/data-collection/execution-logs?limit=100" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Statistiche Ultime 24 Ore

```bash
curl "https://your-app.herokuapp.com/api/v1/admin/data-collection/stats?hours=24" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🎨 Frontend Dashboard (Esempio React)

```jsx
// DataCollectionDashboard.jsx

import { useState, useEffect } from 'react';

function DataCollectionDashboard() {
  const [status, setStatus] = useState(null);
  const [configs, setConfigs] = useState([]);
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    // Carica status generale
    fetch('/api/v1/admin/data-collection/status')
      .then(res => res.json())
      .then(data => setStatus(data));

    // Carica configurazioni
    fetch('/api/v1/admin/data-collection/configs')
      .then(res => res.json())
      .then(data => setConfigs(data));

    // Carica log recenti
    fetch('/api/v1/admin/data-collection/execution-logs?limit=20')
      .then(res => res.json())
      .then(data => setLogs(data));
  }, []);

  const triggerCollection = async (configId) => {
    await fetch(`/api/v1/admin/data-collection/configs/${configId}/trigger`, {
      method: 'POST'
    });
    alert('Collection triggered!');
  };

  return (
    <div>
      {/* Status Overview */}
      {status && (
        <div className="stats">
          <div>Configs Attive: {status.enabled_configs}</div>
          <div>Jobs Attivi: {status.active_jobs}</div>
          <div>Success Rate: {status.stats.success_rate}%</div>
          <div>Records Raccolti: {status.stats.total_records_collected}</div>
        </div>
      )}

      {/* Configurazioni */}
      <h2>Configurazioni Raccolta Dati</h2>
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Exchange</th>
            <th>Timeframes</th>
            <th>Intervallo</th>
            <th>Status</th>
            <th>Azioni</th>
          </tr>
        </thead>
        <tbody>
          {configs.map(config => (
            <tr key={config.id}>
              <td>{config.symbol}</td>
              <td>{config.exchange}</td>
              <td>{config.timeframes.join(', ')}</td>
              <td>{config.interval_minutes}min</td>
              <td>{config.enabled ? '✅' : '❌'}</td>
              <td>
                <button onClick={() => triggerCollection(config.id)}>
                  Trigger Now
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Log Esecuzioni */}
      <h2>Log Recenti</h2>
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Started</th>
            <th>Duration</th>
            <th>Status</th>
            <th>Records</th>
          </tr>
        </thead>
        <tbody>
          {logs.map(log => (
            <tr key={log.id}>
              <td>{log.symbol}</td>
              <td>{new Date(log.started_at).toLocaleString()}</td>
              <td>{log.duration_seconds?.toFixed(2)}s</td>
              <td>
                {log.status === 'success' ? '✅' : 
                 log.status === 'failed' ? '❌' : '⏳'}
              </td>
              <td>{log.records_collected}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## 🔍 Query Utili SQL

### Top 10 simboli per records raccolti

```sql
SELECT 
  symbol,
  COUNT(*) as executions,
  SUM(records_collected) as total_records,
  AVG(duration_seconds) as avg_duration,
  SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END)::float / COUNT(*) * 100 as success_rate
FROM job_execution_logs
WHERE job_type = 'data_collection'
  AND started_at >= NOW() - INTERVAL '7 days'
GROUP BY symbol
ORDER BY total_records DESC
LIMIT 10;
```

### Job falliti recenti

```sql
SELECT *
FROM job_execution_logs
WHERE status = 'failed'
  AND started_at >= NOW() - INTERVAL '24 hours'
ORDER BY started_at DESC;
```

### Performance per exchange

```sql
SELECT 
  exchange,
  AVG(duration_seconds) as avg_duration,
  SUM(records_collected) as total_records
FROM job_execution_logs
WHERE job_type = 'data_collection'
  AND finished_at IS NOT NULL
GROUP BY exchange;
```

---

## ✅ Best Practices

### 1. Intervallo Minimo

**Raccomandazione:** Non scendere sotto i **5 minuti**

- API exchange hanno rate limits
- Dyno Heroku ha limiti di request
- Job troppo frequenti saturano il DB

### 2. Timeframes Intelligenti

```json
// ✅ GOOD - Timeframes progressivi
{
  "timeframes": ["1m", "5m", "1h", "1d"]
}

// ❌ BAD - Troppi timeframes simili
{
  "timeframes": ["1m", "2m", "3m", "4m", "5m"]
}
```

### 3. Monitoring

Controlla regolarmente:
- Success rate (dovrebbe essere >95%)
- Durata media (dovrebbe essere <5s)
- Log errori

### 4. Cleanup

Pulisci log vecchi periodicamente:

```sql
DELETE FROM job_execution_logs
WHERE started_at < NOW() - INTERVAL '30 days';
```

---

## 🚀 Deploy

### 1. Run Migration

```bash
# Locale
python migrate.py upgrade

# Heroku
heroku run python migrate.py upgrade
```

### 2. Test API

```bash
curl https://your-app.herokuapp.com/api/v1/admin/data-collection/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Aggiungi Prime Configurazioni

Usa POST `/configs` per aggiungere simboli da raccogliere.

### 4. Monitor Logs

```bash
heroku logs --tail | grep "collect_data"
```

---

## 📊 Metriche da Monitorare

| Metrica | Valore Ideale | Alert Se |
|---------|---------------|----------|
| Success Rate | >95% | <90% |
| Durata Media | <5s | >10s |
| Records/Giorno | Dipende da config | Calo improvviso >20% |
| Failed Jobs | <5% | >10% |
| Running Jobs Stuck | 0 | >0 per >30min |

---

## 🎯 Prossimi Step

Dopo il deploy:

1. ✅ Aggiungi 3-5 simboli principali (BTC, ETH, BNB, SOL, XRP)
2. ✅ Monitor per 24h - verifica success rate
3. ✅ Aggiungi altri simboli progressivamente
4. ✅ Crea dashboard frontend per visualizzare status
5. ✅ Setup alerting per failed jobs

---

**✨ Sistema completo di data collection amministrabile da API pronto all'uso!**

Ogni job tracciato con precision timing, errors logged, statistiche in real-time. 🎉

