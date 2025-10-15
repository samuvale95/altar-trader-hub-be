# Market Data API - Guida Completa agli Endpoint

## 📋 **Indice**
1. [Simboli](#simboli)
2. [Dati OHLCV (Candlestick)](#ohlcv)
3. [Ticker (Prezzi Real-time)](#ticker)
4. [Indicatori Tecnici](#indicatori)
5. [News](#news)
6. [Summary](#summary)
7. [Statistiche](#statistiche)
8. [Data Collector](#data-collector)
9. [Charts API](#charts)
10. [WebSocket Real-time](#websocket)

---

## 1️⃣ **Simboli** {#simboli}

### **GET /api/v1/market-data/symbols**
Ottiene lista di tutti i simboli disponibili nel database.

**Parametri Query:**
- `exchange` (optional): Filtra per exchange (binance, kraken, kucoin)

**Esempio:**
```bash
GET /api/v1/market-data/symbols
GET /api/v1/market-data/symbols?exchange=binance
```

**Risposta:**
```json
[
  "BTCUSDT",
  "ETHUSDT",
  "ADAUSDT",
  "SOLUSDT",
  ...
]
```

---

## 2️⃣ **Dati OHLCV (Candlestick)** {#ohlcv}

### **GET /api/v1/market-data/ohlcv**
Ottiene dati OHLCV (Open, High, Low, Close, Volume) per un simbolo specifico.

**Parametri Query:**
- `symbol` (required): Simbolo (es: BTCUSDT)
- `timeframe` (required): Intervallo temporale
- `start_date` (optional): Data inizio (ISO format)
- `end_date` (optional): Data fine (ISO format)
- `limit` (optional): Numero massimo risultati (default: 1000, max: 1000)

**Timeframes validi:**
`1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1w`

**Esempio:**
```bash
# Ultimi 100 candlestick 1h per BTCUSDT
GET /api/v1/market-data/ohlcv?symbol=BTCUSDT&timeframe=1h&limit=100

# Dati specifici per range di date
GET /api/v1/market-data/ohlcv?symbol=ETHUSDT&timeframe=1d&start_date=2025-10-01&end_date=2025-10-07

# Ultimi 500 dati 5 minuti
GET /api/v1/market-data/ohlcv?symbol=SOLUSDT&timeframe=5m&limit=500
```

**Risposta:**
```json
[
  {
    "id": 12345,
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "open_price": "126000.50",
    "high_price": "126500.00",
    "low_price": "125800.00",
    "close_price": "126034.28",
    "volume": "1234.567",
    "quote_volume": "155123456.78",
    "trades_count": 15234,
    "taker_buy_volume": "678.90",
    "taker_buy_quote_volume": "85432123.45",
    "timestamp": "2025-10-07T12:00:00",
    "created_at": "2025-10-07T12:01:00"
  },
  ...
]
```

---

## 3️⃣ **Ticker (Prezzi Real-time)** {#ticker}

### **GET /api/v1/market-data/ticker**
Ottiene dati ticker (prezzi real-time) per uno o più simboli.

**Parametri Query:**
- `symbols` (optional): Lista simboli separati da virgola
- `exchange` (optional): Exchange specifico

**Esempio:**
```bash
# Ticker per tutti i simboli
GET /api/v1/market-data/ticker

# Ticker per simboli specifici
GET /api/v1/market-data/ticker?symbols=BTCUSDT,ETHUSDT,SOLUSDT
```

**Risposta:**
```json
[
  {
    "symbol": "BTCUSDT",
    "price": "126034.28",
    "price_change": "1234.56",
    "price_change_percentage": "0.98",
    "volume": "12345.67",
    "quote_volume": "155123456.78",
    "high_24h": "126500.00",
    "low_24h": "125000.00",
    "open_24h": "124800.00",
    "close_24h": "126034.28",
    "timestamp": "2025-10-07T12:00:00"
  },
  ...
]
```

**Nota:** Attualmente `price_change` è a 0 (TODO). Usa invece `/data-collector/latest-prices` per variazioni 24h accurate.

---

## 4️⃣ **Indicatori Tecnici** {#indicatori}

### **GET /api/v1/market-data/indicators**
Ottiene indicatori tecnici per un simbolo.

**Parametri Query:**
- `symbol` (required): Simbolo
- `timeframe` (required): Intervallo temporale
- `indicator_name` (required): Nome indicatore
- `start_date` (optional): Data inizio
- `end_date` (optional): Data fine
- `limit` (optional): Numero massimo risultati (default: 1000)

**Indicatori disponibili:**
- **Trend**: `RSI`, `MACD`, `ADX`, `AROON`, `DX`
- **Media Mobile**: `SMA`, `EMA`, `WMA`, `VWMA`, `T3`
- **Momentum**: `MOM`, `ROC`, `ROCP`, `ROCR`, `CMO`
- **Volume**: `OBV`, `AD`, `ADOSC`, `MFI`
- **Volatilità**: `BB` (Bollinger Bands), `ATR`, `NATR`
- **Oscillatori**: `STOCH`, `STOCHF`, `STOCHRSI`, `CCI`, `WILLR`
- **Candlestick Patterns**: `CDLDOJI`, `CDLHAMMER`, `CDLENGULFING`, etc.

**Esempio:**
```bash
# RSI per BTCUSDT su 1h
GET /api/v1/market-data/indicators?symbol=BTCUSDT&timeframe=1h&indicator_name=RSI&limit=100

# MACD per ETHUSDT su 4h
GET /api/v1/market-data/indicators?symbol=ETHUSDT&timeframe=4h&indicator_name=MACD

# Bollinger Bands per SOLUSDT su 1d
GET /api/v1/market-data/indicators?symbol=SOLUSDT&timeframe=1d&indicator_name=BB
```

**Risposta:**
```json
[
  {
    "id": 123,
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "indicator_name": "RSI",
    "value": "65.34",
    "values": null,
    "signal": "hold",
    "signal_strength": "0.3068",
    "overbought_level": "70",
    "oversold_level": "30",
    "timestamp": "2025-10-07T12:00:00",
    "created_at": "2025-10-07T12:01:00",
    "metadata": null
  },
  ...
]
```

**Segnali:**
- `buy`: Segnale di acquisto
- `sell`: Segnale di vendita
- `hold`: Mantieni posizione

---

## 5️⃣ **News** {#news}

### **GET /api/v1/market-data/news**
Ottiene notizie di mercato con sentiment analysis.

**Parametri Query:**
- `symbol` (optional): Filtra per simbolo
- `source` (optional): Filtra per fonte (Reuters, Bloomberg, etc.)
- `sentiment_label` (optional): Filtra per sentiment (positive, negative, neutral)
- `impact_label` (optional): Filtra per impatto (high, medium, low)
- `start_date` (optional): Data inizio
- `end_date` (optional): Data fine
- `limit` (optional): Numero risultati (default: 100)
- `offset` (optional): Offset per paginazione (default: 0)

**Esempio:**
```bash
# Tutte le news recenti
GET /api/v1/market-data/news?limit=20

# News positive per BTC
GET /api/v1/market-data/news?symbol=BTCUSDT&sentiment_label=positive

# News alto impatto
GET /api/v1/market-data/news?impact_label=high&limit=10
```

**Risposta:**
```json
[
  {
    "id": 456,
    "symbol": "BTCUSDT",
    "title": "Bitcoin reaches new all-time high",
    "content": "Full article content...",
    "summary": "Bitcoin has surpassed...",
    "url": "https://...",
    "source": "Reuters",
    "sentiment_score": "0.8500",
    "sentiment_label": "positive",
    "confidence": "0.9200",
    "impact_score": "0.7500",
    "impact_label": "high",
    "published_at": "2025-10-07T10:00:00",
    "created_at": "2025-10-07T10:05:00",
    "metadata": {}
  },
  ...
]
```

---

## 6️⃣ **Summary** {#summary}

### **GET /api/v1/market-data/summary/{symbol}**
Ottiene un riepilogo completo per un simbolo.

**Parametri Path:**
- `symbol` (required): Simbolo (es: BTCUSDT)

**Esempio:**
```bash
GET /api/v1/market-data/summary/BTCUSDT
GET /api/v1/market-data/summary/ETHUSDT
```

**Risposta:**
```json
{
  "symbol": "BTCUSDT",
  "current_price": "126034.28",
  "price_change_24h": "1234.56",
  "price_change_percentage_24h": "0.98",
  "volume_24h": "12345.67",
  "market_cap": null,
  "high_24h": "126500.00",
  "low_24h": "125000.00",
  "open_24h": "124800.00",
  "close_24h": "126034.28",
  "last_updated": "2025-10-07T12:00:00"
}
```

**Nota:** Attualmente `price_change_24h` è a 0 (TODO). Usa `/data-collector/latest-prices` per dati accurati.

---

## 7️⃣ **Statistiche** {#statistiche}

### **GET /api/v1/market-data/stats**
Ottiene statistiche generali sui dati di mercato.

**Esempio:**
```bash
GET /api/v1/market-data/stats
```

**Risposta:**
```json
{
  "total_symbols": 250,
  "total_candles": 62616,
  "last_update": "2025-10-07T12:00:00",
  "exchanges": ["binance", "kraken", "kucoin"],
  "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"]
}
```

---

## 8️⃣ **Data Collector** {#data-collector}

### **GET /api/v1/data-collector/latest-prices** ⭐
**ENDPOINT RACCOMANDATO** per prezzi in tempo reale con variazioni 24h.

**Parametri Query:**
- `symbols` (optional): Lista simboli separati da virgola
- `limit` (optional): Numero risultati (default: 10)

**Esempio:**
```bash
# Primi 10 simboli con variazione 24h
GET /api/v1/data-collector/latest-prices

# Simboli specifici
GET /api/v1/data-collector/latest-prices?symbols=BTCUSDT,ETHUSDT,SOLUSDT

# Primi 20 simboli
GET /api/v1/data-collector/latest-prices?limit=20
```

**Risposta:**
```json
{
  "latest_prices": [
    {
      "symbol": "BTCUSDT",
      "price": 126034.28,
      "change_24h": 1234.56,
      "change_24h_percent": 0.98,
      "timestamp": "2025-10-07T12:00:00",
      "timeframe": "1h",
      "volume": 12345.67,
      "high_24h": 126500.00,
      "low_24h": 125000.00
    },
    ...
  ],
  "count": 10,
  "requested_symbols": "all",
  "limit": 10,
  "calculated_at": "2025-10-07T12:30:00"
}
```

**Caratteristiche:**
- ✅ Variazione 24h calcolata accuratamente
- ✅ Prezzi sempre aggiornati
- ✅ Volume e range prezzi
- ✅ Performance ottimizzate

---

### **GET /api/v1/data-collector/status**
Ottiene lo stato del data collector e scheduler.

**Esempio:**
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
    "symbols_count": 50,
    "symbols": ["BTCUSDT", "ETHUSDT", ...],
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

---

### **GET /api/v1/data-collector/config**
Ottiene la configurazione del scheduler.

**Esempio:**
```bash
GET /api/v1/data-collector/config
```

**Risposta:**
```json
{
  "collection_interval": 300,
  "symbol_refresh_interval": 3600,
  "is_running": true,
  "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT", ...],
  "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
  "available_symbols": ["BTCUSDT", "ETHUSDT", ...]
}
```

---

### **PUT /api/v1/data-collector/config**
Aggiorna la configurazione del scheduler.

**Body (tutti i campi opzionali):**
```json
{
  "collection_interval": 600,
  "symbol_refresh_interval": 1800,
  "symbols": ["BTCUSDT", "ETHUSDT"],
  "timeframes": ["1m", "5m", "1h"],
  "enabled": true
}
```

**Esempio:**
```bash
# Cambia frequenza raccolta a 10 minuti
PUT /api/v1/data-collector/config
{
  "collection_interval": 600
}

# Cambia simboli tracciati
PUT /api/v1/data-collector/config
{
  "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
}
```

---

### **POST /api/v1/data-collector/start**
Avvia il data scheduler.

**Esempio:**
```bash
POST /api/v1/data-collector/start
```

**Risposta:**
```json
{
  "message": "Data collection scheduler started successfully"
}
```

---

### **POST /api/v1/data-collector/stop**
Ferma il data scheduler.

**Esempio:**
```bash
POST /api/v1/data-collector/stop
```

**Risposta:**
```json
{
  "message": "Data collection scheduler stopped successfully"
}
```

---

### **POST /api/v1/data-collector/refresh-symbols**
Aggiorna la cache dei simboli da Binance.

**Esempio:**
```bash
POST /api/v1/data-collector/refresh-symbols
```

**Risposta:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "submitted",
  "message": "Symbol refresh task submitted successfully"
}
```

---

### **GET /api/v1/data-collector/task/{task_id}**
Monitora lo stato di un task specifico.

**Esempio:**
```bash
GET /api/v1/data-collector/task/550e8400-e29b-41d4-a716-446655440000
```

**Risposta:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_type": "symbol_refresh",
  "status": "completed",
  "progress": 100,
  "message": "Symbols refreshed: 50 symbols loaded",
  "created_at": "2025-10-07T12:00:00",
  "started_at": "2025-10-07T12:00:01",
  "completed_at": "2025-10-07T12:00:05",
  "error": null,
  "result": {
    "success": true,
    "symbols_count": 50,
    "old_count": 48,
    "symbols": ["BTCUSDT", ...],
    "cache_refreshed": true
  }
}
```

---

### **GET /api/v1/data-collector/tasks**
Lista di tutti i task.

**Parametri Query:**
- `task_type` (optional): Filtra per tipo di task

**Esempio:**
```bash
# Tutti i task
GET /api/v1/data-collector/tasks

# Solo task di data collection
GET /api/v1/data-collector/tasks?task_type=data_collection
```

---

### **GET /api/v1/data-collector/tasks/active**
Lista solo i task attivi.

**Esempio:**
```bash
GET /api/v1/data-collector/tasks/active
```

---

### **GET /api/v1/data-collector/tasks/stats**
Statistiche complete dei task.

**Esempio:**
```bash
GET /api/v1/data-collector/tasks/stats
```

**Risposta:**
```json
{
  "task_counts": {
    "pending": 0,
    "running": 1,
    "completed": 25,
    "failed": 0,
    "cancelled": 0
  },
  "active_tasks_count": 1,
  "data_collector_status": {
    "symbols_count": 50,
    "timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
    "available_symbols": ["BTCUSDT", "ETHUSDT", ...]
  }
}
```

---

## 9️⃣ **Charts API** {#charts}

Vedi documentazione dettagliata in `CHARTS_API_DOCUMENTATION.md`.

**Endpoint principali:**
- `GET /api/v1/charts/candlestick/{symbol}`
- `GET /api/v1/charts/line/{symbol}`
- `GET /api/v1/charts/area/{symbol}`
- `GET /api/v1/charts/volume/{symbol}`
- `GET /api/v1/charts/indicators/{symbol}`
- `GET /api/v1/charts/available-symbols`
- `GET /api/v1/charts/available-timeframes/{symbol}`

---

## 🔟 **WebSocket Real-time** {#websocket}

### **WS /ws/market-data**
Connessione WebSocket per aggiornamenti real-time.

**Parametri Query:**
- `symbols` (optional): Lista simboli separati da virgola

**Esempio JavaScript:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/market-data?symbols=BTCUSDT,ETHUSDT');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Market update:', data);
};
```

**Messaggi Ricevuti:**
```json
{
  "type": "market_data",
  "symbol": "BTCUSDT",
  "price": 126034.28,
  "volume": 1234.56,
  "change": 500.0,
  "change_percent": 1.12,
  "timeframe": "1m",
  "timestamp": "2025-10-07T12:30:00"
}
```

---

## 📊 **Comparazione Endpoint per Caso d'Uso**

### **Voglio prezzi real-time con variazione 24h:**
✅ **MIGLIORE**: `GET /api/v1/data-collector/latest-prices`
```bash
GET /api/v1/data-collector/latest-prices?symbols=BTCUSDT,ETHUSDT
```

### **Voglio dati OHLCV per grafici:**
✅ **MIGLIORE**: `GET /api/v1/market-data/ohlcv`
```bash
GET /api/v1/market-data/ohlcv?symbol=BTCUSDT&timeframe=1h&limit=100
```

### **Voglio dati per candlestick chart:**
✅ **MIGLIORE**: `GET /api/v1/charts/candlestick/{symbol}`
```bash
GET /api/v1/charts/candlestick/BTCUSDT?timeframe=1h&limit=100
```

### **Voglio indicatori tecnici:**
✅ **MIGLIORE**: `GET /api/v1/market-data/indicators`
```bash
GET /api/v1/market-data/indicators?symbol=BTCUSDT&timeframe=1h&indicator_name=RSI
```

### **Voglio lista simboli disponibili:**
✅ **MIGLIORE**: `GET /api/v1/market-data/symbols`
```bash
GET /api/v1/market-data/symbols
```

### **Voglio aggiornamenti in tempo reale:**
✅ **MIGLIORE**: WebSocket `WS /ws/market-data`
```javascript
ws://localhost:8000/ws/market-data?symbols=BTCUSDT
```

---

## 🔐 **Autenticazione**

Tutti gli endpoint richiedono autenticazione tramite Bearer Token:

```bash
Authorization: Bearer <your_jwt_token>
```

**Esempio:**
```bash
curl 'http://localhost:8000/api/v1/data-collector/latest-prices' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

---

## 🎯 **Esempi Pratici**

### **Dashboard Trading - Prezzi Live**
```javascript
// Fetch top 20 coins con variazioni
const response = await fetch('/api/v1/data-collector/latest-prices?limit=20', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const data = await response.json();

// Display
data.latest_prices.forEach(coin => {
  console.log(`${coin.symbol}: $${coin.price} (${coin.change_24h_percent}%)`);
});
```

### **Grafico Candlestick**
```javascript
// Fetch 100 candlestick 1h per BTCUSDT
const response = await fetch(
  '/api/v1/market-data/ohlcv?symbol=BTCUSDT&timeframe=1h&limit=100',
  { headers: { 'Authorization': `Bearer ${token}` }}
);
const candles = await response.json();

// Usa per grafico TradingView/Chart.js
```

### **Indicatori RSI**
```javascript
// Fetch RSI per ETHUSDT
const response = await fetch(
  '/api/v1/market-data/indicators?symbol=ETHUSDT&timeframe=1h&indicator_name=RSI&limit=50',
  { headers: { 'Authorization': `Bearer ${token}` }}
);
const rsiData = await response.json();

// Display segnale
const latest = rsiData[0];
console.log(`RSI: ${latest.value} - Signal: ${latest.signal}`);
```

### **Monitor Scheduler**
```javascript
// Polling status ogni 5 secondi
setInterval(async () => {
  const response = await fetch('/api/v1/data-collector/status', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const status = await response.json();
  
  console.log('Scheduler running:', status.scheduler.is_running);
  console.log('Active tasks:', status.scheduler.active_tasks_count);
}, 5000);
```

---

## 📝 **Note Importanti**

### **Limiti:**
- OHLCV: Max 1000 candele per richiesta
- Indicators: Max 1000 record per richiesta
- News: Max 100 news per richiesta
- Latest Prices: Raccomandato max 50 simboli

### **Performance:**
- Usa `limit` per ridurre dati trasferiti
- Cache disponibile su query ripetute
- WebSocket per aggiornamenti real-time (più efficiente del polling)

### **Timeframes:**
Tutti gli endpoint supportano: `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1w`

### **Formato Date:**
ISO 8601: `2025-10-07T12:00:00` o `2025-10-07`

---

## 🚀 **Quick Reference**

| Caso d'Uso | Endpoint | Metodo |
|------------|----------|--------|
| Prezzi live con variazioni | `/data-collector/latest-prices` | GET |
| Dati candlestick | `/market-data/ohlcv` | GET |
| Lista simboli | `/market-data/symbols` | GET |
| Indicatori tecnici | `/market-data/indicators` | GET |
| Summary simbolo | `/market-data/summary/{symbol}` | GET |
| Statistiche generali | `/market-data/stats` | GET |
| Real-time updates | `/ws/market-data` | WebSocket |
| Gestione scheduler | `/data-collector/config` | GET/PUT |
| Controllo scheduler | `/data-collector/start` | POST |

---

## 🎉 **Endpoint NON Esistenti**

Se cerchi endpoint che non esistono, ecco le alternative:

| Endpoint Cercato | Non Esiste | Usa Invece |
|------------------|------------|------------|
| `/market-data/realtime/{base}/{quote}` | ❌ | `/data-collector/latest-prices?symbols=BTCUSDT` |
| `/market-data/price/{symbol}` | ❌ | `/data-collector/latest-prices?symbols=BTCUSDT` |
| `/market-data/candles/{symbol}` | ❌ | `/market-data/ohlcv?symbol=BTCUSDT&timeframe=1h` |

---

## 📚 **Documentazione Correlata**

- `SCHEDULER_MANAGEMENT_API.md` - Gestione completa scheduler
- `CHARTS_API_DOCUMENTATION.md` - API grafici dettagliata
- `LATEST_PRICES_API.md` - Endpoint latest-prices dettagliato
- `NON_BLOCKING_DATA_COLLECTION.md` - Architettura sistema asincrono

---

Questa è la guida completa! Tutti gli endpoint sono pronti per essere utilizzati dal frontend. 🎯
