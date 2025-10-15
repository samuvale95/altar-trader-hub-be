# Paper Trading System - Guida Completa

## 🎯 **Overview**

Sistema di Paper Trading (trading virtuale) completamente funzionale che permette di:
- ✅ Creare portfolio virtuali con capitale iniziale
- ✅ Comprare e vendere qualsiasi crypto
- ✅ Tracciare posizioni e P&L in tempo reale
- ✅ Gestire stop loss e take profit
- ✅ Visualizzare storico trades
- ✅ **Switch facile a trading reale** quando pronto

---

## 🏗️ **Architettura**

### **Design Pattern: Strategy + Factory**

```
┌─────────────────────────────────────┐
│   BaseTradingService (Interface)    │
│   - buy()                            │
│   - sell()                           │
│   - get_positions()                  │
│   - etc...                           │
└─────────────────────────────────────┘
           ▲                  ▲
           │                  │
    ┌──────┴─────┐     ┌─────┴──────┐
    │   Paper    │     │    Live    │
    │  Trading   │     │  Trading   │
    │  Service   │     │  Service   │
    └────────────┘     └────────────┘
           ▲                  ▲
           │                  │
    ┌──────┴──────────────────┴──────┐
    │     TradingFactory              │
    │  get_trading_service(mode)      │
    └─────────────────────────────────┘
```

### **Componenti:**

1. **BaseTradingService**: Interfaccia comune per tutti i tipi di trading
2. **PaperTradingService**: Implementazione per trading virtuale
3. **LiveTradingService**: Stub per trading reale (da completare)
4. **TradingFactory**: Factory per creare il servizio giusto

---

## 📊 **Modelli Database**

### **PaperPortfolio**
```python
- id: int
- user_id: int
- name: str
- mode: PAPER | LIVE
- initial_capital: Decimal
- cash_balance: Decimal
- invested_value: Decimal
- total_value: Decimal
- total_pnl: Decimal
- total_pnl_percentage: Decimal
- realized_pnl: Decimal
- unrealized_pnl: Decimal
- total_trades: int
- winning_trades: int
- losing_trades: int
- win_rate: Decimal
- max_drawdown: Decimal
```

### **PaperPosition**
```python
- id: int
- portfolio_id: int
- symbol: str
- quantity: Decimal
- avg_entry_price: Decimal
- current_price: Decimal
- market_value: Decimal
- total_cost: Decimal
- unrealized_pnl: Decimal
- unrealized_pnl_percentage: Decimal
- stop_loss_price: Decimal (optional)
- take_profit_price: Decimal (optional)
- is_active: bool
```

### **PaperTrade**
```python
- id: int
- portfolio_id: int
- position_id: int
- symbol: str
- side: BUY | SELL
- quantity: Decimal
- price: Decimal
- total_value: Decimal
- fee: Decimal
- total_cost: Decimal
- realized_pnl: Decimal
- realized_pnl_percentage: Decimal
- order_type: MARKET | LIMIT
- status: FILLED
- executed_at: datetime
```

### **PaperBalance**
```python
- id: int
- portfolio_id: int
- asset: str (BTC, ETH, USDT, etc.)
- free: Decimal
- locked: Decimal
- total: Decimal
- usd_value: Decimal
```

---

## 📡 **API Endpoints**

### **1. Crea Portfolio**
```bash
POST /api/v1/paper-trading/portfolio
```

**Body:**
```json
{
  "name": "My First Portfolio",
  "description": "Testing paper trading",
  "initial_capital": 10000.00
}
```

**Risposta:**
```json
{
  "id": 1,
  "name": "My First Portfolio",
  "mode": "paper",
  "initial_capital": 10000.00,
  "cash_balance": 10000.00,
  "total_value": 10000.00,
  "created_at": "2025-10-07T12:00:00"
}
```

---

### **2. Visualizza Portfolio**
```bash
GET /api/v1/paper-trading/portfolio/{portfolio_id}
```

**Risposta:**
```json
{
  "id": 1,
  "name": "My First Portfolio",
  "description": "Testing paper trading",
  "mode": "paper",
  "initial_capital": 10000.00,
  "cash_balance": 7500.00,
  "invested_value": 2600.00,
  "total_value": 10100.00,
  "total_pnl": 100.00,
  "total_pnl_percentage": 1.00,
  "realized_pnl": 50.00,
  "unrealized_pnl": 50.00,
  "total_trades": 5,
  "winning_trades": 3,
  "losing_trades": 2,
  "win_rate": 60.00,
  "max_drawdown": 2.50,
  "created_at": "2025-10-07T12:00:00",
  "updated_at": "2025-10-07T13:00:00"
}
```

---

### **3. Compra Crypto**
```bash
POST /api/v1/paper-trading/portfolio/{portfolio_id}/buy
```

**Body:**
```json
{
  "symbol": "BTCUSDT",
  "quantity": 0.01,
  "price": null,
  "order_type": "MARKET"
}
```

**Risposta:**
```json
{
  "trade_id": 123,
  "symbol": "BTCUSDT",
  "side": "BUY",
  "quantity": 0.01,
  "price": 126034.28,
  "total_cost": 1260.47,
  "fee": 1.26,
  "status": "FILLED",
  "executed_at": "2025-10-07T12:30:00"
}
```

**Note:**
- `price`: Se `null`, usa prezzo di mercato corrente
- `order_type`: `MARKET` o `LIMIT`
- `fee`: 0.1% del valore totale (configurabile)

---

### **4. Vendi Crypto**
```bash
POST /api/v1/paper-trading/portfolio/{portfolio_id}/sell
```

**Body:**
```json
{
  "symbol": "BTCUSDT",
  "quantity": 0.005,
  "price": null,
  "order_type": "MARKET"
}
```

**Risposta:**
```json
{
  "trade_id": 124,
  "symbol": "BTCUSDT",
  "side": "SELL",
  "quantity": 0.005,
  "price": 126500.00,
  "total_cost": 631.87,
  "fee": 0.63,
  "realized_pnl": 2.33,
  "realized_pnl_percentage": 0.37,
  "status": "FILLED",
  "executed_at": "2025-10-07T13:00:00"
}
```

---

### **5. Visualizza Posizioni**
```bash
GET /api/v1/paper-trading/portfolio/{portfolio_id}/positions
```

**Risposta:**
```json
[
  {
    "id": 1,
    "symbol": "BTCUSDT",
    "quantity": 0.02,
    "avg_entry_price": 125000.00,
    "current_price": 126034.28,
    "market_value": 2520.69,
    "total_cost": 2502.50,
    "unrealized_pnl": 18.19,
    "unrealized_pnl_percentage": 0.73,
    "stop_loss_price": 120000.00,
    "take_profit_price": 130000.00,
    "opened_at": "2025-10-07T11:00:00"
  },
  {
    "id": 2,
    "symbol": "ETHUSDT",
    "quantity": 0.5,
    "avg_entry_price": 4700.00,
    "current_price": 4708.88,
    "market_value": 2354.44,
    "total_cost": 2352.35,
    "unrealized_pnl": 2.09,
    "unrealized_pnl_percentage": 0.09,
    "stop_loss_price": null,
    "take_profit_price": null,
    "opened_at": "2025-10-07T12:00:00"
  }
]
```

---

### **6. Storico Trades**
```bash
GET /api/v1/paper-trading/portfolio/{portfolio_id}/trades?limit=50
```

**Risposta:**
```json
[
  {
    "id": 124,
    "symbol": "BTCUSDT",
    "side": "SELL",
    "quantity": 0.005,
    "price": 126500.00,
    "total_value": 632.50,
    "fee": 0.63,
    "total_cost": 631.87,
    "realized_pnl": 2.33,
    "realized_pnl_percentage": 0.37,
    "order_type": "MARKET",
    "status": "FILLED",
    "executed_at": "2025-10-07T13:00:00"
  },
  {
    "id": 123,
    "symbol": "BTCUSDT",
    "side": "BUY",
    "quantity": 0.01,
    "price": 126034.28,
    "total_value": 1260.34,
    "fee": 1.26,
    "total_cost": 1261.60,
    "realized_pnl": 0.00,
    "realized_pnl_percentage": 0.00,
    "order_type": "MARKET",
    "status": "FILLED",
    "executed_at": "2025-10-07T12:30:00"
  }
]
```

---

### **7. Visualizza Saldo**
```bash
# Tutti gli asset
GET /api/v1/paper-trading/portfolio/{portfolio_id}/balance

# Asset specifico
GET /api/v1/paper-trading/portfolio/{portfolio_id}/balance?asset=BTC
```

**Risposta (tutti gli asset):**
```json
{
  "balances": [
    {
      "asset": "USDT",
      "free": 7500.00,
      "locked": 0.00,
      "total": 7500.00,
      "usd_value": 7500.00
    },
    {
      "asset": "BTC",
      "free": 0.02,
      "locked": 0.00,
      "total": 0.02,
      "usd_value": 2520.69
    },
    {
      "asset": "ETH",
      "free": 0.5,
      "locked": 0.00,
      "total": 0.5,
      "usd_value": 2354.44
    }
  ]
}
```

---

### **8. Chiudi Posizione**
```bash
POST /api/v1/paper-trading/portfolio/{portfolio_id}/position/{position_id}/close
```

**Risposta:**
```json
{
  "trade_id": 125,
  "symbol": "BTCUSDT",
  "side": "SELL",
  "quantity": 0.02,
  "price": 126034.28,
  "total_cost": 2519.43,
  "fee": 2.52,
  "realized_pnl": 14.41,
  "realized_pnl_percentage": 0.58,
  "status": "FILLED",
  "executed_at": "2025-10-07T14:00:00"
}
```

---

### **9. Imposta Stop Loss**
```bash
PUT /api/v1/paper-trading/portfolio/{portfolio_id}/position/{position_id}/stop-loss
```

**Body:**
```json
{
  "stop_loss_price": 120000.00
}
```

**Risposta:**
```json
{
  "position_id": 1,
  "symbol": "BTCUSDT",
  "stop_loss_price": 120000.00,
  "message": "Stop loss set successfully"
}
```

---

### **10. Imposta Take Profit**
```bash
PUT /api/v1/paper-trading/portfolio/{portfolio_id}/position/{position_id}/take-profit
```

**Body:**
```json
{
  "take_profit_price": 130000.00
}
```

**Risposta:**
```json
{
  "position_id": 1,
  "symbol": "BTCUSDT",
  "take_profit_price": 130000.00,
  "message": "Take profit set successfully"
}
```

---

### **11. Aggiorna Valore Portfolio**
```bash
POST /api/v1/paper-trading/portfolio/{portfolio_id}/update-value
```

Aggiorna il valore del portfolio in base ai prezzi di mercato correnti.

**Risposta:**
```json
{
  "portfolio_id": 1,
  "cash_balance": 7500.00,
  "invested_value": 2600.00,
  "total_value": 10100.00,
  "total_pnl": 100.00,
  "total_pnl_percentage": 1.00,
  "unrealized_pnl": 50.00,
  "updated_at": "2025-10-07T14:00:00"
}
```

---

## 💰 **Sistema di Commissioni**

### **Fee di Trading:**
- **Default**: 0.1% (10 basis points)
- **Applicata su**: Sia acquisti che vendite
- **Esempio**:
  ```
  Acquisto: $1,000 → Fee: $1.00 → Total: $1,001.00
  Vendita: $1,100 → Fee: $1.10 → Proceeds: $1,098.90
  ```

### **Configurabile:**
```python
# In paper_trading_service.py
self.default_fee_percentage = Decimal("0.001")  # 0.1%
```

---

## 📈 **Calcolo P&L**

### **Unrealized P&L (Posizioni Aperte):**
```python
unrealized_pnl = (current_price - avg_entry_price) * quantity
unrealized_pnl_% = (unrealized_pnl / total_cost) * 100
```

### **Realized P&L (Posizioni Chiuse):**
```python
realized_pnl = (sell_price - avg_entry_price) * quantity - fees
realized_pnl_% = (realized_pnl / cost_basis) * 100
```

### **Total P&L:**
```python
total_pnl = realized_pnl + unrealized_pnl
total_pnl_% = (total_pnl / initial_capital) * 100
```

---

## 🎮 **Esempi Pratici**

### **Scenario Completo: Day Trading**

```javascript
// 1. Crea portfolio con $10,000
const portfolio = await fetch('/api/v1/paper-trading/portfolio', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: "Day Trading Portfolio",
    initial_capital: 10000
  })
}).then(r => r.json());

console.log(`Portfolio creato: ID ${portfolio.id}`);

// 2. Compra 0.02 BTC
const buyTrade = await fetch(`/api/v1/paper-trading/portfolio/${portfolio.id}/buy`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    symbol: "BTCUSDT",
    quantity: 0.02,
    order_type: "MARKET"
  })
}).then(r => r.json());

console.log(`Acquistato ${buyTrade.quantity} BTC a $${buyTrade.price}`);
console.log(`Costo totale: $${buyTrade.total_cost} (fee: $${buyTrade.fee})`);

// 3. Visualizza posizioni
const positions = await fetch(`/api/v1/paper-trading/portfolio/${portfolio.id}/positions`, {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

positions.forEach(pos => {
  console.log(`${pos.symbol}: ${pos.quantity} @ $${pos.current_price}`);
  console.log(`P&L: $${pos.unrealized_pnl} (${pos.unrealized_pnl_percentage}%)`);
});

// 4. Imposta stop loss e take profit
await fetch(`/api/v1/paper-trading/portfolio/${portfolio.id}/position/${positions[0].id}/stop-loss`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    stop_loss_price: 120000
  })
});

await fetch(`/api/v1/paper-trading/portfolio/${portfolio.id}/position/${positions[0].id}/take-profit`, {
  method: 'PUT',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    take_profit_price: 130000
  })
});

// 5. Vendi metà posizione
const sellTrade = await fetch(`/api/v1/paper-trading/portfolio/${portfolio.id}/sell`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    symbol: "BTCUSDT",
    quantity: 0.01,
    order_type: "MARKET"
  })
}).then(r => r.json());

console.log(`Venduto ${sellTrade.quantity} BTC a $${sellTrade.price}`);
console.log(`P&L realizzato: $${sellTrade.realized_pnl} (${sellTrade.realized_pnl_percentage}%)`);

// 6. Visualizza storico trades
const trades = await fetch(`/api/v1/paper-trading/portfolio/${portfolio.id}/trades?limit=10`, {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

trades.forEach(trade => {
  console.log(`${trade.side} ${trade.quantity} ${trade.symbol} @ $${trade.price}`);
  if (trade.side === 'SELL') {
    console.log(`  P&L: $${trade.realized_pnl} (${trade.realized_pnl_percentage}%)`);
  }
});

// 7. Aggiorna valore portfolio
const summary = await fetch(`/api/v1/paper-trading/portfolio/${portfolio.id}/update-value`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());

console.log(`Portfolio value: $${summary.total_value}`);
console.log(`Total P&L: $${summary.total_pnl} (${summary.total_pnl_percentage}%)`);
```

---

## 🔄 **Switch a Trading Reale**

### **Quando sei pronto per il trading reale:**

```python
from app.services.trading.trading_factory import get_trading_service

# Paper trading (default)
paper_service = get_trading_service(mode="paper")

# Live trading (quando pronto)
live_service = get_trading_service(
    mode="live",
    exchange="binance",
    api_key="your_binance_api_key",
    secret_key="your_binance_secret"
)

# Stessa interfaccia per entrambi!
await live_service.buy(portfolio_id, "BTCUSDT", 0.01)
```

### **Cosa Fare:**

1. **Configura API Keys** in database per l'utente
2. **Modifica factory** per usare `mode="live"`
3. **Completa implementazione** in `LiveTradingService`
4. **Test su testnet** prima di production

**Nota**: LiveTradingService ha già scheletro implementato, basta completare i TODO!

---

## 🎯 **Features Implementate**

### **Portfolio Management:**
- ✅ Crea portfolio multipli
- ✅ Capitale iniziale personalizzabile
- ✅ Tracking valore real-time
- ✅ Metriche performance complete

### **Trading:**
- ✅ Ordini BUY/SELL
- ✅ Market orders (prezzo corrente)
- ✅ Limit orders (prezzo specifico)
- ✅ Fee di trading realistiche
- ✅ Validazioni complete

### **Risk Management:**
- ✅ Stop loss per posizione
- ✅ Take profit per posizione
- ✅ Max drawdown tracking
- ✅ Position sizing

### **Analytics:**
- ✅ P&L realizzato e non realizzato
- ✅ Win rate
- ✅ Performance percentuale
- ✅ Storico trades completo

### **Balances:**
- ✅ Tracking multi-asset
- ✅ Conversione USD value
- ✅ Free/Locked distinction

---

## 🧪 **Testing**

### **Test Manuale:**

```bash
# 1. Crea portfolio
curl -X POST 'http://localhost:8000/api/v1/paper-trading/portfolio' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"name": "Test Portfolio", "initial_capital": 10000}'

# 2. Compra BTC
curl -X POST 'http://localhost:8000/api/v1/paper-trading/portfolio/1/buy' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"symbol": "BTCUSDT", "quantity": 0.01}'

# 3. Visualizza posizioni
curl 'http://localhost:8000/api/v1/paper-trading/portfolio/1/positions' \
  -H 'Authorization: Bearer YOUR_TOKEN'

# 4. Vendi
curl -X POST 'http://localhost:8000/api/v1/paper-trading/portfolio/1/sell' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{"symbol": "BTCUSDT", "quantity": 0.005}'
```

---

## 📊 **Database Migration**

Per creare le tabelle:

```bash
# Genera migration
alembic revision --autogenerate -m "Add paper trading tables"

# Applica migration
alembic upgrade head
```

Oppure le tabelle vengono create automaticamente all'avvio se usi `init_db()`.

---

## 🔐 **Sicurezza**

### **Autenticazione:**
Tutti gli endpoint richiedono autenticazione JWT:
```
Authorization: Bearer <your_token>
```

### **Validazioni:**
- ✅ User ownership: Solo owner può accedere al portfolio
- ✅ Quantity validation: Quantità > 0
- ✅ Balance check: Verifica fondi sufficienti
- ✅ Position check: Verifica posizione esistente per vendita

---

## 🎨 **Componente React Esempio**

```jsx
function PaperTradingDashboard() {
  const [portfolio, setPortfolio] = useState(null);
  const [positions, setPositions] = useState([]);
  
  // Load portfolio
  useEffect(() => {
    loadPortfolio();
    const interval = setInterval(loadPortfolio, 30000);
    return () => clearInterval(interval);
  }, []);
  
  const loadPortfolio = async () => {
    const data = await fetch('/api/v1/paper-trading/portfolio/1', {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());
    
    setPortfolio(data);
    
    const pos = await fetch('/api/v1/paper-trading/portfolio/1/positions', {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());
    
    setPositions(pos);
  };
  
  const handleBuy = async (symbol, quantity) => {
    await fetch(`/api/v1/paper-trading/portfolio/1/buy`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ symbol, quantity, order_type: 'MARKET' })
    });
    
    loadPortfolio();
  };
  
  const handleSell = async (symbol, quantity) => {
    await fetch(`/api/v1/paper-trading/portfolio/1/sell`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ symbol, quantity, order_type: 'MARKET' })
    });
    
    loadPortfolio();
  };
  
  return (
    <div className="paper-trading-dashboard">
      {/* Portfolio Summary */}
      <div className="portfolio-summary">
        <h2>{portfolio?.name}</h2>
        <div className="stats">
          <div>Total Value: ${portfolio?.total_value?.toLocaleString()}</div>
          <div className={portfolio?.total_pnl >= 0 ? 'positive' : 'negative'}>
            P&L: ${portfolio?.total_pnl?.toFixed(2)} ({portfolio?.total_pnl_percentage?.toFixed(2)}%)
          </div>
          <div>Win Rate: {portfolio?.win_rate?.toFixed(2)}%</div>
          <div>Cash: ${portfolio?.cash_balance?.toLocaleString()}</div>
        </div>
      </div>
      
      {/* Positions */}
      <div className="positions">
        <h3>Open Positions</h3>
        {positions.map(pos => (
          <div key={pos.id} className="position-card">
            <h4>{pos.symbol}</h4>
            <div>Quantity: {pos.quantity}</div>
            <div>Entry: ${pos.avg_entry_price}</div>
            <div>Current: ${pos.current_price}</div>
            <div className={pos.unrealized_pnl >= 0 ? 'positive' : 'negative'}>
              P&L: ${pos.unrealized_pnl} ({pos.unrealized_pnl_percentage}%)
            </div>
            <button onClick={() => handleSell(pos.symbol, pos.quantity)}>
              Close Position
            </button>
          </div>
        ))}
      </div>
      
      {/* Trading Form */}
      <TradingForm onBuy={handleBuy} onSell={handleSell} />
    </div>
  );
}
```

---

## 🚀 **Roadmap per Live Trading**

### **Quando vuoi passare al trading reale:**

**Step 1**: Aggiungi API keys al database
```sql
INSERT INTO api_keys (user_id, exchange, api_key, secret_key)
VALUES (1, 'binance', 'your_key', 'your_secret');
```

**Step 2**: Completa LiveTradingService
```python
# In live_trading_service.py
# Completa i metodi TODO:
# - create_portfolio() → Sync with exchange
# - get_positions() → Fetch from exchange
# - update_portfolio_value() → Calculate from real balances
```

**Step 3**: Aggiungi endpoint per switch mode
```python
PUT /api/v1/paper-trading/portfolio/{id}/switch-mode
{
  "mode": "live",
  "exchange": "binance"
}
```

**Step 4**: Test su testnet
```python
service = get_trading_service(
    mode="live",
    exchange="binance",
    api_key="testnet_key",
    secret_key="testnet_secret"
)
```

---

## ⚠️ **Note Importanti**

### **Paper Trading:**
- ✅ Nessun rischio reale
- ✅ Capitale virtuale
- ✅ Prezzi da database (real-time)
- ✅ Esecuzione istantanea
- ✅ Nessun slippage

### **Live Trading (quando implementato):**
- ⚠️ Capitale reale a rischio
- ⚠️ Esecuzione su exchange vero
- ⚠️ Possibile slippage
- ⚠️ Latenza di rete
- ⚠️ Richiede API keys verificate

---

## 🎉 **Vantaggi dell'Architettura**

### **1. Interfaccia Comune:**
```python
# Stesso codice per paper e live!
service.buy(portfolio_id, "BTCUSDT", 0.01)
```

### **2. Switch Facile:**
```python
# Cambia solo mode
service = get_trading_service(mode="paper")  # o "live"
```

### **3. Testing Sicuro:**
```python
# Testa strategie senza rischio
paper_service.buy(...)
paper_service.sell(...)
```

### **4. Codice Riusabile:**
```python
# Frontend uguale per paper e live
<TradingForm service={tradingService} />
```

---

## 📚 **Documentazione Correlata**

- `app/models/paper_trading.py` - Modelli database
- `app/services/trading/base_trading_service.py` - Interfaccia base
- `app/services/trading/paper_trading_service.py` - Implementazione paper
- `app/services/trading/live_trading_service.py` - Stub per live
- `app/services/trading/trading_factory.py` - Factory pattern
- `app/api/v1/paper_trading.py` - API endpoints
- `app/schemas/paper_trading.py` - Pydantic schemas

---

Il sistema è pronto per l'uso! Puoi iniziare subito con il paper trading e passare al live quando sei pronto. 🚀
