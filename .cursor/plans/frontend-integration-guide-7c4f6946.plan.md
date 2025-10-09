<!-- 7c4f6946-8649-4303-a44b-163f1a2b493f ea03b84a-ea1f-4016-bc4c-0245ca08ac9a -->
# Frontend Integration Guide - Trading Mode Architecture

## Contenuti del Documento

### 1. Executive Summary

- Panoramica dei cambiamenti architetturali
- Impatto sul frontend
- Vantaggi per l'esperienza utente

### 2. Breaking Changes

- Trading mode ora è a livello utente (non portfolio)
- Nuovi endpoint API unificati `/api/v1/trading/`
- Parametro `trading_mode` richiesto al login
- Response del login include `trading_mode`

### 3. Autenticazione Aggiornata

**Login Request Schema:**

```typescript
interface LoginRequest {
  email: string;
  password: string;
  trading_mode?: 'paper' | 'live'; // Default: 'paper'
}
```

**Login Response Schema:**

```typescript
interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  trading_mode: 'paper' | 'live'; // NUOVO CAMPO
}
```

**User Response Schema:**

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

### 4. Nuovi Endpoint API

Mappatura completa degli endpoint:

**VECCHI (deprecati):**

- `/api/v1/paper-trading/portfolio` → **USARE** `/api/v1/trading/portfolios`
- `/api/v1/paper-trading/portfolio/{id}` → **USARE** `/api/v1/trading/portfolios/{id}`
- etc.

**NUOVI (consigliati):**

- `POST /api/v1/trading/portfolios`
- `GET /api/v1/trading/portfolios`
- `GET /api/v1/trading/portfolios/{id}`
- `POST /api/v1/trading/portfolios/{id}/buy`
- `POST /api/v1/trading/portfolios/{id}/sell`
- `GET /api/v1/trading/portfolios/{id}/positions`
- `GET /api/v1/trading/portfolios/{id}/trades`
- `GET /api/v1/trading/portfolios/{id}/balance`
- `POST /api/v1/trading/portfolios/{id}/positions/{position_id}/close`
- `PUT /api/v1/trading/portfolios/{id}/positions/{position_id}/stop-loss`
- `PUT /api/v1/trading/portfolios/{id}/positions/{position_id}/take-profit`
- `POST /api/v1/trading/portfolios/{id}/update-value`

### 5. TypeScript Types & Interfaces

Definizioni complete per tutti i tipi necessari basati sugli schema Pydantic del backend.

### 6. State Management

Esempi di gestione dello stato (React Context / Redux / Zustand):

```typescript
interface AppState {
  user: User | null;
  tradingMode: 'paper' | 'live';
  portfolios: Portfolio[];
  // ...
}
```

### 7. Esempi di Codice React

**Login Component:**

- Form con selezione trading mode
- Gestione del toggle paper/live
- Salvataggio del mode in local storage

**API Service:**

- Funzioni per chiamare i nuovi endpoint
- Gestione automatica del token
- Error handling

**Portfolio Component:**

- Visualizzazione del mode attivo
- Badge "PAPER MODE" / "LIVE MODE"
- Warning per live mode

### 8. Migrazione Step-by-Step

1. Aggiornare le interfacce TypeScript
2. Aggiornare il componente di login
3. Modificare le chiamate API
4. Aggiungere indicatori visivi del mode
5. Testare con paper mode
6. Testare con live mode

### 9. UI/UX Recommendations

- Mostrare chiaramente il mode attivo (badge, banner)
- Conferma obbligatoria prima di passare a live mode
- Colori diversi per paper (verde/blu) e live (rosso/arancio)
- Disclaimer per live mode

### 10. Error Handling

Nuovi possibili errori e come gestirli.

### 11. Testing Checklist

- [ ] Login con paper mode
- [ ] Login con live mode
- [ ] Creazione portfolio in entrambi i mode
- [ ] Switch tra mode (logout/login)
- [ ] Operazioni di trading in paper mode
- [ ] Verifica separazione dati

### 12. FAQ

- Come cambio mode?
- I dati sono condivisi tra paper e live?
- Posso avere portfolio in entrambi i mode?
- etc.

## File da Creare

`FRONTEND_INTEGRATION_GUIDE.md` - Documento completo markdown con tutti i dettagli sopra, esempi di codice funzionanti, e riferimenti alle API.