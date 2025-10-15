# 📋 Per Frontend Team - Nuove API Data Collection

## 🆕 Cosa È Stato Aggiunto

Sistema per **gestire dinamicamente la raccolta dati crypto** con tracking completo delle esecuzioni.

---

## 📡 Nuove API (10 Endpoint)

**Base URL:** `/api/v1/admin/data-collection`  
**Auth:** Richiede JWT token (come altre API admin)

### Gestione Configurazioni

| Method | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/configs` | Lista configurazioni |
| POST | `/configs` | Crea config + avvia job |
| PUT | `/configs/{id}` | Aggiorna config + aggiorna job |
| DELETE | `/configs/{id}` | Elimina config + ferma job |
| POST | `/configs/{id}/enable` | Attiva raccolta |
| POST | `/configs/{id}/disable` | Disattiva raccolta |
| POST | `/configs/{id}/trigger` | Esegui ora (manuale) |

### Logs & Statistiche

| Method | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/execution-logs` | Log esecuzioni (filtrabili) |
| GET | `/stats` | Statistiche aggregate |
| GET | `/status` | Dashboard overview |

---

## 📊 Data Models

```typescript
// Configurazione raccolta dati
interface DataCollectionConfig {
  id: number;
  symbol: string;              // "BTC/USDT"
  exchange: string;            // "binance", "kraken", "kucoin"
  timeframes: string[];        // ["1m", "5m", "1h", "1d"]
  interval_minutes: number;    // 10
  enabled: boolean;
  job_id: string | null;
  created_at: string;
  description?: string;
}

// Log esecuzione job
interface JobExecutionLog {
  id: number;
  symbol: string;
  started_at: string;          // ISO datetime
  finished_at?: string;        // ISO datetime
  duration_seconds?: number;   // 3.2
  status: 'running' | 'success' | 'failed';
  records_collected?: number;  // 6
  error_message?: string;      // Se failed
}

// Statistiche
interface Stats {
  total_executions: number;
  success_rate: number;        // 98.5
  average_duration_seconds?: number;
  total_records_collected?: number;
}
```

---

## 💻 Esempi Chiamate

### 1. Dashboard Overview

```javascript
const response = await fetch('/api/v1/admin/data-collection/status', {
  headers: { 'Authorization': `Bearer ${token}` }
});

const data = await response.json();
// {
//   total_configs: 5,
//   enabled_configs: 4,
//   active_jobs: 4,
//   recent_executions: [...],  // Last 10 logs
//   stats: { success_rate: 98.5, ... }
// }
```

### 2. Aggiungi Simbolo

```javascript
const response = await fetch('/api/v1/admin/data-collection/configs', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    symbol: 'BTC/USDT',
    exchange: 'binance',
    timeframes: ['1m', '5m', '1h', '1d'],
    interval_minutes: 10,
    enabled: true,
    description: 'Bitcoin tracking'
  })
});

// ✅ Job scheduler creato automaticamente!
```

### 3. Visualizza Logs

```javascript
const response = await fetch('/api/v1/admin/data-collection/execution-logs?limit=50', {
  headers: { 'Authorization': `Bearer ${token}` }
});

const logs = await response.json();
// [{
//   symbol: "BTC/USDT",
//   started_at: "2025-01-15T14:30:00Z",
//   finished_at: "2025-01-15T14:30:03Z",
//   duration_seconds: 3.2,
//   status: "success",
//   records_collected: 6
// }]
```

---

## 🎨 UI da Implementare

### Pagina 1: Dashboard
- 4 cards con stats (total runs, success rate, avg duration, records)
- Tabella con ultimi 10 log

**Chiamata:** `GET /status`

### Pagina 2: Gestione Configurazioni
- Tabella configurazioni attive
- Button "+ Add New"
- Toggle enable/disable
- Button "Run Now" per trigger manuale
- Edit/Delete actions

**Chiamate:** `GET /configs`, `POST /configs`, `PUT /configs/{id}`, `DELETE /configs/{id}`

### Pagina 3: Execution Logs
- Tabella logs con filtri (symbol, status, date)
- Pagination
- Detail view per errors

**Chiamata:** `GET /execution-logs?symbol=BTC&status=success&limit=50`

---

## ⚡ Quick Integration

```jsx
// Esempio React Hook
const [configs, setConfigs] = useState([]);
const [logs, setLogs] = useState([]);

useEffect(() => {
  // Carica configurazioni
  fetch('/api/v1/admin/data-collection/configs')
    .then(res => res.json())
    .then(data => setConfigs(data));

  // Carica logs
  fetch('/api/v1/admin/data-collection/execution-logs?limit=50')
    .then(res => res.json())
    .then(data => setLogs(data));
}, []);

// Aggiungi simbolo
const addSymbol = async (symbol, timeframes, interval) => {
  await fetch('/api/v1/admin/data-collection/configs', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      symbol,
      exchange: 'binance',
      timeframes,
      interval_minutes: interval,
      enabled: true
    })
  });
  
  // Ricarica configs
  // Dopo 10 minuti vedrai il primo log!
};
```

---

## ✅ Validazione Form

```javascript
// Timeframes validi
const TIMEFRAMES = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'];

// Symbol format
if (!symbol.includes('/')) {
  error = 'Symbol must be format BASE/QUOTE (e.g., BTC/USDT)';
}

// Interval range
if (interval < 1 || interval > 1440) {
  error = 'Interval must be 1-1440 minutes';
}
```

---

## 🧪 Test API

Swagger UI: `https://your-app.herokuapp.com/docs`  
Tag: **data-collection-admin**

---

## 📚 Documentazione Completa

- `FRONTEND_DATA_COLLECTION_SPEC.md` - Spec completa con codice React/TS ⭐
- `DATA_COLLECTION_ADMIN_GUIDE.md` - Guida backend dettagliata

---

**That's it!** 3 pagine UI + 10 endpoint API = Sistema completo! 🚀

