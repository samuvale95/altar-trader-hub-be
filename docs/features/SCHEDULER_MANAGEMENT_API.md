# Scheduler Management API - Sistema Unificato

## 🎯 **Nuova Architettura Semplificata**

Il sistema è stato semplificato per avere **un solo modo di raccolta dati**: automatico, ma completamente gestibile dal frontend.

### **Caratteristiche:**
- ✅ **Avvio automatico**: Il scheduler parte automaticamente all'avvio dell'app
- ✅ **Gestione completa dal frontend**: Tutti i parametri modificabili via API
- ✅ **Monitoraggio in tempo reale**: Status e progresso sempre disponibili
- ✅ **Controllo start/stop**: Possibilità di abilitare/disabilitare il scheduler
- ✅ **Configurazione dinamica**: Simboli, timeframes e frequenze modificabili

---

## 📡 **API Endpoints**

### **1. Status del Scheduler**
```bash
GET /api/v1/data-collector/status
```

**Risposta:**
```json
{
  "scheduler": {
    "is_running": true,
    "collection_interval": 300,
    "symbol_refresh_interval": 3600,
    "data_collection_running": true,
    "active_tasks_count": 1,
    "scheduler_task_types": ["scheduled_data_collection"]
  },
  "data_feeder": {
    "symbols_count": 10,
    "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT", ...],
    "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"]
  },
  "task_manager": {
    "active_tasks": 1,
    "task_counts": {
      "pending": 0,
      "running": 1,
      "completed": 15,
      "failed": 0,
      "cancelled": 0
    }
  }
}
```

### **2. Configurazione del Scheduler**
```bash
GET /api/v1/data-collector/config
```

**Risposta:**
```json
{
  "collection_interval": 300,
  "symbol_refresh_interval": 3600,
  "is_running": true,
  "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"],
  "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
  "available_symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT", ...]
}
```

### **3. Aggiorna Configurazione**
```bash
PUT /api/v1/data-collector/config
```

**Body (tutti i campi sono opzionali):**
```json
{
  "collection_interval": 600,        // Frequenza raccolta (secondi)
  "symbol_refresh_interval": 1800,   // Frequenza refresh simboli (secondi)
  "symbols": ["BTCUSDT", "ETHUSDT"], // Lista simboli da tracciare
  "timeframes": ["1m", "5m", "1h"],  // Timeframes da raccogliere
  "enabled": true                    // Abilita/disabilita scheduler
}
```

**Risposta:**
```json
{
  "message": "Scheduler configuration updated successfully",
  "config": {
    "collection_interval": 600,
    "symbol_refresh_interval": 1800,
    "is_running": true,
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "timeframes": ["1m", "5m", "1h"]
  }
}
```

### **4. Avvia Scheduler**
```bash
POST /api/v1/data-collector/start
```

**Risposta:**
```json
{
  "message": "Data collection scheduler started successfully"
}
```

### **5. Ferma Scheduler**
```bash
POST /api/v1/data-collector/stop
```

**Risposta:**
```json
{
  "message": "Data collection scheduler stopped successfully"
}
```

### **6. Refresh Simboli**
```bash
POST /api/v1/data-collector/refresh-symbols
```

**Risposta:**
```json
{
  "task_id": "uuid",
  "status": "submitted",
  "message": "Symbol refresh task submitted successfully"
}
```

### **7. Task Management**
```bash
# Lista tutti i task
GET /api/v1/data-collector/tasks

# Solo task attivi
GET /api/v1/data-collector/tasks/active

# Status di un task specifico
GET /api/v1/data-collector/task/{task_id}

# Cancella un task
POST /api/v1/data-collector/task/{task_id}/cancel

# Statistiche task
GET /api/v1/data-collector/tasks/stats
```

---

## ⚙️ **Configurazione Predefinita**

### **Valori di Default:**
```python
collection_interval = 300        # 5 minuti
symbol_refresh_interval = 3600   # 1 ora
symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT", ...]
timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
```

### **Validazioni:**
- **Collection interval**: Minimo 60 secondi (1 minuto)
- **Symbol refresh interval**: Minimo 300 secondi (5 minuti)
- **Symbols**: Almeno 1 simbolo richiesto
- **Timeframes**: Solo valori validi: `['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']`

---

## 🔄 **Flusso di Funzionamento**

### **Avvio Applicazione:**
```
1. App si avvia
2. Data Scheduler parte automaticamente
3. Carica configurazione predefinita
4. Inizia raccolta automatica ogni 5 minuti
5. Refresh simboli ogni ora
```

### **Modifica Configurazione dal Frontend:**
```
1. Frontend chiama PUT /config
2. Backend aggiorna parametri in memoria
3. Prossima esecuzione usa nuova configurazione
4. Log delle modifiche per audit
```

### **Controllo Start/Stop:**
```
1. Frontend chiama POST /start o POST /stop
2. Scheduler viene abilitato/disabilitato
3. Task attivi vengono gestiti correttamente
4. Status aggiornato in tempo reale
```

---

## 📊 **Monitoraggio Frontend**

### **Dashboard Scheduler:**
```javascript
// Esempio di integrazione frontend
const schedulerAPI = {
  // Get current status
  async getStatus() {
    const response = await fetch('/api/v1/data-collector/status');
    return response.json();
  },
  
  // Get configuration
  async getConfig() {
    const response = await fetch('/api/v1/data-collector/config');
    return response.json();
  },
  
  // Update configuration
  async updateConfig(config) {
    const response = await fetch('/api/v1/data-collector/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    return response.json();
  },
  
  // Start scheduler
  async start() {
    const response = await fetch('/api/v1/data-collector/start', {
      method: 'POST'
    });
    return response.json();
  },
  
  // Stop scheduler
  async stop() {
    const response = await fetch('/api/v1/data-collector/stop', {
      method: 'POST'
    });
    return response.json();
  }
};
```

### **Componente React Esempio:**
```jsx
function SchedulerDashboard() {
  const [status, setStatus] = useState(null);
  const [config, setConfig] = useState(null);
  
  useEffect(() => {
    // Polling per aggiornamenti status
    const interval = setInterval(async () => {
      const statusData = await schedulerAPI.getStatus();
      setStatus(statusData);
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);
  
  const handleToggleScheduler = async () => {
    if (status?.scheduler?.is_running) {
      await schedulerAPI.stop();
    } else {
      await schedulerAPI.start();
    }
  };
  
  const handleUpdateConfig = async (newConfig) => {
    await schedulerAPI.updateConfig(newConfig);
    // Refresh config
    const configData = await schedulerAPI.getConfig();
    setConfig(configData);
  };
  
  return (
    <div>
      <h2>Data Collection Scheduler</h2>
      
      <div>
        <h3>Status</h3>
        <p>Running: {status?.scheduler?.is_running ? 'Yes' : 'No'}</p>
        <p>Active Tasks: {status?.scheduler?.active_tasks_count}</p>
        <p>Collection Interval: {status?.scheduler?.collection_interval}s</p>
        
        <button onClick={handleToggleScheduler}>
          {status?.scheduler?.is_running ? 'Stop' : 'Start'} Scheduler
        </button>
      </div>
      
      <div>
        <h3>Configuration</h3>
        <ConfigForm config={config} onUpdate={handleUpdateConfig} />
      </div>
    </div>
  );
}
```

---

## 🎯 **Vantaggi della Nuova Architettura**

### **1. Semplicità:**
- ✅ Un solo sistema di raccolta dati
- ✅ API chiare e intuitive
- ✅ Configurazione centralizzata

### **2. Controllo Totale:**
- ✅ Tutti i parametri modificabili dal frontend
- ✅ Start/stop on-demand
- ✅ Monitoraggio completo

### **3. Affidabilità:**
- ✅ Avvio automatico garantito
- ✅ Gestione errori robusta
- ✅ Recovery automatico

### **4. Flessibilità:**
- ✅ Simboli personalizzabili
- ✅ Timeframes configurabili
- ✅ Frequenze adattabili

### **5. User Experience:**
- ✅ Dashboard intuitiva
- ✅ Controlli in tempo reale
- ✅ Feedback immediato

---

## 🚀 **Esempi Pratici**

### **Scenario 1: Configurazione Iniziale**
```bash
# 1. Verifica status
GET /api/v1/data-collector/status

# 2. Configura simboli personalizzati
PUT /api/v1/data-collector/config
{
  "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
  "timeframes": ["1m", "5m", "1h"]
}

# 3. Modifica frequenza (ogni 10 minuti)
PUT /api/v1/data-collector/config
{
  "collection_interval": 600
}
```

### **Scenario 2: Monitoraggio e Controllo**
```bash
# 1. Verifica se scheduler è attivo
GET /api/v1/data-collector/status

# 2. Se necessario, ferma temporaneamente
POST /api/v1/data-collector/stop

# 3. Modifica configurazione
PUT /api/v1/data-collector/config
{
  "enabled": false
}

# 4. Riattiva quando necessario
PUT /api/v1/data-collector/config
{
  "enabled": true
}
```

### **Scenario 3: Refresh Simboli**
```bash
# 1. Refresh lista simboli disponibili
POST /api/v1/data-collector/refresh-symbols

# 2. Verifica nuovi simboli disponibili
GET /api/v1/data-collector/config

# 3. Aggiorna configurazione con nuovi simboli
PUT /api/v1/data-collector/config
{
  "symbols": ["BTCUSDT", "ETHUSDT", "NEWUSDT"]
}
```

---

## 🎉 **Conclusione**

Il nuovo sistema è molto più semplice e potente:

1. **Un solo modo di raccolta**: Automatico ma controllabile
2. **Gestione completa dal frontend**: Tutti i parametri modificabili
3. **Monitoraggio in tempo reale**: Status sempre aggiornato
4. **API intuitive**: Endpoint chiari e ben documentati
5. **Affidabilità**: Avvio automatico e gestione errori robusta

Ora hai un sistema di data collection completamente gestibile dal frontend! 🚀

