# Data Collection Architecture - Sistema Integrato

## 🎯 **Problema Risolto: Sovrapposizione Scheduler/Collector**

### **Situazione Precedente:**
- ❌ Data Scheduler (automatico) e Data Collector API (manuale) lavoravano indipendentemente
- ❌ Possibili sovrapposizioni e conflitti
- ❌ Metodi diversi (sincrono vs asincrono)
- ❌ Nessuna coordinazione tra i sistemi

### **Nuova Architettura Integrata:**
- ✅ Sistema unificato che usa il Task Manager per entrambi
- ✅ Coordinazione automatica per evitare sovrapposizioni
- ✅ Metodo asincrono unificato
- ✅ Visibilità completa di tutte le operazioni

---

## 🏗️ **Architettura Unificata**

### **1. Task Manager (Centro di Controllo)**
```
Task Manager
├── Gestisce TUTTI i task di data collection
├── Evita sovrapposizioni
├── Tracking progresso unificato
└── API unificata per status
```

### **2. Data Scheduler (Automatico)**
```
Data Scheduler
├── Ogni 5 minuti: Controlla se serve raccolta
├── Ogni 1 ora: Refresh simboli
├── Usa Task Manager per sottomettere task
└── Evita duplicazioni controllando task attivi
```

### **3. Data Collector API (Manuale)**
```
Data Collector API
├── Endpoint per avviare raccolta manuale
├── Usa Task Manager per sottomettere task
├── Controllo granulare (simboli/timeframes specifici)
└── Stesso sistema di tracking del scheduler
```

---

## 🔄 **Flusso Unificato**

### **Raccolta Automatica (Scheduler)**
```
1. Scheduler controlla ogni minuto
2. Se passati 5 minuti dall'ultima raccolta:
   ├── Controlla se c'è già un task "data_collection" attivo
   ├── Se NO: Crea nuovo task "scheduled_data_collection"
   └── Se SÌ: Salta questo ciclo
3. Task viene gestito dal Task Manager
4. Progresso tracciabile via API
```

### **Raccolta Manuale (API)**
```
1. Utente chiama POST /api/v1/data-collector/start
2. API controlla se c'è già un task attivo
3. Se NO: Crea nuovo task "data_collection"
4. Se SÌ: Ritorna errore o aspetta
5. Task viene gestito dal Task Manager
6. Stesso sistema di tracking
```

---

## 🎯 **Tipi di Task Distinti**

### **`scheduled_data_collection`**
- **Origine**: Data Scheduler automatico
- **Simboli**: Tutti i simboli configurati
- **Timeframes**: Tutti i timeframes configurati
- **Frequenza**: Ogni 5 minuti
- **Priorità**: Bassa (background)

### **`data_collection`**
- **Origine**: API manuale
- **Simboli**: Specificati dall'utente
- **Timeframes**: Specificati dall'utente
- **Frequenza**: On-demand
- **Priorità**: Alta (utente richiede)

### **`symbol_refresh`**
- **Origine**: API manuale
- **Azione**: Refresh cache simboli
- **Frequenza**: On-demand
- **Priorità**: Media

---

## 🛡️ **Prevenzione Sovrapposizioni**

### **Controllo Task Attivi**
```python
# Il scheduler controlla prima di creare nuovi task
active_tasks = task_manager.get_active_tasks()
data_collection_running = any(
    task.task_type in ["data_collection", "scheduled_data_collection"] 
    for task in active_tasks.values()
)

if not data_collection_running:
    # Crea nuovo task
else:
    # Salta questo ciclo
```

### **Vantaggi:**
- ✅ Nessuna sovrapposizione di raccolte
- ✅ Evita sovraccarico dell'API Binance
- ✅ Prevenzione race conditions
- ✅ Ottimizzazione risorse

---

## 📊 **API Unificate**

### **Status Completo**
```bash
GET /api/v1/data-collector/status
```

**Risposta:**
```json
{
  "is_running": true,
  "symbols_count": 50,
  "active_tasks": 1,
  "collection_interval": 300,
  "symbols": ["BTCUSDT", "ETHUSDT", ...],
  "scheduler_status": {
    "is_running": true,
    "collection_interval": 300,
    "symbol_refresh_interval": 3600,
    "data_collection_running": true,
    "active_tasks_count": 1,
    "scheduler_task_types": ["scheduled_data_collection"]
  }
}
```

### **Task Management**
```bash
# Lista tutti i task (automatici + manuali)
GET /api/v1/data-collector/tasks

# Solo task attivi
GET /api/v1/data-collector/tasks/active

# Statistiche complete
GET /api/v1/data-collector/tasks/stats
```

---

## ⚙️ **Configurazione**

### **Scheduler Settings**
```python
# app/services/data_scheduler.py
collection_interval = 300  # 5 minuti
symbol_refresh_interval = 3600  # 1 ora
check_interval = 60  # Controlla ogni minuto
```

### **Task Manager Settings**
```python
# app/services/task_manager.py
max_concurrent_tasks = 5
task_cleanup_delay = 300  # 5 minuti
```

---

## 🔍 **Monitoring e Debug**

### **Logs Strutturati**
```
2024-01-15 10:30:00 [INFO] Starting scheduled data collection
2024-01-15 10:30:01 [INFO] Data collection already running, skipping scheduled collection
2024-01-15 10:30:02 [INFO] Scheduled data collection task submitted: uuid-123
```

### **Metriche Disponibili**
- Task attivi per tipo
- Tempo di esecuzione task
- Frequenza raccolte
- Errori per task
- Utilizzo API Binance

---

## 🚀 **Vantaggi della Nuova Architettura**

### **1. Coordinazione**
- ✅ Nessuna sovrapposizione tra automatico e manuale
- ✅ Controllo centralizzato via Task Manager
- ✅ Visibilità completa di tutte le operazioni

### **2. Flessibilità**
- ✅ Raccolta automatica in background
- ✅ Raccolta manuale on-demand
- ✅ Controllo granulare per operazioni manuali

### **3. Affidabilità**
- ✅ Prevenzione race conditions
- ✅ Gestione errori unificata
- ✅ Recovery automatico

### **4. Monitoring**
- ✅ Tracking progresso unificato
- ✅ API unificata per status
- ✅ Logs strutturati

### **5. Performance**
- ✅ Evita sovraccarico API
- ✅ Ottimizzazione risorse
- ✅ Controllo concorrenza

---

## 📝 **Esempi Pratici**

### **Scenario 1: Raccolta Automatica**
```
10:00 - Scheduler controlla: nessun task attivo
10:00 - Scheduler crea: scheduled_data_collection
10:00-10:05 - Task esegue raccolta
10:05 - Scheduler controlla: task ancora attivo
10:05 - Scheduler salta questo ciclo
10:06 - Task completa
10:06 - Scheduler controlla: nessun task attivo
10:06 - Scheduler può creare nuovo task
```

### **Scenario 2: Raccolta Manuale Durante Automatica**
```
10:02 - Scheduler ha task attivo
10:02 - Utente chiama API manuale
10:02 - API controlla: task attivo
10:02 - API ritorna: "Data collection already running"
10:02 - Utente può monitorare via /tasks/active
```

### **Scenario 3: Raccolta Manuale Completa**
```
10:10 - Nessun task attivo
10:10 - Utente chiama API con simboli specifici
10:10 - API crea: data_collection con simboli custom
10:10-10:12 - Task esegue raccolta custom
10:12 - Task completa
10:12 - Scheduler può riprendere normale funzionamento
```

---

## 🎯 **Conclusione**

La nuova architettura risolve completamente il problema di sovrapposizione:

1. **Sistema Unificato**: Tutto passa attraverso il Task Manager
2. **Coordinazione**: Scheduler e API si coordinano automaticamente
3. **Flessibilità**: Mantiene entrambi i modi di raccolta
4. **Affidabilità**: Prevenzione conflitti e sovrapposizioni
5. **Monitoring**: Visibilità completa di tutte le operazioni

Ora il sistema è molto più robusto e prevedibile! 🎉

