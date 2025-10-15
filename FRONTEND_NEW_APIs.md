# 🆕 Nuove API - Data Collection Management

Riepilogo delle nuove API aggiunte per gestire la raccolta dati crypto.

## 📊 Nuove Tabelle Database

### 1. `data_collection_configs`
Configurazione di quali simboli crypto raccogliere e quando.

```typescript
interface DataCollectionConfig {
  id: number;
  symbol: string;              // "BTC/USDT"
  exchange: string;            // "binance"
  timeframes: string[];        // ["1m", "5m", "1h", "1d"]
  interval_minutes: number;    // 10
  enabled: boolean;
  job_id: string;              // "collect_data_1"
  created_at: string;
  updated_at?: string;
  description?: string;
}
```

### 2. `job_execution_logs`
Log di ogni esecuzione job con start time, end time, duration, errors.

```typescript
interface JobExecutionLog {
  id: number;
  job_name: string;            // "collect_data_1"
  job_type: string;            // "data_collection"
  symbol: string;              // "BTC/USDT"
  exchange: string;
  started_at: string;          // ISO datetime
  finished_at?: string;        // ISO datetime
  duration_seconds?: number;   // 3.2
  status: 'running' | 'success' | 'failed';
  records_collected?: number;  // 6
  error_message?: string;
  metadata?: object;
}
```

---

## 🔗 Nuovi Endpoint API

Base URL: `/api/v1/admin/data-collection`

### CRUD Configurazioni

```javascript
// 1. Lista configurazioni
GET /configs
GET /configs?enabled=true&exchange=binance

// 2. Crea configurazione (+ avvia job automatico)
POST /configs
{
  "symbol": "BTC/USDT",
  "exchange": "binance",
  "timeframes": ["1m", "5m", "1h"],
  "interval_minutes": 10,
  "enabled": true
}

// 3. Aggiorna configurazione (+ aggiorna job automatico)
PUT /configs/{id}
{
  "interval_minutes": 5,
  "timeframes": ["1m", "1h"]
}

// 4. Elimina configurazione (+ ferma job automatico)
DELETE /configs/{id}

// 5. Enable/Disable
POST /configs/{id}/enable   // Avvia job
POST /configs/{id}/disable  // Ferma job

// 6. Trigger manuale (esegui ora, non aspetta scheduler)
POST /configs/{id}/trigger
```

### Logs & Statistiche

```javascript
// 7. Lista execution logs (filtrabili)
GET /execution-logs
GET /execution-logs?symbol=BTC/USDT&status=success&limit=50

// 8. Dettaglio log specifico
GET /execution-logs/{id}

// 9. Statistiche aggregate (ultime 24h)
GET /stats
GET /stats?hours=24&job_type=data_collection

// 10. Dashboard overview (tutto in una chiamata)
GET /status
```

---

## 🎨 UI da Implementare

### 1. Dashboard Page (Priority HIGH)

```
GET /status → Mostra:
- Total configs, enabled configs
- Active jobs count
- Success rate, avg duration
- Recent executions (last 10)
- Stats cards
```

**Components:**
- 4 cards con stats (total runs, success %, avg duration, records)
- Tabella con ultimi 10 log

### 2. Config Management Page (Priority HIGH)

```
GET /configs → Tabella configurazioni
POST /configs → Form per aggiungere simbolo
PUT /configs/{id} → Edit inline o modal
DELETE /configs/{id} → Delete con conferma
POST /configs/{id}/enable|disable → Toggle switch
POST /configs/{id}/trigger → Button "Run Now"
```

**Components:**
- Tabella configurazioni
- Modal create/edit
- Toggle enable/disable
- Button trigger manual

### 3. Execution Logs Page (Priority MEDIUM)

```
GET /execution-logs → Tabella log con filtri
```

**Components:**
- Tabella logs con pagination
- Filtri: symbol, status, date range
- Detail modal per vedere metadata/errors

---

## 💻 Esempio Chiamate API

### Aggiungere Simbolo

```javascript
const response = await fetch('/api/v1/admin/data-collection/configs', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    symbol: 'ETH/USDT',
    exchange: 'binance',
    timeframes: ['1m', '5m', '1h', '1d'],
    interval_minutes: 10,
    enabled: true
  })
});

// Risposta:
{
  "id": 5,
  "symbol": "ETH/USDT",
  "job_id": "collect_data_5",
  ...
}

// ✅ Job scheduler creato automaticamente!
```

### Visualizzare Logs

```javascript
const response = await fetch('/api/v1/admin/data-collection/execution-logs?limit=50', {
  headers: { 'Authorization': `Bearer ${token}` }
});

const logs = await response.json();

// Mostra in tabella:
logs.forEach(log => {
  console.log(`${log.symbol}: ${log.status} in ${log.duration_seconds}s`);
});
```

### Dashboard Overview

```javascript
const response = await fetch('/api/v1/admin/data-collection/status', {
  headers: { 'Authorization': `Bearer ${token}` }
});

const data = await response.json();

// Mostra:
// - data.total_configs
// - data.enabled_configs
// - data.stats.success_rate
// - data.recent_executions (array)
```

---

## 📝 Validazione Form

```javascript
// Timeframes validi
const VALID_TIMEFRAMES = [
  '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', 
  '6h', '8h', '12h', '1d', '3d', '1w', '1M'
];

// Validazione
if (!symbol.includes('/')) {
  error = 'Symbol must be in format BASE/QUOTE (e.g., BTC/USDT)';
}

if (interval_minutes < 1 || interval_minutes > 1440) {
  error = 'Interval must be between 1 and 1440 minutes';
}

if (timeframes.length === 0) {
  error = 'Select at least one timeframe';
}
```

---

## 🎯 Quick Implementation

**3 pagine minime:**

1. **Dashboard** - `GET /status`
2. **Configs** - `GET /configs`, `POST /configs`, `DELETE /configs/{id}`
3. **Logs** - `GET /execution-logs`

Dettagli completi con codice React in: **`FRONTEND_DATA_COLLECTION_SPEC.md`**

---

## 🔧 Test Endpoint

Dopo deploy, testa con:

```bash
# Login
curl -X POST https://your-app.herokuapp.com/api/v1/auth/login \
  -d '{"email":"admin@test.com","password":"password"}'

# Get status
curl https://your-app.herokuapp.com/api/v1/admin/data-collection/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Oppure usa Swagger: `https://your-app.herokuapp.com/docs` → tag **data-collection-admin**

---

**File completo con tutti i dettagli:** `FRONTEND_DATA_COLLECTION_SPEC.md` 📄

