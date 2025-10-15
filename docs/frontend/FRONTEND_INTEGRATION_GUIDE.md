# Frontend Integration Guide - Trading Mode Architecture

## Executive Summary

### Panoramica dei Cambiamenti

Il backend di Altar Trader Hub ha subito una riorganizzazione architetturale significativa. La modifica principale riguarda la gestione del **trading mode** (paper vs live), che ora avviene a **livello di utente** anziché a livello di portfolio.

**Prima:** Ogni portfolio aveva la sua modalità (paper o live).  
**Ora:** L'utente sceglie la modalità al login, e tutti i portfolio e le operazioni usano quella modalità.

### Impatto sul Frontend

1. **Login aggiornato:** Richiede un nuovo parametro `trading_mode`
2. **Nuovi endpoint API:** Percorso unificato `/api/v1/trading/` invece di `/api/v1/paper-trading/`
3. **State management:** Necessità di tracciare il `trading_mode` corrente dell'utente
4. **UI/UX:** Aggiungere indicatori visivi del mode attivo (badge, banner, colori)

### Vantaggi per l'Utente

- Esperienza utente semplificata: una sola interfaccia per entrambe le modalità
- Passaggio facile tra paper e live trading tramite logout/login
- Dati completamente separati tra le due modalità per maggiore sicurezza
- Possibilità di testare strategie in paper mode prima di passare a live

---

## Breaking Changes

### 1. Trading Mode a Livello Utente

Il trading mode **non è più** una proprietà del portfolio, ma dell'utente stesso. Questo significa:

- Non puoi più creare portfolio con modalità diverse nella stessa sessione
- Il mode viene scelto al login e resta attivo per tutta la sessione
- Per cambiare mode, l'utente deve fare logout e login nuovamente

### 2. Nuovi Endpoint API

Gli endpoint sotto `/api/v1/paper-trading/` sono **deprecati** (ma ancora funzionanti per retrocompatibilità).

**Usa invece:** `/api/v1/trading/`

### 3. Parametro Trading Mode nel Login

Il login ora **accetta** (opzionale) il parametro `trading_mode`:

```json
{
  "email": "user@example.com",
  "password": "password",
  "trading_mode": "paper"  // o "live"
}
```

Se omesso, default è `"paper"`.

### 4. Response del Login Include Trading Mode

La risposta del login include il campo `trading_mode`:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "expires_in": 86400,
  "trading_mode": "paper"  // NUOVO CAMPO
}
```

---

## Autenticazione Aggiornata

### TypeScript Interfaces

#### Login Request

```typescript
interface LoginRequest {
  email: string;
  password: string;
  trading_mode?: 'paper' | 'live'; // Default: 'paper'
}
```

#### Login Response

```typescript
interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  trading_mode: 'paper' | 'live'; // NUOVO CAMPO
}
```

#### User Response

```typescript
interface User {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  is_verified: boolean;
  trading_mode: 'paper' | 'live'; // NUOVO CAMPO
  created_at: string;
  updated_at?: string;
  last_login?: string;
}
```

### Esempio di Implementazione Login

```typescript
// services/auth.service.ts
export const authService = {
  async login(email: string, password: string, tradingMode: 'paper' | 'live' = 'paper'): Promise<LoginResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
        trading_mode: tradingMode,
      }),
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data: LoginResponse = await response.json();
    
    // Salva il token e il trading mode
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('trading_mode', data.trading_mode);
    
    return data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user');
    }

    return response.json();
  },

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('trading_mode');
  },
};
```

---

## Nuovi Endpoint API

### Mappatura Endpoint

| Vecchio Endpoint (Deprecato) | Nuovo Endpoint (Consigliato) |
|------------------------------|-------------------------------|
| `POST /api/v1/paper-trading/portfolio` | `POST /api/v1/trading/portfolios` |
| `GET /api/v1/paper-trading/portfolios` | `GET /api/v1/trading/portfolios` |
| `GET /api/v1/paper-trading/portfolio/{id}` | `GET /api/v1/trading/portfolios/{id}` |
| `POST /api/v1/paper-trading/portfolio/{id}/buy` | `POST /api/v1/trading/portfolios/{id}/buy` |
| `POST /api/v1/paper-trading/portfolio/{id}/sell` | `POST /api/v1/trading/portfolios/{id}/sell` |
| `GET /api/v1/paper-trading/portfolio/{id}/positions` | `GET /api/v1/trading/portfolios/{id}/positions` |
| `GET /api/v1/paper-trading/portfolio/{id}/trades` | `GET /api/v1/trading/portfolios/{id}/trades` |

### Lista Completa Endpoint Unificati

#### Portfolio Management

```typescript
// Crea un nuovo portfolio
POST /api/v1/trading/portfolios
Body: {
  name: string;
  description?: string;
  initial_capital: number; // Default: 10000
}

// Lista tutti i portfolio dell'utente
GET /api/v1/trading/portfolios

// Ottiene i dettagli di un portfolio
GET /api/v1/trading/portfolios/{portfolio_id}

// Aggiorna il valore del portfolio
POST /api/v1/trading/portfolios/{portfolio_id}/update-value
```

#### Trading Operations

```typescript
// Esegue un ordine di acquisto
POST /api/v1/trading/portfolios/{portfolio_id}/buy
Body: {
  symbol: string;        // es. "BTCUSDT"
  quantity: number;
  price?: number;        // Se omesso, usa il prezzo di mercato
  order_type?: string;   // "MARKET" o "LIMIT", default: "MARKET"
}

// Esegue un ordine di vendita
POST /api/v1/trading/portfolios/{portfolio_id}/sell
Body: {
  symbol: string;
  quantity: number;
  price?: number;
  order_type?: string;
}

// Storico dei trade
GET /api/v1/trading/portfolios/{portfolio_id}/trades?limit=100
```

#### Position Management

```typescript
// Lista delle posizioni aperte
GET /api/v1/trading/portfolios/{portfolio_id}/positions

// Chiude una posizione completamente
POST /api/v1/trading/portfolios/{portfolio_id}/positions/{position_id}/close

// Imposta stop loss
PUT /api/v1/trading/portfolios/{portfolio_id}/positions/{position_id}/stop-loss
Body: {
  stop_loss_price: number;
}

// Imposta take profit
PUT /api/v1/trading/portfolios/{portfolio_id}/positions/{position_id}/take-profit
Body: {
  take_profit_price: number;
}
```

#### Balance

```typescript
// Ottiene il balance del portfolio (tutti gli asset)
GET /api/v1/trading/portfolios/{portfolio_id}/balance

// Ottiene il balance di un asset specifico
GET /api/v1/trading/portfolios/{portfolio_id}/balance?asset=BTC
```

---

## TypeScript Types & Interfaces

### Complete Type Definitions

```typescript
// types/trading.types.ts

export type TradingMode = 'paper' | 'live';

export type OrderType = 'MARKET' | 'LIMIT';

export type OrderSide = 'BUY' | 'SELL';

export type OrderStatus = 'FILLED' | 'PARTIAL' | 'CANCELLED';

export interface Portfolio {
  id: number;
  name: string;
  description: string | null;
  mode: string;
  initial_capital: number;
  cash_balance: number;
  invested_value: number;
  total_value: number;
  total_pnl: number;
  total_pnl_percentage: number;
  realized_pnl: number;
  unrealized_pnl: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  max_drawdown: number;
  created_at: string;
  updated_at: string | null;
}

export interface CreatePortfolioRequest {
  name: string;
  description?: string;
  initial_capital?: number; // Default: 10000, Max: 1000000
}

export interface Position {
  id: number;
  symbol: string;
  quantity: number;
  avg_entry_price: number;
  current_price: number;
  market_value: number;
  total_cost: number;
  unrealized_pnl: number;
  unrealized_pnl_percentage: number;
  stop_loss_price: number | null;
  take_profit_price: number | null;
  opened_at: string;
}

export interface TradeRequest {
  symbol: string;
  quantity: number;
  price?: number;
  order_type?: OrderType;
}

export interface TradeResponse {
  trade_id: number;
  symbol: string;
  side: OrderSide;
  quantity: number;
  price: number;
  total_cost: number;
  fee: number;
  realized_pnl?: number;
  realized_pnl_percentage?: number;
  status: OrderStatus;
  executed_at: string;
}

export interface TradeHistory {
  id: number;
  symbol: string;
  side: OrderSide;
  quantity: number;
  price: number;
  total_value: number;
  fee: number;
  total_cost: number;
  realized_pnl: number;
  realized_pnl_percentage: number;
  order_type: OrderType;
  status: OrderStatus;
  executed_at: string;
}

export interface Balance {
  asset: string;
  free: number;
  locked: number;
  total: number;
  usd_value: number;
}

export interface BalancesResponse {
  balances: Balance[];
}

export interface PortfolioSummary {
  portfolio_id: number;
  cash_balance: number;
  invested_value: number;
  total_value: number;
  total_pnl: number;
  total_pnl_percentage: number;
  unrealized_pnl: number;
  updated_at: string;
}

export interface SetStopLossRequest {
  stop_loss_price: number;
}

export interface SetTakeProfitRequest {
  take_profit_price: number;
}
```

---

## State Management

### React Context Example

```typescript
// contexts/TradingContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, Portfolio, TradingMode } from '../types/trading.types';
import { authService } from '../services/auth.service';

interface TradingContextType {
  user: User | null;
  tradingMode: TradingMode;
  portfolios: Portfolio[];
  isLoading: boolean;
  login: (email: string, password: string, mode: TradingMode) => Promise<void>;
  logout: () => void;
  switchMode: (mode: TradingMode) => Promise<void>;
  refreshPortfolios: () => Promise<void>;
}

const TradingContext = createContext<TradingContextType | undefined>(undefined);

export const TradingProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [tradingMode, setTradingMode] = useState<TradingMode>('paper');
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Carica i dati iniziali
    const initializeAuth = async () => {
      const token = localStorage.getItem('access_token');
      const storedMode = localStorage.getItem('trading_mode') as TradingMode;
      
      if (token) {
        try {
          const userData = await authService.getCurrentUser();
          setUser(userData);
          setTradingMode(storedMode || userData.trading_mode);
        } catch (error) {
          // Token scaduto o invalido
          authService.logout();
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string, mode: TradingMode = 'paper') => {
    setIsLoading(true);
    try {
      const response = await authService.login(email, password, mode);
      const userData = await authService.getCurrentUser();
      
      setUser(userData);
      setTradingMode(response.trading_mode);
      
      // Carica i portfolio
      await refreshPortfolios();
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setTradingMode('paper');
    setPortfolios([]);
  };

  const switchMode = async (mode: TradingMode) => {
    if (!user) return;
    
    // Per cambiare mode, devi fare logout e login nuovamente
    const email = user.email;
    logout();
    
    // Chiedi all'utente di reinserire la password
    // Questo dovrebbe essere gestito dal componente UI
    throw new Error('REAUTHENTICATION_REQUIRED');
  };

  const refreshPortfolios = async () => {
    if (!user) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/trading/portfolios`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setPortfolios(data);
      }
    } catch (error) {
      console.error('Failed to refresh portfolios:', error);
    }
  };

  return (
    <TradingContext.Provider
      value={{
        user,
        tradingMode,
        portfolios,
        isLoading,
        login,
        logout,
        switchMode,
        refreshPortfolios,
      }}
    >
      {children}
    </TradingContext.Provider>
  );
};

export const useTrading = () => {
  const context = useContext(TradingContext);
  if (context === undefined) {
    throw new Error('useTrading must be used within a TradingProvider');
  }
  return context;
};
```

### Zustand Store Example

```typescript
// stores/tradingStore.ts
import create from 'zustand';
import { User, Portfolio, TradingMode } from '../types/trading.types';

interface TradingState {
  user: User | null;
  tradingMode: TradingMode;
  portfolios: Portfolio[];
  setUser: (user: User | null) => void;
  setTradingMode: (mode: TradingMode) => void;
  setPortfolios: (portfolios: Portfolio[]) => void;
  reset: () => void;
}

export const useTradingStore = create<TradingState>((set) => ({
  user: null,
  tradingMode: (localStorage.getItem('trading_mode') as TradingMode) || 'paper',
  portfolios: [],
  
  setUser: (user) => set({ user }),
  setTradingMode: (mode) => {
    localStorage.setItem('trading_mode', mode);
    set({ tradingMode: mode });
  },
  setPortfolios: (portfolios) => set({ portfolios }),
  
  reset: () => set({
    user: null,
    tradingMode: 'paper',
    portfolios: [],
  }),
}));
```

---

## Esempi di Codice React

### Login Component

```typescript
// components/LoginForm.tsx
import React, { useState } from 'react';
import { useTrading } from '../contexts/TradingContext';
import { TradingMode } from '../types/trading.types';

export const LoginForm: React.FC = () => {
  const { login, isLoading } = useTrading();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [tradingMode, setTradingMode] = useState<TradingMode>('paper');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await login(email, password, tradingMode);
    } catch (err) {
      setError('Login failed. Please check your credentials.');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="login-form">
      <h2>Login to Altar Trader Hub</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="form-group">
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>

      <div className="form-group">
        <label>Trading Mode</label>
        <div className="mode-selector">
          <label className={tradingMode === 'paper' ? 'active' : ''}>
            <input
              type="radio"
              name="tradingMode"
              value="paper"
              checked={tradingMode === 'paper'}
              onChange={() => setTradingMode('paper')}
            />
            <span className="mode-badge paper">Paper Trading</span>
            <small>Safe simulation mode - No real money</small>
          </label>

          <label className={tradingMode === 'live' ? 'active' : ''}>
            <input
              type="radio"
              name="tradingMode"
              value="live"
              checked={tradingMode === 'live'}
              onChange={() => setTradingMode('live')}
            />
            <span className="mode-badge live">Live Trading</span>
            <small>⚠️ Real money - Use with caution</small>
          </label>
        </div>
      </div>

      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
};
```

### Trading Mode Badge Component

```typescript
// components/TradingModeBadge.tsx
import React from 'react';
import { useTrading } from '../contexts/TradingContext';

export const TradingModeBadge: React.FC = () => {
  const { tradingMode } = useTrading();

  return (
    <div className={`trading-mode-badge ${tradingMode}`}>
      <span className="mode-icon">
        {tradingMode === 'paper' ? '📝' : '💰'}
      </span>
      <span className="mode-text">
        {tradingMode === 'paper' ? 'Paper Mode' : 'Live Mode'}
      </span>
      {tradingMode === 'live' && (
        <span className="warning-icon" title="Real money trading">⚠️</span>
      )}
    </div>
  );
};
```

### API Service

```typescript
// services/trading.service.ts
import { 
  Portfolio, 
  CreatePortfolioRequest, 
  Position, 
  TradeRequest, 
  TradeResponse,
  TradeHistory,
  BalancesResponse,
  Balance
} from '../types/trading.types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const getAuthHeaders = () => ({
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
});

export const tradingService = {
  // Portfolio operations
  async createPortfolio(data: CreatePortfolioRequest): Promise<Portfolio> {
    const response = await fetch(`${API_BASE_URL}/api/v1/trading/portfolios`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error('Failed to create portfolio');
    }

    return response.json();
  },

  async getPortfolios(): Promise<Portfolio[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/trading/portfolios`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch portfolios');
    }

    return response.json();
  },

  async getPortfolio(portfolioId: number): Promise<Portfolio> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/trading/portfolios/${portfolioId}`,
      { headers: getAuthHeaders() }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch portfolio');
    }

    return response.json();
  },

  // Trading operations
  async buy(portfolioId: number, trade: TradeRequest): Promise<TradeResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/trading/portfolios/${portfolioId}/buy`,
      {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(trade),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to execute buy order');
    }

    return response.json();
  },

  async sell(portfolioId: number, trade: TradeRequest): Promise<TradeResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/trading/portfolios/${portfolioId}/sell`,
      {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(trade),
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to execute sell order');
    }

    return response.json();
  },

  // Position operations
  async getPositions(portfolioId: number): Promise<Position[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/trading/portfolios/${portfolioId}/positions`,
      { headers: getAuthHeaders() }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch positions');
    }

    return response.json();
  },

  async closePosition(portfolioId: number, positionId: number): Promise<TradeResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/trading/portfolios/${portfolioId}/positions/${positionId}/close`,
      {
        method: 'POST',
        headers: getAuthHeaders(),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to close position');
    }

    return response.json();
  },

  // Trade history
  async getTradeHistory(portfolioId: number, limit = 100): Promise<TradeHistory[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/trading/portfolios/${portfolioId}/trades?limit=${limit}`,
      { headers: getAuthHeaders() }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch trade history');
    }

    return response.json();
  },

  // Balance operations
  async getBalances(portfolioId: number): Promise<BalancesResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/trading/portfolios/${portfolioId}/balance`,
      { headers: getAuthHeaders() }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch balances');
    }

    return response.json();
  },

  async getBalance(portfolioId: number, asset: string): Promise<Balance> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/trading/portfolios/${portfolioId}/balance?asset=${asset}`,
      { headers: getAuthHeaders() }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch balance');
    }

    return response.json();
  },
};
```

### Portfolio Component

```typescript
// components/PortfolioCard.tsx
import React from 'react';
import { Portfolio } from '../types/trading.types';
import { useTrading } from '../contexts/TradingContext';

interface PortfolioCardProps {
  portfolio: Portfolio;
}

export const PortfolioCard: React.FC<PortfolioCardProps> = ({ portfolio }) => {
  const { tradingMode } = useTrading();

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <div className={`portfolio-card ${tradingMode}`}>
      <div className="portfolio-header">
        <h3>{portfolio.name}</h3>
        <span className={`mode-badge ${tradingMode}`}>
          {tradingMode === 'paper' ? '📝 PAPER' : '💰 LIVE'}
        </span>
      </div>

      {portfolio.description && (
        <p className="portfolio-description">{portfolio.description}</p>
      )}

      <div className="portfolio-stats">
        <div className="stat">
          <label>Total Value</label>
          <span className="value">{formatCurrency(portfolio.total_value)}</span>
        </div>

        <div className="stat">
          <label>P&L</label>
          <span className={`value ${portfolio.total_pnl >= 0 ? 'positive' : 'negative'}`}>
            {formatCurrency(portfolio.total_pnl)}
            <small> ({formatPercentage(portfolio.total_pnl_percentage)})</small>
          </span>
        </div>

        <div className="stat">
          <label>Cash Balance</label>
          <span className="value">{formatCurrency(portfolio.cash_balance)}</span>
        </div>

        <div className="stat">
          <label>Invested</label>
          <span className="value">{formatCurrency(portfolio.invested_value)}</span>
        </div>
      </div>

      <div className="portfolio-metrics">
        <div className="metric">
          <span>Win Rate:</span>
          <strong>{portfolio.win_rate.toFixed(1)}%</strong>
        </div>
        <div className="metric">
          <span>Total Trades:</span>
          <strong>{portfolio.total_trades}</strong>
        </div>
        <div className="metric">
          <span>Max Drawdown:</span>
          <strong>{portfolio.max_drawdown.toFixed(2)}%</strong>
        </div>
      </div>

      {tradingMode === 'live' && (
        <div className="live-warning">
          ⚠️ This is a live portfolio with real money
        </div>
      )}
    </div>
  );
};
```

---

## Migrazione Step-by-Step

### Step 1: Aggiornare le Interfacce TypeScript

1. Copia le definizioni dei tipi dalla sezione "TypeScript Types & Interfaces"
2. Crea il file `src/types/trading.types.ts`
3. Aggiungi il tipo `TradingMode` all'interfaccia `User`

```typescript
// Prima
interface User {
  id: number;
  email: string;
  // ...
}

// Dopo
interface User {
  id: number;
  email: string;
  trading_mode: 'paper' | 'live'; // AGGIUNTO
  // ...
}
```

### Step 2: Aggiornare il Componente di Login

1. Aggiungi il campo `trading_mode` al form di login
2. Implementa il toggle/radio button per scegliere la modalità
3. Passa il parametro `trading_mode` nella chiamata API di login

```typescript
// Modifica la funzione di login
const handleLogin = async () => {
  const response = await authService.login(email, password, tradingMode);
  // Salva anche il trading_mode oltre al token
  localStorage.setItem('trading_mode', response.trading_mode);
};
```

### Step 3: Modificare le Chiamate API

Sostituisci tutti i riferimenti a `/api/v1/paper-trading/` con `/api/v1/trading/`:

```typescript
// Prima
const url = '/api/v1/paper-trading/portfolio';

// Dopo
const url = '/api/v1/trading/portfolios';
```

### Step 4: Aggiungere Indicatori Visivi del Mode

1. Crea un componente `TradingModeBadge`
2. Mostralo nell'header/navbar
3. Usa colori diversi per paper (blu/verde) e live (rosso/arancio)

```typescript
<header>
  <Logo />
  <TradingModeBadge />
  <UserMenu />
</header>
```

### Step 5: Aggiornare lo State Management

1. Aggiungi `tradingMode` al tuo store globale
2. Sincronizza con `localStorage` e con i dati dell'utente
3. Passa il `tradingMode` ai componenti che ne hanno bisogno

### Step 6: Testare con Paper Mode

1. Effettua il login con `trading_mode: "paper"`
2. Crea un portfolio
3. Esegui operazioni di trading
4. Verifica che tutti i dati vengano salvati correttamente

### Step 7: Testare con Live Mode

1. Effettua logout
2. Login con `trading_mode: "live"`
3. Verifica che i portfolio paper NON siano visibili
4. Crea un portfolio live
5. Verifica la separazione completa dei dati

---

## UI/UX Recommendations

### Indicatori Visivi

#### 1. Trading Mode Badge

Mostra sempre in modo prominente il mode attivo:

```tsx
<div className={`mode-badge ${tradingMode}`}>
  {tradingMode === 'paper' ? (
    <>
      <span className="icon">📝</span>
      <span>PAPER MODE</span>
      <span className="subtitle">Safe simulation</span>
    </>
  ) : (
    <>
      <span className="icon">💰</span>
      <span>LIVE MODE</span>
      <span className="subtitle">Real money ⚠️</span>
    </>
  )}
</div>
```

#### 2. Color Scheme

**Paper Mode:**
- Primary: Blue (#3B82F6) o Green (#10B981)
- Background: Light blue tint
- Border: Blue accent

**Live Mode:**
- Primary: Red (#EF4444) o Orange (#F59E0B)
- Background: Light red/orange tint
- Border: Red accent
- Warning indicators

#### 3. Conferma per Live Mode

Prima di permettere il login in live mode, mostra un dialog di conferma:

```tsx
const confirmLiveMode = () => {
  return window.confirm(
    'You are about to enter LIVE TRADING mode.\n\n' +
    'This will use REAL MONEY.\n\n' +
    'Are you sure you want to continue?'
  );
};
```

#### 4. Disclaimer Persistente

In live mode, mostra un disclaimer fisso:

```tsx
{tradingMode === 'live' && (
  <div className="live-mode-disclaimer">
    <strong>⚠️ LIVE TRADING MODE</strong>
    <p>You are trading with real money. All transactions are final.</p>
  </div>
)}
```

### Esempi CSS

```css
/* Trading Mode Badge */
.mode-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 14px;
}

.mode-badge.paper {
  background: #DBEAFE;
  color: #1E40AF;
  border: 2px solid #3B82F6;
}

.mode-badge.live {
  background: #FEE2E2;
  color: #991B1B;
  border: 2px solid #EF4444;
}

/* Portfolio Card with Mode */
.portfolio-card.paper {
  border-left: 4px solid #3B82F6;
}

.portfolio-card.live {
  border-left: 4px solid #EF4444;
  background: linear-gradient(to right, #FEF2F2 0%, white 10%);
}

/* Live Warning */
.live-warning {
  background: #FEE2E2;
  color: #991B1B;
  padding: 12px;
  border-radius: 8px;
  margin-top: 16px;
  text-align: center;
  font-weight: 600;
}
```

---

## Error Handling

### Nuovi Errori Possibili

#### 1. Reauthentication Required

Quando l'utente prova a cambiare mode:

```typescript
try {
  await switchMode('live');
} catch (error) {
  if (error.message === 'REAUTHENTICATION_REQUIRED') {
    // Mostra dialog per reinserire la password
    showReauthDialog();
  }
}
```

#### 2. Trading Mode Mismatch

Se il token ha un mode diverso da quello richiesto:

```typescript
const handleApiError = (error: any) => {
  if (error.status === 403 && error.detail?.includes('trading mode')) {
    // L'utente ha provato ad accedere a dati di un mode diverso
    alert('Please logout and login with the correct trading mode');
    logout();
  }
};
```

#### 3. Insufficient Balance (Paper vs Live)

```typescript
try {
  await tradingService.buy(portfolioId, {
    symbol: 'BTCUSDT',
    quantity: 1,
  });
} catch (error) {
  if (error.message.includes('Insufficient funds')) {
    if (tradingMode === 'paper') {
      showError('Not enough virtual balance. Add more capital to your paper portfolio.');
    } else {
      showError('Insufficient real funds. Please deposit more money.');
    }
  }
}
```

### Error Handler Utility

```typescript
// utils/errorHandler.ts
export const handleTradingError = (error: any, tradingMode: TradingMode) => {
  // Network errors
  if (!navigator.onLine) {
    return 'No internet connection. Please check your network.';
  }

  // Authentication errors
  if (error.status === 401) {
    return 'Session expired. Please login again.';
  }

  // Permission errors
  if (error.status === 403) {
    return 'You do not have permission to perform this action.';
  }

  // Validation errors
  if (error.status === 400) {
    return error.detail || 'Invalid request. Please check your input.';
  }

  // Server errors
  if (error.status >= 500) {
    return 'Server error. Please try again later.';
  }

  // Generic error
  return error.message || 'An unexpected error occurred.';
};
```

---

## Testing Checklist

### Authentication

- [ ] Login con paper mode (default)
- [ ] Login con paper mode (esplicito)
- [ ] Login con live mode
- [ ] Verifica che il token includa `trading_mode`
- [ ] Verifica che `/api/v1/auth/me` restituisca `trading_mode`
- [ ] Logout corretto (rimozione token e mode)

### Portfolio Operations

- [ ] Creazione portfolio in paper mode
- [ ] Creazione portfolio in live mode
- [ ] Lista portfolio mostra solo quelli del mode corrente
- [ ] Dettagli portfolio in paper mode
- [ ] Dettagli portfolio in live mode

### Trading Operations

- [ ] Ordine BUY in paper mode
- [ ] Ordine SELL in paper mode
- [ ] Ordine BUY in live mode (quando implementato)
- [ ] Ordine SELL in live mode (quando implementato)
- [ ] Verifica che gli ordini paper non influenzino live

### Mode Switching

- [ ] Logout da paper mode
- [ ] Login a live mode
- [ ] Verifica che i portfolio paper non siano visibili
- [ ] Logout da live mode
- [ ] Login a paper mode
- [ ] Verifica che i portfolio live non siano visibili

### UI/UX

- [ ] Badge del mode visibile in header
- [ ] Colori corretti per paper mode
- [ ] Colori corretti per live mode
- [ ] Warning visibile in live mode
- [ ] Conferma richiesta per switch a live mode

### Data Separation

- [ ] Portfolio paper e live sono separati
- [ ] Posizioni paper e live sono separate
- [ ] Trade paper e live sono separati
- [ ] Balance paper e live sono separati
- [ ] Dati di mercato sono condivisi (market_data)

---

## FAQ

### Come cambio trading mode?

Per cambiare modalità devi:
1. Fare **logout** dall'applicazione
2. Fare **login** nuovamente selezionando il mode desiderato

Non è possibile cambiare mode senza logout perché questo garantisce la sicurezza e la separazione completa dei dati.

### I dati sono condivisi tra paper e live?

**No**, i dati sono completamente separati:
- Portfolio paper ≠ Portfolio live
- Posizioni paper ≠ Posizioni live
- Trade paper ≠ Trade live

**Eccezione:** I dati storici di mercato (prezzi, candele, volumi) sono condivisi tra entrambe le modalità.

### Posso avere portfolio in entrambi i mode?

Sì! Puoi creare portfolio in entrambe le modalità, ma:
- Quando sei loggato in paper mode, vedi solo i portfolio paper
- Quando sei loggato in live mode, vedi solo i portfolio live

Per accedere ai portfolio dell'altro mode, devi fare logout e login con il mode corrispondente.

### Cosa succede se faccio login senza specificare il mode?

Se non specifichi il `trading_mode` nel login, il sistema usa **paper mode** come default per sicurezza.

### Come faccio a sapere in che mode sono?

Ci sono diversi modi:
1. Guarda il badge del mode nell'header/navbar
2. Controlla il `localStorage`: `localStorage.getItem('trading_mode')`
3. Controlla il colore dell'interfaccia (blu/verde = paper, rosso/arancio = live)

### Posso passare da paper a live senza logout?

No, per cambiare mode devi necessariamente fare logout e login. Questo è un comportamento intenzionale per:
- Sicurezza: evitare cambi accidentali
- Separazione dei dati: garantire che non ci siano mix tra paper e live
- Consapevolezza: l'utente deve essere consapevole del mode in cui sta operando

### Il live mode è già attivo?

Attualmente il **live mode** usa temporaneamente il backend paper trading. Quando il live trading service sarà completamente implementato, le operazioni in live mode verranno automaticamente instradate al servizio live reale.

Puoi comunque testare l'interfaccia e il flusso di lavoro completo.

### Gli endpoint vecchi `/api/v1/paper-trading/` funzionano ancora?

Sì, sono ancora disponibili per retrocompatibilità, ma sono **deprecati**. È fortemente consigliato migrare ai nuovi endpoint `/api/v1/trading/` per beneficiare della nuova architettura.

### Come faccio il deploy delle modifiche?

1. Aggiorna tutte le interfacce TypeScript
2. Testa accuratamente in ambiente di sviluppo
3. Esegui il deploy del frontend
4. Il backend è già aggiornato e retrocompatibile
5. Monitora eventuali errori nei log

---

## Risorse Aggiuntive

### Link Utili

- Backend Architecture Doc: `TRADING_MODE_ARCHITECTURE.md`
- API Documentation: `http://localhost:8000/docs` (quando il backend è in esecuzione)
- OpenAPI Spec: `http://localhost:8000/openapi.json`

### Contatti

Per domande o supporto sull'integrazione, contatta il team backend.

---

**Documento creato il:** 2025-10-09  
**Versione Backend:** 0.1.0  
**Ultima modifica:** 2025-10-09

