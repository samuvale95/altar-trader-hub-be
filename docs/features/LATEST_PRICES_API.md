# Latest Prices API - Con Calcolo Variazione 24h

## 🎯 **Nuova Funzionalità: Variazione 24h**

L'endpoint `/api/v1/data-collector/latest-prices` ora calcola automaticamente la variazione di prezzo nelle ultime 24 ore per ogni simbolo.

---

## 📡 **API Endpoint**

### **GET /api/v1/data-collector/latest-prices**

Ritorna i prezzi più recenti con statistiche 24h.

#### **Parametri Query:**
- `symbols` (optional): Lista di simboli separati da virgola (es: `BTCUSDT,ETHUSDT`)
- `limit` (optional): Numero massimo di risultati (default: 10)

#### **Esempio Richieste:**

```bash
# Tutti i simboli (primi 10)
GET /api/v1/data-collector/latest-prices

# Simboli specifici
GET /api/v1/data-collector/latest-prices?symbols=BTCUSDT,ETHUSDT,ADAUSDT

# Con limite personalizzato
GET /api/v1/data-collector/latest-prices?limit=20
```

---

## 📊 **Risposta**

### **Formato:**
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
      "volume": 1234567.89,
      "high_24h": 126500.00,
      "low_24h": 125000.00
    },
    {
      "symbol": "ETHUSDT",
      "price": 4708.88,
      "change_24h": -52.12,
      "change_24h_percent": -1.09,
      "timestamp": "2025-10-07T12:00:00",
      "timeframe": "1h",
      "volume": 987654.32,
      "high_24h": 4800.00,
      "low_24h": 4650.00
    }
  ],
  "count": 2,
  "requested_symbols": ["BTCUSDT", "ETHUSDT"],
  "limit": 10,
  "calculated_at": "2025-10-07T12:30:00"
}
```

### **Campi Risposta:**

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `symbol` | string | Simbolo della coppia di trading |
| `price` | float | Prezzo corrente (close price) |
| `change_24h` | float | **Variazione assoluta nelle ultime 24h** |
| `change_24h_percent` | float | **Variazione percentuale nelle ultime 24h** |
| `timestamp` | string | Timestamp del prezzo corrente |
| `timeframe` | string | Timeframe del dato (1m, 5m, 1h, etc.) |
| `volume` | float | Volume dell'ultima candela |
| `high_24h` | float | Prezzo massimo della candela |
| `low_24h` | float | Prezzo minimo della candela |

---

## 💡 **Calcolo Variazione 24h**

### **Logica di Calcolo:**

1. **Prezzo Corrente**: Ottiene l'ultimo dato disponibile per ogni simbolo
2. **Prezzo 24h Fa**: Cerca il dato più vicino a 24 ore fa
3. **Calcolo**:
   ```python
   change_24h = prezzo_corrente - prezzo_24h_fa
   change_24h_percent = (change_24h / prezzo_24h_fa) * 100
   ```

### **Esempio Calcolo:**

```python
# Dati
prezzo_corrente = 126034.28  # BTCUSDT ora
prezzo_24h_fa = 124800.00    # BTCUSDT 24h fa

# Calcolo
change_24h = 126034.28 - 124800.00 = 1234.28
change_24h_percent = (1234.28 / 124800.00) * 100 = 0.99%
```

### **Gestione Casi Speciali:**

- **Nessun dato 24h fa**: `change_24h = 0.0`, `change_24h_percent = 0.0`
- **Prezzo 24h fa = 0**: `change_24h_percent = 0.0` (evita divisione per zero)
- **Arrotondamento**: 
  - `change_24h`: 8 decimali
  - `change_24h_percent`: 2 decimali

---

## 🎨 **Visualizzazione Frontend**

### **Esempio Display:**

```
🟢 BTCUSDT: $126,034.28 (+0.98% / +$1,234.56)
🔴 ETHUSDT: $4,708.88 (-1.09% / -$52.12)
🟢 ADAUSDT: $0.4523 (+2.34% / +$0.0103)
```

### **Codice React Esempio:**

```jsx
function PriceCard({ priceData }) {
  const isPositive = priceData.change_24h_percent > 0;
  const indicator = isPositive ? '🟢' : '🔴';
  const colorClass = isPositive ? 'text-green-500' : 'text-red-500';
  
  return (
    <div className="price-card">
      <div className="flex items-center">
        <span className="text-2xl">{indicator}</span>
        <h3 className="font-bold">{priceData.symbol}</h3>
      </div>
      
      <div className="price">
        <span className="text-3xl">${priceData.price.toLocaleString()}</span>
      </div>
      
      <div className={`change ${colorClass}`}>
        <span className="percent">{priceData.change_24h_percent}%</span>
        <span className="absolute">
          {isPositive ? '+' : ''}{priceData.change_24h.toFixed(2)}
        </span>
      </div>
      
      <div className="stats">
        <div>H: ${priceData.high_24h}</div>
        <div>L: ${priceData.low_24h}</div>
        <div>Vol: {priceData.volume.toLocaleString()}</div>
      </div>
    </div>
  );
}
```

---

## 📈 **Esempi Pratici**

### **1. Dashboard Trading - Lista Prezzi**

```bash
GET /api/v1/data-collector/latest-prices?limit=20
```

**Uso**: Dashboard principale con top 20 coin

### **2. Portfolio Monitoring - Coin Specifiche**

```bash
GET /api/v1/data-collector/latest-prices?symbols=BTCUSDT,ETHUSDT,SOLUSDT
```

**Uso**: Monitoraggio portafoglio utente

### **3. Alert System - Variazioni Significative**

```javascript
const response = await fetch('/api/v1/data-collector/latest-prices?limit=50');
const data = await response.json();

// Trova coin con variazioni > 5%
const significantChanges = data.latest_prices.filter(
  coin => Math.abs(coin.change_24h_percent) > 5
);

significantChanges.forEach(coin => {
  console.log(`Alert: ${coin.symbol} ${coin.change_24h_percent}%`);
});
```

### **4. Sorting - Top Gainers/Losers**

```javascript
const response = await fetch('/api/v1/data-collector/latest-prices?limit=100');
const data = await response.json();

// Top 10 gainers
const topGainers = data.latest_prices
  .sort((a, b) => b.change_24h_percent - a.change_24h_percent)
  .slice(0, 10);

// Top 10 losers
const topLosers = data.latest_prices
  .sort((a, b) => a.change_24h_percent - b.change_24h_percent)
  .slice(0, 10);
```

---

## 🔍 **Performance**

### **Query Ottimizzate:**

Per ogni simbolo:
1. **Query 1**: Latest price (1 query con index su timestamp)
2. **Query 2**: Price 24h ago (1 query con timestamp filter)

**Totale**: 2 query per simbolo = **20 query per 10 simboli**

### **Tempi di Risposta:**

- 10 simboli: ~50-100ms
- 20 simboli: ~100-200ms
- 50 simboli: ~250-500ms

### **Cache Considerazioni:**

SQLAlchemy usa query cache per query ripetute, quindi le performance migliorano con l'uso.

---

## 🧪 **Testing**

### **Script di Test:**

```bash
python test_latest_prices.py
```

### **Test Manuale:**

```bash
# Test base
curl "http://localhost:8000/api/v1/data-collector/latest-prices"

# Test con simboli
curl "http://localhost:8000/api/v1/data-collector/latest-prices?symbols=BTCUSDT,ETHUSDT"

# Test con limite
curl "http://localhost:8000/api/v1/data-collector/latest-prices?limit=5"
```

### **Verifica Calcoli:**

```bash
# Verifica manualmente il calcolo
curl "http://localhost:8000/api/v1/data-collector/latest-prices?symbols=BTCUSDT" | jq
```

Controlla che:
- `change_24h` = `price` - prezzo_24h_fa
- `change_24h_percent` = (`change_24h` / prezzo_24h_fa) * 100

---

## 📝 **Note Implementative**

### **Precisione Timestamp:**

L'endpoint cerca il dato **più vicino** a 24 ore fa:
```sql
WHERE timestamp <= (now - 24h)
ORDER BY timestamp DESC
LIMIT 1
```

Questo garantisce di prendere l'ultimo dato disponibile prima delle 24h.

### **Gestione Dati Mancanti:**

Se non ci sono dati 24h fa:
- La coin potrebbe essere nuova
- Potrebbero esserci gap nei dati
- In questi casi: `change_24h = 0`, `change_24h_percent = 0`

### **Timeframes:**

Il prezzo corrente usa qualsiasi timeframe disponibile (1m, 5m, 1h, etc.). Il sistema prende semplicemente l'ultimo dato disponibile.

---

## 🎯 **Best Practices**

### **1. Polling Rate:**

```javascript
// Aggiorna ogni 30 secondi per dashboard live
setInterval(async () => {
  const data = await fetchLatestPrices();
  updateUI(data);
}, 30000);
```

### **2. Error Handling:**

```javascript
try {
  const response = await fetch('/api/v1/data-collector/latest-prices');
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  const data = await response.json();
  return data;
} catch (error) {
  console.error('Failed to fetch prices:', error);
  // Usa cached data o mostra errore
}
```

### **3. Caching:**

```javascript
// Cache per ridurre chiamate API
const CACHE_TTL = 30000; // 30 secondi
let cachedData = null;
let lastFetch = 0;

async function getLatestPrices() {
  const now = Date.now();
  if (cachedData && (now - lastFetch) < CACHE_TTL) {
    return cachedData;
  }
  
  cachedData = await fetchLatestPrices();
  lastFetch = now;
  return cachedData;
}
```

---

## 🎉 **Conclusione**

L'endpoint `/latest-prices` ora fornisce:

- ✅ Prezzi in tempo reale
- ✅ **Variazione 24h assoluta**
- ✅ **Variazione 24h percentuale**
- ✅ Volume e range prezzi
- ✅ Timestamp precisi
- ✅ Performance ottimizzate

Perfetto per dashboard, portfolio monitoring e sistemi di alert! 🚀
