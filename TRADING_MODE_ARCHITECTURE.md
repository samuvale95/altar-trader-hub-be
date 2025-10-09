# Trading Mode Architecture

## Panoramica

Il sistema ora supporta un'architettura unificata dove il **trading mode** (paper o live) è gestito a livello di utente, non a livello di portfolio. Questo significa che quando un utente fa login, sceglie se operare in modalità paper trading (simulata) o live trading (reale), e tutte le operazioni successive useranno quella modalità.

## Cambiamenti Architetturali

### 1. Modello User Aggiornato

Il modello `User` ora include il campo `trading_mode`:

```python
class TradingMode(enum.Enum):
    PAPER = "paper"  # Virtual trading
    LIVE = "live"    # Real trading with actual money

class User(Base):
    # ... altri campi ...
    trading_mode = Column(SQLEnum(TradingMode), default=TradingMode.PAPER, nullable=False)
```

### 2. Login con Trading Mode

Lo schema di login ora accetta un parametro `trading_mode`:

```python
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    trading_mode: Optional[TradingModeEnum] = TradingModeEnum.PAPER
```

**Esempio di richiesta di login:**

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "trading_mode": "paper"
  }'
```

**Risposta:**

```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 86400,
  "trading_mode": "paper"
}
```

### 3. Unified Trading Service

È stato creato un nuovo servizio `UnifiedTradingService` che:
- Controlla il `trading_mode` dell'utente
- Instrada le richieste al servizio appropriato (paper o live)
- Logga tutte le operazioni con il mode corrispondente

### 4. Nuovi Endpoint API Unificati

I nuovi endpoint sono sotto `/api/v1/trading/` e funzionano per entrambe le modalità:

#### Gestione Portfolio

- `POST /api/v1/trading/portfolios` - Crea un nuovo portfolio
- `GET /api/v1/trading/portfolios` - Lista tutti i portfolio dell'utente
- `GET /api/v1/trading/portfolios/{portfolio_id}` - Dettagli di un portfolio
- `POST /api/v1/trading/portfolios/{portfolio_id}/update-value` - Aggiorna il valore del portfolio

#### Trading

- `POST /api/v1/trading/portfolios/{portfolio_id}/buy` - Esegue un ordine di acquisto
- `POST /api/v1/trading/portfolios/{portfolio_id}/sell` - Esegue un ordine di vendita
- `GET /api/v1/trading/portfolios/{portfolio_id}/trades` - Storico dei trade

#### Posizioni

- `GET /api/v1/trading/portfolios/{portfolio_id}/positions` - Lista delle posizioni
- `POST /api/v1/trading/portfolios/{portfolio_id}/positions/{position_id}/close` - Chiude una posizione
- `PUT /api/v1/trading/portfolios/{portfolio_id}/positions/{position_id}/stop-loss` - Imposta stop loss
- `PUT /api/v1/trading/portfolios/{portfolio_id}/positions/{position_id}/take-profit` - Imposta take profit

#### Balance

- `GET /api/v1/trading/portfolios/{portfolio_id}/balance` - Ottiene il balance del portfolio

## Separazione dei Dati

### Tabelle Database

I dati rimangono separati in tabelle diverse:

**Paper Trading:**
- `paper_portfolios`
- `paper_positions`
- `paper_trades`
- `paper_balances`

**Live Trading:**
- `portfolios`
- `positions`
- `orders`
- `balances`

Il servizio unificato decide automaticamente quale tabella usare in base al `trading_mode` dell'utente.

### Dati Storici

I dati di mercato storici (`market_data` table) sono condivisi tra entrambe le modalità e non vengono duplicati.

## Flusso di Utilizzo

### 1. Registrazione

```bash
POST /api/v1/auth/register
{
  "email": "trader@example.com",
  "password": "securepassword",
  "first_name": "John",
  "last_name": "Doe"
}
```

L'utente viene creato con `trading_mode = PAPER` di default.

### 2. Login (Paper Mode)

```bash
POST /api/v1/auth/login
{
  "email": "trader@example.com",
  "password": "securepassword",
  "trading_mode": "paper"
}
```

### 3. Creazione Portfolio

```bash
POST /api/v1/trading/portfolios
{
  "name": "My Trading Portfolio",
  "description": "Portfolio for crypto trading",
  "initial_capital": 10000
}
```

Se l'utente è in paper mode, viene creato un record in `paper_portfolios`.
Se l'utente è in live mode, viene creato un record in `portfolios`.

### 4. Operazioni di Trading

Tutte le operazioni successive (buy, sell, etc.) vengono eseguite sulla tabella corretta in base al mode dell'utente.

## Cambio di Modalità

Per cambiare modalità, l'utente deve:
1. Fare logout
2. Fare login specificando il nuovo `trading_mode`

```bash
# Passa a Live Mode
POST /api/v1/auth/login
{
  "email": "trader@example.com",
  "password": "securepassword",
  "trading_mode": "live"
}
```

## Retrocompatibilità

Gli endpoint vecchi sotto `/api/v1/paper-trading/` rimangono disponibili per retrocompatibilità, ma è consigliato usare i nuovi endpoint unificati `/api/v1/trading/`.

## Sicurezza

- Il `trading_mode` viene salvato nel database utente
- Ogni operazione controlla il mode dell'utente autenticato
- Non è possibile mescolare operazioni paper e live nella stessa sessione
- Il live trading richiede API keys configurate

## Implementazione Futura

Attualmente, il **live trading service** non è ancora implementato completamente. Quando un utente è in live mode, il sistema:
- Logga un warning
- Usa temporaneamente il paper service
- Quando il live service sarà pronto, le operazioni verranno automaticamente instradate correttamente

## Note Importanti

1. **I portfolio sono separati**: Un utente può avere portfolio sia in paper che in live mode, ma sono completamente separati
2. **Il mode non può essere cambiato a livello di portfolio**: È una scelta a livello di sessione utente
3. **I dati non vengono condivisi**: Le posizioni e i trade in paper mode non influenzano quelli in live mode
4. **Testing sicuro**: Gli utenti possono testare strategie in paper mode prima di passare a live mode

## Vantaggi

- ✅ Interfaccia unificata per utenti
- ✅ Facile passaggio tra paper e live trading
- ✅ Dati completamente separati per sicurezza
- ✅ Logging dettagliato del mode in uso
- ✅ Flessibilità per future estensioni
- ✅ Retrocompatibilità con API esistenti

