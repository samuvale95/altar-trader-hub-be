# 📋 Frontend Spec - Data Collection Management

Specifiche complete per implementare l'interfaccia di gestione raccolta dati crypto.

## 🎯 Overview

Il backend ora supporta **gestione dinamica della raccolta dati crypto** completamente via API.

**Features disponibili:**
- ✅ Aggiungere/rimuovere simboli da raccogliere
- ✅ Configurare exchange, timeframes, intervallo
- ✅ Enable/disable raccolta per simbolo
- ✅ Trigger manuale raccolta dati
- ✅ Visualizzare log di tutte le esecuzioni (start, end, duration, errors)
- ✅ Statistiche real-time (success rate, durata media, records raccolti)

---

## 📡 API Endpoints

Base URL: `https://your-app.herokuapp.com/api/v1/admin/data-collection`

Tutti gli endpoint richiedono autenticazione JWT:
```javascript
headers: {
  'Authorization': 'Bearer YOUR_JWT_TOKEN'
}
```

---

### 1. Dashboard Overview

**`GET /status`**

Restituisce overview completo del sistema di raccolta dati.

**Response:**
```json
{
  "total_configs": 5,
  "enabled_configs": 4,
  "disabled_configs": 1,
  "active_jobs": 4,
  "recent_executions": [
    {
      "id": 1234,
      "job_name": "collect_data_1",
      "symbol": "BTC/USDT",
      "started_at": "2025-01-15T14:30:00Z",
      "finished_at": "2025-01-15T14:30:03Z",
      "duration_seconds": 3.2,
      "status": "success",
      "records_collected": 6
    }
  ],
  "stats": {
    "total_executions": 144,
    "successful_executions": 142,
    "failed_executions": 2,
    "running_executions": 0,
    "success_rate": 98.61,
    "average_duration_seconds": 3.5,
    "total_records_collected": 864,
    "last_execution": "2025-01-15T14:30:00Z"
  }
}
```

**UI Suggestion:**
```
┌─────────────────────────────────────────┐
│  Data Collection Dashboard               │
├─────────────────────────────────────────┤
│  📊 Overview                             │
│  • Active Configurations: 4/5            │
│  • Active Jobs: 4                        │
│  • Success Rate: 98.61%                  │
│  • Records Today: 864                    │
│  • Last Run: 2 minutes ago               │
├─────────────────────────────────────────┤
│  [View Configurations] [View Logs]       │
└─────────────────────────────────────────┘
```

---

### 2. Lista Configurazioni

**`GET /configs?enabled=true&exchange=binance&skip=0&limit=100`**

Lista tutte le configurazioni di raccolta dati.

**Query Params:**
- `enabled`: boolean (optional) - Filtra per enabled/disabled
- `exchange`: string (optional) - Filtra per exchange
- `skip`: int (default 0) - Pagination offset
- `limit`: int (default 100, max 100) - Pagination limit

**Response:**
```json
[
  {
    "id": 1,
    "symbol": "BTC/USDT",
    "exchange": "binance",
    "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
    "interval_minutes": 10,
    "enabled": true,
    "job_id": "collect_data_1",
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T12:00:00Z",
    "description": "Bitcoin price tracking",
    "created_by": 1
  }
]
```

**UI Suggestion:**
```
┌─────────────────────────────────────────────────────────────┐
│  Data Collection Configurations                             │
├─────────────────────────────────────────────────────────────┤
│  [+ Add New Configuration]                [🔍 Search]       │
├──────┬──────────┬─────────┬──────────────┬──────┬──────────┤
│Status│ Symbol   │Exchange │ Timeframes   │Interval│ Actions│
├──────┼──────────┼─────────┼──────────────┼──────┼──────────┤
│  ✅  │BTC/USDT  │binance  │1m,5m,1h,1d   │10min │[▶][✏️][🗑️]│
│  ✅  │ETH/USDT  │binance  │1m,5m,1h      │10min │[▶][✏️][🗑️]│
│  ❌  │SOL/USDT  │binance  │1h,1d         │30min │[▶][✏️][🗑️]│
└──────┴──────────┴─────────┴──────────────┴──────┴──────────┘

Legend:
[▶] = Trigger Now (POST /configs/{id}/trigger)
[✏️] = Edit (PUT /configs/{id})
[🗑️] = Delete (DELETE /configs/{id})
```

---

### 3. Crea Nuova Configurazione

**`POST /configs`**

Crea nuova configurazione e avvia job automaticamente.

**Request:**
```json
{
  "symbol": "ETH/USDT",
  "exchange": "binance",
  "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
  "interval_minutes": 10,
  "enabled": true,
  "description": "Ethereum price tracking"
}
```

**Validation:**
- `symbol`: Required, format "BASE/QUOTE" (e.g., "BTC/USDT")
- `exchange`: Required, default "binance"
- `timeframes`: Required, array of valid timeframes
  - Valid: `1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `6h`, `8h`, `12h`, `1d`, `3d`, `1w`, `1M`
- `interval_minutes`: Required, 1-1440 (1 min to 24 hours)
- `enabled`: Optional, default true
- `description`: Optional, max 200 chars

**Response:**
```json
{
  "id": 5,
  "symbol": "ETH/USDT",
  "exchange": "binance",
  "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
  "interval_minutes": 10,
  "enabled": true,
  "job_id": "collect_data_5",
  "created_at": "2025-01-15T15:00:00Z",
  "description": "Ethereum price tracking"
}
```

**UI Suggestion - Form:**
```
┌──────────────────────────────────────┐
│  Add Data Collection Configuration    │
├──────────────────────────────────────┤
│  Symbol: [BTC/USDT        ▼]         │
│  Exchange: [binance       ▼]         │
│                                       │
│  Timeframes:                          │
│  ☑ 1m   ☑ 5m   ☑ 15m  ☑ 1h          │
│  ☑ 4h   ☑ 1d   ☐ 1w   ☐ 1M          │
│                                       │
│  Interval: [10] minutes               │
│  Slider: [1min]───●────[1440min]     │
│                                       │
│  Description (optional):              │
│  [Bitcoin price tracking...]          │
│                                       │
│  ☑ Enable immediately                 │
│                                       │
│  [Cancel]  [Create Configuration]     │
└──────────────────────────────────────┘
```

---

### 4. Aggiorna Configurazione

**`PUT /configs/{config_id}`**

Aggiorna configurazione esistente e job scheduler.

**Request (partial update):**
```json
{
  "interval_minutes": 5,
  "timeframes": ["1m", "1h", "1d"]
}
```

**Response:** Config aggiornata

⚡ **Il job scheduler viene aggiornato automaticamente in background!**

---

### 5. Enable/Disable

**`POST /configs/{config_id}/enable`**  
Abilita config e avvia job scheduler.

**`POST /configs/{config_id}/disable`**  
Disabilita config e ferma job scheduler.

**Response:** Config aggiornata

**UI Suggestion:**
```javascript
// Toggle switch
<Switch 
  checked={config.enabled}
  onChange={async (checked) => {
    const endpoint = checked ? 'enable' : 'disable';
    await fetch(`/api/v1/admin/data-collection/configs/${config.id}/${endpoint}`, {
      method: 'POST'
    });
  }}
/>
```

---

### 6. Trigger Manuale

**`POST /configs/{config_id}/trigger`**

Esegue raccolta dati immediatamente, senza aspettare scheduler.

**Response:**
```json
{
  "message": "Data collection triggered for BTC/USDT",
  "config_id": 1
}
```

**UI Suggestion:**
```javascript
<Button onClick={() => triggerCollection(configId)}>
  ▶️ Run Now
</Button>

// Mostra loading spinner
// Dopo 3-5 secondi, ricarica execution logs
```

---

### 7. Job Execution Logs

**`GET /execution-logs?symbol=BTC/USDT&status=success&limit=50`**

Lista log di tutte le esecuzioni job.

**Query Params:**
- `job_name`: string (optional)
- `job_type`: string (optional) - "data_collection", "cleanup", "strategy"
- `symbol`: string (optional)
- `status`: string (optional) - "running", "success", "failed"
- `start_date`: datetime (optional)
- `end_date`: datetime (optional)
- `skip`: int (default 0)
- `limit`: int (default 100, max 1000)

**Response:**
```json
[
  {
    "id": 5678,
    "job_name": "collect_data_1",
    "job_type": "data_collection",
    "symbol": "BTC/USDT",
    "exchange": "binance",
    "timeframe": null,
    "started_at": "2025-01-15T14:30:00Z",
    "finished_at": "2025-01-15T14:30:03Z",
    "duration_seconds": 3.2,
    "status": "success",
    "records_collected": 6,
    "error_message": null,
    "error_type": null,
    "metadata": {
      "timeframes_collected": 6,
      "timeframes_failed": 0,
      "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"]
    }
  }
]
```

**UI Suggestion - Log Table:**
```
┌─────────────────────────────────────────────────────────────────────┐
│  Job Execution Logs                                [Filter ▼]       │
├──────┬──────────┬─────────────────┬────────┬────────┬────────┬─────┤
│Symbol│ Started  │    Duration     │ Status │Records │Actions │     │
├──────┼──────────┼─────────────────┼────────┼────────┼────────┼─────┤
│BTC/  │14:30:00  │ ████████ 3.2s  │   ✅   │   6    │[👁️]    │     │
│USDT  │          │                 │        │        │        │     │
├──────┼──────────┼─────────────────┼────────┼────────┼────────┼─────┤
│ETH/  │14:20:00  │ ███████  2.8s  │   ✅   │   4    │[👁️]    │     │
│USDT  │          │                 │        │        │        │     │
├──────┼──────────┼─────────────────┼────────┼────────┼────────┼─────┤
│SOL/  │14:10:00  │ ████     1.5s  │   ❌   │   0    │[👁️]    │     │
│USDT  │          │                 │  (err) │        │        │     │
└──────┴──────────┴─────────────────┴────────┴────────┴────────┴─────┘

Color coding:
✅ Green = success
❌ Red = failed
⏳ Yellow = running
```

---

### 8. Statistiche

**`GET /stats?job_type=data_collection&hours=24`**

Statistiche aggregate esecuzioni job.

**Query Params:**
- `job_type`: string (optional) - Filtra per tipo job
- `hours`: int (default 24, max 720) - Ore da analizzare

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

**UI Suggestion - Cards:**
```
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ Total Runs    │ │ Success Rate  │ │ Avg Duration  │ │ Records/Day   │
│               │ │               │ │               │ │               │
│     144       │ │   98.61%      │ │    3.5s       │ │     864       │
│               │ │               │ │               │ │               │
│  ↑ 12% today  │ │  ✅ Excellent │ │  ⚡ Fast      │ │  ↑ 5% today   │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
```

**UI Suggestion - Charts:**
```javascript
// Chart.js / Recharts
// 1. Success rate over time (line chart)
// 2. Duration trend (area chart)
// 3. Records collected per hour (bar chart)
// 4. Failed jobs by symbol (pie chart)
```

---

## 🎨 UI/UX Suggestions

### Pagina 1: Dashboard

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│  🎛️ Data Collection Control Center                   │
├──────────────────────────────────────────────────────┤
│                                                       │
│  [Stats Cards: 4 cards in row]                       │
│                                                       │
│  ┌─────────────────────┐  ┌─────────────────────┐   │
│  │  Success Rate Chart │  │ Duration Trend      │   │
│  │  (last 24h)         │  │ (last 7 days)       │   │
│  └─────────────────────┘  └─────────────────────┘   │
│                                                       │
│  Recent Executions (Last 10)                         │
│  [Table with latest logs]                            │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### Pagina 2: Configurazioni

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│  📊 Data Collection Configurations                   │
├──────────────────────────────────────────────────────┤
│                                                       │
│  [+ Add New]  [Filter ▼]  [Search: ______]          │
│                                                       │
│  ┌─────────────────────────────────────────┐         │
│  │ Symbol    │ Exchange │ Interval │Actions│         │
│  ├───────────┼──────────┼──────────┼───────┤         │
│  │ BTC/USDT  │ Binance  │ 10min    │[⚙️][▶]│         │
│  │ ✅ Enabled│ 6 TFs    │ Next: 5m │       │         │
│  ├───────────┼──────────┼──────────┼───────┤         │
│  │ ETH/USDT  │ Binance  │ 10min    │[⚙️][▶]│         │
│  │ ✅ Enabled│ 4 TFs    │ Next: 8m │       │         │
│  └─────────────────────────────────────────┘         │
│                                                       │
└──────────────────────────────────────────────────────┘

Actions:
[⚙️] = Edit configuration
[▶] = Trigger now
Toggle = Enable/Disable
```

### Pagina 3: Execution Logs

**Layout:**
```
┌──────────────────────────────────────────────────────┐
│  📝 Execution Logs                                   │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Filters:                                            │
│  Symbol: [All ▼] Status: [All ▼] Date: [Last 7d ▼] │
│                                                       │
│  ┌───────────────────────────────────────────┐       │
│  │Time      │Symbol   │Duration│Status│Details│      │
│  ├──────────┼─────────┼────────┼──────┼───────┤      │
│  │14:30:00  │BTC/USDT │  3.2s  │  ✅  │ [👁️]  │      │
│  │14:20:00  │ETH/USDT │  2.8s  │  ✅  │ [👁️]  │      │
│  │14:10:00  │SOL/USDT │  1.5s  │  ❌  │ [👁️]  │      │
│  └──────────┴─────────┴────────┴──────┴───────┘      │
│                                                       │
│  [Load More]                    Showing 1-20 of 500  │
└──────────────────────────────────────────────────────┘

Click [👁️] to see:
- Full error message (if failed)
- Metadata (timeframes collected)
- Exact timestamps
```

---

## 💻 Esempi Codice Frontend

### React Hook per Data Collection

```typescript
// useDataCollection.ts

import { useState, useEffect } from 'react';

interface DataCollectionConfig {
  id: number;
  symbol: string;
  exchange: string;
  timeframes: string[];
  interval_minutes: number;
  enabled: boolean;
  job_id: string;
  description?: string;
}

interface JobExecutionLog {
  id: number;
  symbol: string;
  started_at: string;
  finished_at?: string;
  duration_seconds?: number;
  status: 'running' | 'success' | 'failed';
  records_collected?: number;
  error_message?: string;
}

interface Stats {
  success_rate: number;
  total_executions: number;
  average_duration_seconds?: number;
  total_records_collected?: number;
}

export function useDataCollection() {
  const [configs, setConfigs] = useState<DataCollectionConfig[]>([]);
  const [logs, setLogs] = useState<JobExecutionLog[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchConfigs = async () => {
    const response = await fetch('/api/v1/admin/data-collection/configs', {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    const data = await response.json();
    setConfigs(data);
  };

  const fetchLogs = async (limit = 50) => {
    const response = await fetch(
      `/api/v1/admin/data-collection/execution-logs?limit=${limit}`,
      { headers: { 'Authorization': `Bearer ${getToken()}` } }
    );
    const data = await response.json();
    setLogs(data);
  };

  const fetchStats = async (hours = 24) => {
    const response = await fetch(
      `/api/v1/admin/data-collection/stats?hours=${hours}`,
      { headers: { 'Authorization': `Bearer ${getToken()}` } }
    );
    const data = await response.json();
    setStats(data);
  };

  const createConfig = async (config: Omit<DataCollectionConfig, 'id' | 'job_id' | 'created_at'>) => {
    const response = await fetch('/api/v1/admin/data-collection/configs', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(config)
    });
    
    if (!response.ok) throw new Error('Failed to create config');
    
    const newConfig = await response.json();
    setConfigs([...configs, newConfig]);
    return newConfig;
  };

  const updateConfig = async (id: number, updates: Partial<DataCollectionConfig>) => {
    const response = await fetch(`/api/v1/admin/data-collection/configs/${id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    });
    
    if (!response.ok) throw new Error('Failed to update config');
    
    const updatedConfig = await response.json();
    setConfigs(configs.map(c => c.id === id ? updatedConfig : c));
    return updatedConfig;
  };

  const deleteConfig = async (id: number) => {
    const response = await fetch(`/api/v1/admin/data-collection/configs/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    
    if (!response.ok) throw new Error('Failed to delete config');
    
    setConfigs(configs.filter(c => c.id !== id));
  };

  const toggleConfig = async (id: number, enable: boolean) => {
    const endpoint = enable ? 'enable' : 'disable';
    const response = await fetch(
      `/api/v1/admin/data-collection/configs/${id}/${endpoint}`,
      {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getToken()}` }
      }
    );
    
    if (!response.ok) throw new Error('Failed to toggle config');
    
    const updatedConfig = await response.json();
    setConfigs(configs.map(c => c.id === id ? updatedConfig : c));
  };

  const triggerNow = async (id: number) => {
    const response = await fetch(
      `/api/v1/admin/data-collection/configs/${id}/trigger`,
      {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getToken()}` }
      }
    );
    
    if (!response.ok) throw new Error('Failed to trigger collection');
    
    // Refresh logs after 5 seconds to see new execution
    setTimeout(fetchLogs, 5000);
    
    return await response.json();
  };

  useEffect(() => {
    Promise.all([fetchConfigs(), fetchLogs(), fetchStats()])
      .finally(() => setLoading(false));

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchLogs();
      fetchStats();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  return {
    configs,
    logs,
    stats,
    loading,
    createConfig,
    updateConfig,
    deleteConfig,
    toggleConfig,
    triggerNow,
    refresh: () => Promise.all([fetchConfigs(), fetchLogs(), fetchStats()])
  };
}
```

---

## 🎨 Component Examples

### Dashboard Component

```tsx
// DataCollectionDashboard.tsx

import { useDataCollection } from './useDataCollection';
import { StatsCard } from './StatsCard';
import { LogsTable } from './LogsTable';

export function DataCollectionDashboard() {
  const { stats, logs, loading } = useDataCollection();

  if (loading) return <Spinner />;

  return (
    <div className="dashboard">
      <h1>Data Collection Dashboard</h1>

      {/* Stats Cards */}
      <div className="stats-grid">
        <StatsCard
          title="Total Runs"
          value={stats?.total_executions}
          icon="📊"
        />
        <StatsCard
          title="Success Rate"
          value={`${stats?.success_rate}%`}
          status={stats?.success_rate > 95 ? 'good' : 'warning'}
          icon="✅"
        />
        <StatsCard
          title="Avg Duration"
          value={`${stats?.average_duration_seconds?.toFixed(1)}s`}
          icon="⚡"
        />
        <StatsCard
          title="Records Today"
          value={stats?.total_records_collected}
          icon="💾"
        />
      </div>

      {/* Recent Logs */}
      <LogsTable logs={logs.slice(0, 10)} />
    </div>
  );
}
```

### Config List Component

```tsx
// ConfigList.tsx

import { useDataCollection } from './useDataCollection';

export function ConfigList() {
  const { configs, toggleConfig, triggerNow, deleteConfig } = useDataCollection();
  const [selectedConfig, setSelectedConfig] = useState(null);

  return (
    <div>
      <div className="header">
        <h1>Data Collection Configurations</h1>
        <button onClick={() => setShowCreateModal(true)}>
          + Add New Configuration
        </button>
      </div>

      <table>
        <thead>
          <tr>
            <th>Status</th>
            <th>Symbol</th>
            <th>Exchange</th>
            <th>Timeframes</th>
            <th>Interval</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {configs.map(config => (
            <tr key={config.id}>
              <td>
                <Switch
                  checked={config.enabled}
                  onChange={(checked) => toggleConfig(config.id, checked)}
                />
              </td>
              <td><strong>{config.symbol}</strong></td>
              <td>{config.exchange}</td>
              <td>
                <Badge>{config.timeframes.length} timeframes</Badge>
                <Tooltip>{config.timeframes.join(', ')}</Tooltip>
              </td>
              <td>{config.interval_minutes}min</td>
              <td>
                <button onClick={() => triggerNow(config.id)}>▶️ Run Now</button>
                <button onClick={() => setSelectedConfig(config)}>✏️ Edit</button>
                <button onClick={() => deleteConfig(config.id)}>🗑️</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### Create/Edit Modal

```tsx
// ConfigModal.tsx

import { useState } from 'react';

const AVAILABLE_TIMEFRAMES = [
  '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', 
  '6h', '8h', '12h', '1d', '3d', '1w', '1M'
];

export function ConfigModal({ config, onSave, onClose }) {
  const [symbol, setSymbol] = useState(config?.symbol || '');
  const [exchange, setExchange] = useState(config?.exchange || 'binance');
  const [timeframes, setTimeframes] = useState(config?.timeframes || ['1h', '1d']);
  const [interval, setInterval] = useState(config?.interval_minutes || 10);
  const [description, setDescription] = useState(config?.description || '');

  const handleSubmit = async () => {
    const data = {
      symbol: symbol.toUpperCase(),
      exchange,
      timeframes,
      interval_minutes: interval,
      enabled: true,
      description
    };

    await onSave(data);
    onClose();
  };

  return (
    <Modal>
      <h2>{config ? 'Edit' : 'Create'} Configuration</h2>

      <FormGroup>
        <label>Symbol (e.g., BTC/USDT)</label>
        <input 
          value={symbol}
          onChange={e => setSymbol(e.target.value)}
          placeholder="BTC/USDT"
        />
      </FormGroup>

      <FormGroup>
        <label>Exchange</label>
        <select value={exchange} onChange={e => setExchange(e.target.value)}>
          <option value="binance">Binance</option>
          <option value="kraken">Kraken</option>
          <option value="kucoin">KuCoin</option>
        </select>
      </FormGroup>

      <FormGroup>
        <label>Timeframes</label>
        <div className="checkbox-grid">
          {AVAILABLE_TIMEFRAMES.map(tf => (
            <label key={tf}>
              <input
                type="checkbox"
                checked={timeframes.includes(tf)}
                onChange={e => {
                  if (e.target.checked) {
                    setTimeframes([...timeframes, tf]);
                  } else {
                    setTimeframes(timeframes.filter(t => t !== tf));
                  }
                }}
              />
              {tf}
            </label>
          ))}
        </div>
      </FormGroup>

      <FormGroup>
        <label>Interval: {interval} minutes</label>
        <input
          type="range"
          min="1"
          max="1440"
          step="5"
          value={interval}
          onChange={e => setInterval(parseInt(e.target.value))}
        />
        <div className="range-labels">
          <span>1min</span>
          <span>6h</span>
          <span>24h</span>
        </div>
      </FormGroup>

      <FormGroup>
        <label>Description (optional)</label>
        <input
          value={description}
          onChange={e => setDescription(e.target.value)}
          placeholder="e.g., Bitcoin price tracking"
          maxLength={200}
        />
      </FormGroup>

      <div className="actions">
        <button onClick={onClose}>Cancel</button>
        <button onClick={handleSubmit} className="primary">
          {config ? 'Update' : 'Create'}
        </button>
      </div>
    </Modal>
  );
}
```

---

## 🔄 Real-time Updates

### WebSocket (Optional)

Se vuoi aggiornamenti real-time:

```javascript
// Quando un job finisce, backend può pushare via WebSocket
ws.on('job_completed', (data) => {
  // Update logs list
  setLogs(prevLogs => [data, ...prevLogs]);
  
  // Show notification
  toast.success(`${data.symbol} collection completed in ${data.duration_seconds}s`);
});
```

### Polling (Semplice)

```javascript
// Refresh ogni 30 secondi
useEffect(() => {
  const interval = setInterval(() => {
    fetchLogs();
    fetchStats();
  }, 30000);

  return () => clearInterval(interval);
}, []);
```

---

## 📊 Grafici Consigliati

### 1. Success Rate Trend (Line Chart)

```javascript
// X-axis: Time (hourly)
// Y-axis: Success % (0-100%)
// Color: Green if >95%, Yellow if 90-95%, Red if <90%
```

### 2. Duration by Symbol (Bar Chart)

```javascript
// X-axis: Symbol
// Y-axis: Avg duration (seconds)
// Tooltip: Min/Max/Avg duration
```

### 3. Records Collected (Area Chart)

```javascript
// X-axis: Time (daily)
// Y-axis: Total records collected
// Stacked by symbol
```

### 4. Failed Jobs Distribution (Pie Chart)

```javascript
// Slices: Failed jobs by error type
// Click slice → filter logs by error type
```

---

## ⚡ Performance Tips

### 1. Pagination

```javascript
// Infinite scroll per logs
const [page, setPage] = useState(0);
const LIMIT = 50;

const fetchMoreLogs = async () => {
  const response = await fetch(
    `/execution-logs?skip=${page * LIMIT}&limit=${LIMIT}`
  );
  const newLogs = await response.json();
  setLogs([...logs, ...newLogs]);
  setPage(page + 1);
};
```

### 2. Caching

```javascript
// Cache stats per 1 minuto
const { data: stats } = useSWR(
  '/api/v1/admin/data-collection/stats',
  fetcher,
  { refreshInterval: 60000 }  // 1 min
);
```

### 3. Lazy Loading Charts

```javascript
// Carica chart data solo quando visibili
const { ref, inView } = useInView();

{inView && <DurationChart data={stats} />}
```

---

## 🎯 User Flow

### Aggiungere Nuovo Simbolo

```
1. User clicca "+ Add New Configuration"
   ↓
2. Compila form:
   - Symbol: SOL/USDT
   - Exchange: binance
   - Timeframes: [1m, 5m, 1h]
   - Interval: 10 minutes
   ↓
3. Click "Create"
   ↓
4. POST /configs
   ↓
5. Backend:
   - Salva config in DB
   - Crea job scheduler automaticamente
   ↓
6. Frontend:
   - Mostra success notification
   - Aggiunge config alla tabella
   - Dopo 10 min, apparirà primo log
```

### Modificare Intervallo

```
1. User clicca "Edit" su config esistente
   ↓
2. Modifica intervallo: 10min → 5min
   ↓
3. Click "Update"
   ↓
4. PUT /configs/{id}
   ↓
5. Backend aggiorna job scheduler automaticamente
   ↓
6. Prossima esecuzione sarà tra 5min invece che 10min
```

### Trigger Manuale

```
1. User clicca "▶️ Run Now"
   ↓
2. POST /configs/{id}/trigger
   ↓
3. Backend esegue immediatamente (async)
   ↓
4. Dopo 3-5 sec, nuovo log appare
   ↓
5. Frontend auto-refresh logs
```

---

## 🐛 Error Handling

### Display Errors

```tsx
{log.status === 'failed' && (
  <Alert severity="error">
    <AlertTitle>Collection Failed</AlertTitle>
    <strong>Error:</strong> {log.error_message}
    <br />
    <strong>Type:</strong> {log.error_type}
    <br />
    <button onClick={() => retryCollection(log.config_id)}>
      🔄 Retry Now
    </button>
  </Alert>
)}
```

### Validation Errors

```tsx
try {
  await createConfig(formData);
} catch (error) {
  if (error.response?.status === 400) {
    // Validation error
    const detail = error.response.data.detail;
    setError(detail);  // "Symbol must be in format BASE/QUOTE"
  }
}
```

---

## 📱 Mobile Responsive

```css
/* Desktop */
.stats-grid {
  grid-template-columns: repeat(4, 1fr);
}

/* Tablet */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Mobile */
@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  table {
    display: block;
    overflow-x: auto;
  }
}
```

---

## ✅ Checklist Frontend

- [ ] Dashboard overview con stats cards
- [ ] Tabella configurazioni con CRUD
- [ ] Modal create/edit configuration
- [ ] Enable/disable toggle
- [ ] Trigger now button
- [ ] Tabella execution logs con filtri
- [ ] Dettaglio log (modal o drawer)
- [ ] Grafici statistiche
- [ ] Auto-refresh ogni 30s
- [ ] Error handling e notifications
- [ ] Loading states
- [ ] Mobile responsive
- [ ] Search/filter per symbol
- [ ] Pagination logs

---

## 🎁 Bonus Features

### 1. Notifiche

```javascript
// Quando job fallisce
if (log.status === 'failed') {
  toast.error(`${log.symbol} collection failed: ${log.error_message}`);
}

// Quando success rate scende
if (stats.success_rate < 90) {
  toast.warning('Success rate below 90%! Check failed jobs.');
}
```

### 2. Bulk Actions

```javascript
// Enable multiple configs
const enableMultiple = async (configIds: number[]) => {
  await Promise.all(
    configIds.map(id => toggleConfig(id, true))
  );
};
```

### 3. Export Logs

```javascript
// Export to CSV
const exportLogs = () => {
  const csv = logs.map(log => 
    `${log.symbol},${log.started_at},${log.duration_seconds},${log.status}`
  ).join('\n');
  
  downloadFile(csv, 'execution-logs.csv');
};
```

---

## 🚀 Quick Start Frontend

```bash
# 1. Crea pagina/route
/admin/data-collection

# 2. Crea components
- DataCollectionDashboard
- ConfigList
- ConfigModal
- LogsTable
- StatsCards

# 3. Setup API calls
- Use fetch or axios
- Add JWT token to headers

# 4. Test con backend locale
npm run dev
```

---

## 📚 API Full Documentation

Tutti gli endpoint sono documentati su:
```
https://your-app.herokuapp.com/docs#tag/data-collection-admin
```

Swagger UI interattivo con:
- Schema completi
- Esempi request/response
- Try it out

---

## 🆘 Support

Per domande o problemi:
1. Controlla `DATA_COLLECTION_ADMIN_GUIDE.md`
2. Testa API su `/docs`
3. Verifica logs: `heroku logs --tail`

---

**✨ Backend pronto! Buon lavoro con il frontend! 🚀**

