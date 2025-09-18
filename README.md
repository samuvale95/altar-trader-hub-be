# Altar Trader Hub Backend

Un backend completo per un trading bot crypto costruito con FastAPI, SQLite e Redis.

## 🚀 Caratteristiche

- **API REST** completa con FastAPI
- **Autenticazione JWT** con refresh token
- **Database SQLite** per sviluppo locale (PostgreSQL per produzione)
- **Redis** per cache e sessioni
- **WebSocket** per aggiornamenti real-time
- **Celery** per task asincroni
- **Docker** e **Kubernetes** per deployment
- **Monitoring** con Prometheus e Grafana

## 📋 Prerequisiti

- Python 3.11+
- Redis (per cache e Celery)
- Docker (opzionale)

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