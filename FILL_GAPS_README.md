# 🔄 Script per Riempire Gap nei Dati

## 📋 Descrizione

Questi script permettono di riempire tutti i gap (buchi) nei dati di mercato tra il primo e l'ultimo record presente nel database.

## 📦 Script Disponibili

### 1️⃣ `fill_data_gaps.py` - Completo
**Riempie TUTTI i gap per tutti i simboli e timeframe.**

```bash
python fill_data_gaps.py
```

⚠️ **Attenzione**: 
- Può richiedere **molto tempo** (migliaia di candele)
- Usa **molte chiamate API** a Binance
- Consigliato **solo se necessario**

### 2️⃣ `fill_data_gaps_selective.py` - Selettivo ⭐ (Consigliato)
**Permette di scegliere quali simboli riempire.**

```bash
python fill_data_gaps_selective.py
```

**Menu Opzioni:**
1. **Simboli principali** (BTC, ETH, BNB, XRP, ADA)
2. **Top 10 simboli** (I 10 più importanti)
3. **Tutti i simboli** (Tutti nel database)
4. **Custom** (Inserisci manualmente)

**Oppure usa direttamente:**
```bash
# Opzione 1 (simboli principali)
echo "1" | python fill_data_gaps_selective.py

# Opzione 2 (top 10)
echo "2" | python fill_data_gaps_selective.py
```

## ⚙️ Prerequisiti

### 1. **Database Lock**
Se il server è in esecuzione, potrebbe bloccare il database (SQLite limitation).

**Soluzioni:**
- ✅ Gli script hanno **retry logic** automatico
- ✅ Aspettano fino a 5 secondi per ottenere il lock
- ⚠️ Se ancora problemi, ferma il server temporaneamente

### 2. **Virtual Environment**
```bash
cd /path/to/altar-trader-hub-be
source venv/bin/activate
```

### 3. **Connessione Internet**
Gli script scaricano dati da Binance, serve connessione stabile.

## 🚀 Esempi d'Uso

### Esempio 1: Riempi solo BTC ed ETH
```bash
cd altar-trader-hub-be
source venv/bin/activate
python fill_data_gaps_selective.py

# Seleziona: 4 (Custom)
# Inserisci: BTCUSDT,ETHUSDT
```

### Esempio 2: Riempi simboli principali (automatico)
```bash
cd altar-trader-hub-be
source venv/bin/activate
echo "1" | python fill_data_gaps_selective.py
```

### Esempio 3: Riempi tutto (lungo!)
```bash
cd altar-trader-hub-be
source venv/bin/activate
python fill_data_gaps.py
```

## 📊 Output Esempio

```
================================================================================
🔄 RIEMPIMENTO GAP SELETTIVO
================================================================================

📊 Simboli: BTCUSDT, ETHUSDT, BNBUSDT
⏰ Timeframes: 1m, 5m, 15m, 1h

================================================================================
📈 BTCUSDT
================================================================================
   1m    - 6 gap, ~33293 candele mancanti
      Gap 1/6: 2025-09-19 01:01 → 2025-09-19 09:22 ✅ 502 candele
      Gap 2/6: 2025-09-19 09:24 → 2025-09-29 17:20 ✅ 14639 candele
      ...
   5m    - 4 gap, ~6251 candele mancanti
      Gap 1/4: 2025-09-19 01:05 → 2025-09-19 09:20 ✅ 100 candele
      ...

================================================================================
✅ COMPLETATO: 45892 candele totali inserite
================================================================================
```

## 🔧 Caratteristiche

### ✅ Retry Logic
- Riprova automaticamente se il database è locked
- Fino a 5 tentativi con pause di 1 secondo

### ✅ Rate Limiting
- Rispetta i limiti API di Binance
- Pause di 0.3s tra le richieste

### ✅ Gestione Errori
- Rollback automatico in caso di errore
- Log dettagliati degli errori

### ✅ Progress Tracking
- Mostra avanzamento in tempo reale
- Conta delle candele inserite

## ⚠️ Limitazioni

### SQLite Concurrency
SQLite non supporta bene scritture concorrenti. Se hai problemi persistenti:

```bash
# Ferma il server
pkill -f uvicorn

# Esegui lo script
python fill_data_gaps_selective.py

# Riavvia il server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Rate Limits Binance
- **1200 richieste/minuto** (weight)
- **10 richieste/secondo** (raw)

Gli script rispettano questi limiti con pause automatiche.

## 📝 Note

- **Timeframe supportati**: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w
- **Max candele per richiesta**: 1000 (limite Binance)
- **Fonte dati**: Binance Mainnet (dati reali)

## 🐛 Troubleshooting

### Problema: "Database is locked"
**Soluzione**: Gli script hanno retry automatico. Se persiste, ferma il server.

### Problema: "No data received"
**Soluzione**: Alcuni simboli potrebbero non avere dati per quel periodo su Binance.

### Problema: Script troppo lento
**Soluzione**: Usa `fill_data_gaps_selective.py` con meno simboli.

## 📞 Supporto

Per problemi o domande, verifica i log:
```bash
tail -f /tmp/fill_gaps.log
```

