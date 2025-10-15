# Altar Trader Hub Backend

Un backend completo per un trading bot crypto costruito con FastAPI e PostgreSQL.

## 🚀 Caratteristiche

- **API REST** completa con FastAPI
- **Autenticazione JWT** con refresh token
- **Database PostgreSQL** (SQLite per sviluppo locale)
- **Redis** opzionale per cache
- **WebSocket** per aggiornamenti real-time
- **Heroku Scheduler** per task periodici
- **Deploy facile su Heroku** con costi minimi ($5/mese)
- **Multi-exchange support** (Binance, Kraken, KuCoin)
- **Paper Trading** per test strategie senza rischi

## 📋 Prerequisiti

### Sviluppo Locale
- Python 3.11+
- Redis (opzionale, per cache)
- PostgreSQL (opzionale, può usare SQLite)

### Produzione (Heroku)
- Account Heroku (gratuito)
- Database PostgreSQL esterno (Neon/Supabase - gratuito)
- Redis esterno opzionale (Upstash - gratuito)

## 🛠️ Installazione

1. **Clona il repository:**
   ```bash
   git clone <repository-url>
   cd altar-trader-hub-be
   ```

2. **Crea un ambiente virtuale:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Su Windows: venv\Scripts\activate
   ```

3. **Installa le dipendenze:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configura le variabili d'ambiente:**
   ```bash
   cp .env.example .env
   # Modifica .env con le tue configurazioni
   ```

5. **Avvia Redis:**
   ```bash
   # Su macOS con Homebrew:
   brew services start redis
   
   # Su Ubuntu/Debian:
   sudo systemctl start redis
   
   # Con Docker:
   docker run -d -p 6379:6379 redis:alpine
   ```

## 🚀 Avvio dell'applicazione

1. **Avvia l'applicazione:**
   ```bash
   python run.py
   ```

2. **L'applicazione sarà disponibile su:**
   - API: http://localhost:8000
   - Health check: http://localhost:8000/health
   - Documentazione: http://localhost:8000/docs

## 🧪 Test

Esegui i test per verificare che tutto funzioni:

```bash
python test_api.py
```

## 📚 API Endpoints

### Autenticazione
- `POST /api/v1/auth/register` - Registrazione utente
- `POST /api/v1/auth/login` - Login utente
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Profilo utente corrente

### Portfolio
- `GET /api/v1/portfolio/` - Lista portfolio
- `POST /api/v1/portfolio/` - Crea portfolio
- `GET /api/v1/portfolio/{id}` - Dettagli portfolio
- `PUT /api/v1/portfolio/{id}` - Aggiorna portfolio
- `DELETE /api/v1/portfolio/{id}` - Elimina portfolio

### Strategie
- `GET /api/v1/strategies/` - Lista strategie
- `POST /api/v1/strategies/` - Crea strategia
- `GET /api/v1/strategies/{id}` - Dettagli strategia
- `PUT /api/v1/strategies/{id}` - Aggiorna strategia
- `DELETE /api/v1/strategies/{id}` - Elimina strategia
- `POST /api/v1/strategies/{id}/start` - Avvia strategia
- `POST /api/v1/strategies/{id}/stop` - Ferma strategia

### Ordini
- `GET /api/v1/orders/` - Lista ordini
- `POST /api/v1/orders/` - Crea ordine
- `GET /api/v1/orders/{id}` - Dettagli ordine
- `PUT /api/v1/orders/{id}` - Aggiorna ordine
- `DELETE /api/v1/orders/{id}` - Cancella ordine

### Market Data
- `GET /api/v1/market-data/symbols` - Lista simboli
- `GET /api/v1/market-data/ohlcv` - Dati OHLCV
- `GET /api/v1/market-data/ticker` - Ticker
- `GET /api/v1/market-data/indicators` - Indicatori tecnici

### Notifiche
- `GET /api/v1/notifications/` - Lista notifiche
- `POST /api/v1/notifications/` - Crea notifica
- `PUT /api/v1/notifications/{id}` - Aggiorna notifica

### WebSocket
- `WS /ws` - Connessione WebSocket per aggiornamenti real-time

## 🐳 Docker

### Sviluppo
```bash
docker-compose -f docker/docker-compose.yml up
```

### Produzione
```bash
docker-compose -f docker/docker-compose.prod.yml up
```

## ☸️ Kubernetes

### Deploy con Helm
```bash
helm install altar-trader-hub ./helm/altar-trader-hub
```

### Deploy con kubectl
```bash
kubectl apply -f k8s/
```

## 🔧 Configurazione

### Variabili d'ambiente principali

```bash
# Database
DATABASE_URL=sqlite:///./trading_bot.db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys (opzionale)
BINANCE_API_KEY=your-binance-api-key
BINANCE_SECRET_KEY=your-binance-secret-key
```

## 📊 Monitoring

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

## 🧪 Testing

```bash
# Test unitari
pytest

# Test con coverage
pytest --cov=app

# Linting
flake8 app/
black app/
isort app/
```

## 📝 Sviluppo

### Struttura del progetto

```
app/
├── api/           # Endpoint API
├── core/          # Configurazione core
├── models/        # Modelli database
├── schemas/       # Schemi Pydantic
├── services/      # Servizi business
├── tasks/         # Task Celery
└── utils/         # Utilità
```

### Aggiungere un nuovo endpoint

1. Crea il modello in `app/models/`
2. Crea lo schema in `app/schemas/`
3. Crea l'endpoint in `app/api/v1/`
4. Aggiungi il router in `app/main.py`

## 🚀 Deployment

### Deploy su Heroku (Consigliato)

Il modo più semplice ed economico per deployare l'applicazione.

**Costo: $5/mese** (Web Dyno Eco + database esterno gratuito)

1. **Setup Rapido:**
   ```bash
   # Crea app Heroku
   heroku create your-app-name
   
   # Configura database PostgreSQL esterno (Neon/Supabase)
   heroku config:set DATABASE_URL="postgresql://user:pass@host/db"
   
   # Genera secret key
   heroku config:set SECRET_KEY="$(openssl rand -hex 32)"
   
   # Deploy
   git push heroku main
   ```

2. **Setup Heroku Scheduler** (gratuito):
   ```bash
   heroku addons:create scheduler:standard
   heroku addons:open scheduler
   ```
   
   Aggiungi questi job:
   - `python heroku_scheduler.py collect_crypto_data` (ogni 10 min)
   - `python heroku_scheduler.py cleanup_old_data` (giornaliero)
   - `python heroku_scheduler.py execute_strategies` (ogni 10 min)

3. **Documentazione Completa:**
   
   Consulta [HEROKU_DEPLOYMENT.md](HEROKU_DEPLOYMENT.md) per:
   - Setup database PostgreSQL gratuito (Neon/Supabase)
   - Setup Redis gratuito (Upstash)
   - Configurazione variabili ambiente
   - Troubleshooting
   - Tips & tricks

### Sviluppo Locale

```bash
# Installa Heroku CLI
brew install heroku/brew/heroku

# Test locale con Procfile
heroku local web
```

## 🤝 Contribuire

1. Fork del repository
2. Crea un branch per la feature (`git checkout -b feature/amazing-feature`)
3. Commit delle modifiche (`git commit -m 'Add amazing feature'`)
4. Push al branch (`git push origin feature/amazing-feature`)
5. Apri una Pull Request

## 📄 Licenza

Questo progetto è sotto licenza MIT. Vedi il file `LICENSE` per i dettagli.

## 🆘 Supporto

Per supporto o domande, apri una issue su GitHub.