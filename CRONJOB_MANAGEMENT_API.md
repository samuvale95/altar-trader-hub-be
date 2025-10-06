# Cronjob Management API

## 🎯 Overview

API endpoints per gestire i cronjob di raccolta dati cripto da interfaccia grafica.

## 📋 Endpoints Disponibili

### **1. Stato Cronjob**
```http
GET /api/v1/cronjob/status
```

**Response:**
```json
{
  "is_running": true,
  "config": {
    "main_symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"],
    "timeframes": ["1m", "5m", "1h"],
    "intervals": {
      "main_collection": 30,
      "high_volume": 300,
      "symbol_update": 1800,
      "status_report": 600
    }
  },
  "statistics": {
    "total_executions": 150,
    "last_execution": "2025-09-29T19:30:00",
    "success_count": 148,
    "error_count": 2,
    "start_time": "2025-09-29T18:00:00"
  },
  "active_tasks": ["main_collection", "high_volume"]
}
```

### **2. Avvia Cronjob**
```http
POST /api/v1/cronjob/start
Content-Type: application/json

{
  "main_symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"],
  "timeframes": ["1m", "5m", "1h"],
  "intervals": {
    "main_collection": 30,
    "high_volume": 300
  }
}
```

### **3. Ferma Cronjob**
```http
POST /api/v1/cronjob/stop
```

### **4. Aggiorna Configurazione**
```http
PUT /api/v1/cronjob/config
Content-Type: application/json

{
  "main_symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"],
  "timeframes": ["1m", "5m", "15m", "1h", "4h"],
  "intervals": {
    "main_collection": 60,
    "high_volume": 600,
    "symbol_update": 3600,
    "status_report": 1200
  }
}
```

### **5. Aggiungi Simboli**
```http
POST /api/v1/cronjob/add-symbols
Content-Type: application/json

["SOLUSDT", "MATICUSDT", "AVAXUSDT"]
```

### **6. Rimuovi Simboli**
```http
DELETE /api/v1/cronjob/remove-symbols
Content-Type: application/json

["ADAUSDT", "DOTUSDT"]
```

### **7. Aggiorna Intervalli**
```http
PUT /api/v1/cronjob/intervals
Content-Type: application/json

{
  "main_collection": 60,
  "high_volume": 600
}
```

### **8. Esegui Task Immediatamente**
```http
POST /api/v1/cronjob/execute-now/main_collection
POST /api/v1/cronjob/execute-now/high_volume
POST /api/v1/cronjob/execute-now/symbol_update
POST /api/v1/cronjob/execute-now/status_report
```

### **9. Logs Cronjob**
```http
GET /api/v1/cronjob/logs?limit=100
```

## 🎨 Frontend Integration

### **React Component Example**

```jsx
import React, { useState, useEffect } from 'react';

const CronjobManager = () => {
  const [status, setStatus] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [config, setConfig] = useState({});

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/v1/cronjob/status', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setStatus(data);
      setIsRunning(data.is_running);
      setConfig(data.config);
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };

  const startCronjob = async () => {
    try {
      await fetch('/api/v1/cronjob/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(config)
      });
      fetchStatus();
    } catch (error) {
      console.error('Error starting cronjob:', error);
    }
  };

  const stopCronjob = async () => {
    try {
      await fetch('/api/v1/cronjob/stop', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      fetchStatus();
    } catch (error) {
      console.error('Error stopping cronjob:', error);
    }
  };

  const addSymbols = async (symbols) => {
    try {
      await fetch('/api/v1/cronjob/add-symbols', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(symbols)
      });
      fetchStatus();
    } catch (error) {
      console.error('Error adding symbols:', error);
    }
  };

  const updateIntervals = async (intervals) => {
    try {
      await fetch('/api/v1/cronjob/intervals', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(intervals)
      });
      fetchStatus();
    } catch (error) {
      console.error('Error updating intervals:', error);
    }
  };

  return (
    <div className="cronjob-manager">
      <h2>Cronjob Manager</h2>
      
      <div className="status-section">
        <h3>Status</h3>
        <p>Running: {isRunning ? 'Yes' : 'No'}</p>
        <p>Total Executions: {status?.statistics?.total_executions}</p>
        <p>Success Rate: {status?.statistics?.success_count}/{status?.statistics?.total_executions}</p>
      </div>

      <div className="controls">
        <button onClick={startCronjob} disabled={isRunning}>
          Start Cronjob
        </button>
        <button onClick={stopCronjob} disabled={!isRunning}>
          Stop Cronjob
        </button>
      </div>

      <div className="config-section">
        <h3>Configuration</h3>
        
        <div className="symbols">
          <h4>Symbols ({config?.main_symbols?.length})</h4>
          <div className="symbol-list">
            {config?.main_symbols?.map(symbol => (
              <span key={symbol} className="symbol-tag">{symbol}</span>
            ))}
          </div>
          <button onClick={() => addSymbols(['NEWSYMBOL'])}>
            Add Symbol
          </button>
        </div>

        <div className="intervals">
          <h4>Intervals</h4>
          <div className="interval-controls">
            <label>
              Main Collection (seconds):
              <input 
                type="number" 
                value={config?.intervals?.main_collection}
                onChange={(e) => updateIntervals({
                  main_collection: parseInt(e.target.value)
                })}
              />
            </label>
            <label>
              High Volume (seconds):
              <input 
                type="number" 
                value={config?.intervals?.high_volume}
                onChange={(e) => updateIntervals({
                  high_volume: parseInt(e.target.value)
                })}
              />
            </label>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CronjobManager;
```

### **Vue.js Component Example**

```vue
<template>
  <div class="cronjob-manager">
    <h2>Cronjob Manager</h2>
    
    <div class="status-section">
      <h3>Status</h3>
      <p>Running: {{ isRunning ? 'Yes' : 'No' }}</p>
      <p>Total Executions: {{ status?.statistics?.total_executions }}</p>
    </div>

    <div class="controls">
      <button @click="startCronjob" :disabled="isRunning">
        Start Cronjob
      </button>
      <button @click="stopCronjob" :disabled="!isRunning">
        Stop Cronjob
      </button>
    </div>

    <div class="config-section">
      <h3>Configuration</h3>
      
      <div class="symbols">
        <h4>Symbols ({{ config?.main_symbols?.length }})</h4>
        <div class="symbol-list">
          <span 
            v-for="symbol in config?.main_symbols" 
            :key="symbol" 
            class="symbol-tag"
          >
            {{ symbol }}
          </span>
        </div>
        <button @click="addSymbols(['NEWSYMBOL'])">
          Add Symbol
        </button>
      </div>

      <div class="intervals">
        <h4>Intervals</h4>
        <div class="interval-controls">
          <label>
            Main Collection (seconds):
            <input 
              type="number" 
              :value="config?.intervals?.main_collection"
              @change="updateIntervals({
                main_collection: parseInt($event.target.value)
              })"
            />
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CronjobManager',
  data() {
    return {
      status: null,
      isRunning: false,
      config: {},
      token: localStorage.getItem('token')
    };
  },
  async mounted() {
    await this.fetchStatus();
  },
  methods: {
    async fetchStatus() {
      try {
        const response = await fetch('/api/v1/cronjob/status', {
          headers: {
            'Authorization': `Bearer ${this.token}`
          }
        });
        const data = await response.json();
        this.status = data;
        this.isRunning = data.is_running;
        this.config = data.config;
      } catch (error) {
        console.error('Error fetching status:', error);
      }
    },
    async startCronjob() {
      try {
        await fetch('/api/v1/cronjob/start', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`
          },
          body: JSON.stringify(this.config)
        });
        await this.fetchStatus();
      } catch (error) {
        console.error('Error starting cronjob:', error);
      }
    },
    async stopCronjob() {
      try {
        await fetch('/api/v1/cronjob/stop', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.token}`
          }
        });
        await this.fetchStatus();
      } catch (error) {
        console.error('Error stopping cronjob:', error);
      }
    },
    async addSymbols(symbols) {
      try {
        await fetch('/api/v1/cronjob/add-symbols', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`
          },
          body: JSON.stringify(symbols)
        });
        await this.fetchStatus();
      } catch (error) {
        console.error('Error adding symbols:', error);
      }
    },
    async updateIntervals(intervals) {
      try {
        await fetch('/api/v1/cronjob/intervals', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`
          },
          body: JSON.stringify(intervals)
        });
        await this.fetchStatus();
      } catch (error) {
        console.error('Error updating intervals:', error);
      }
    }
  }
};
</script>
```

## 🎯 Features Principali

### **✅ Controllo Completo:**
- Start/Stop cronjob
- Configurazione dinamica
- Esecuzione manuale task

### **✅ Gestione Simboli:**
- Aggiungi/rimuovi simboli
- Lista simboli attivi
- Validazione simboli

### **✅ Configurazione Intervalli:**
- Intervalli personalizzabili
- Aggiornamento in tempo reale
- Validazione intervalli

### **✅ Monitoraggio:**
- Statistiche in tempo reale
- Logs esecuzione
- Stato task attivi

### **✅ Sicurezza:**
- Autenticazione JWT
- Validazione input
- Gestione errori

## 🚀 Utilizzo

1. **Autenticati** con JWT token
2. **Ottieni stato** corrente del cronjob
3. **Configura** simboli e intervalli
4. **Avvia** il cronjob
5. **Monitora** l'esecuzione
6. **Gestisci** la configurazione dinamicamente

Il sistema è ora completamente gestibile da interfaccia grafica! 🎉

