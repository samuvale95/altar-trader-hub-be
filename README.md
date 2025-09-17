# Altar Trader Hub Backend

Backend completo per il trading bot crypto con architettura modulare scalabile, costruito con FastAPI, PostgreSQL, Redis e Celery.

## 🚀 Caratteristiche

- **API REST completa** per gestione portfolio, strategie, ordini e market data
- **WebSocket real-time** per aggiornamenti istantanei
- **Supporto multi-exchange** (Binance, Kraken, KuCoin)
- **Engine di strategie** con backtesting e paper trading
- **Indicatori tecnici** avanzati (RSI, MACD, Bollinger Bands, etc.)
- **Sistema di notifiche** (Email, Telegram, Push)
- **Task asincroni** con Celery
- **Monitoring completo** con Prometheus e Grafana
- **Docker ready** per deployment facile

## 🏗️ Architettura

```
[Frontend React] <--REST/WebSocket--> [API Gateway/Sicurezza]
                                                    |
                                        [Backend Core Server]
                                                    |
  +-------------------+----------------------+--------------------------+
  |                   |                      |                          |
[Data Feeder]    [Strategy Engine]   [Order Manager]           [Notification Service]
 |                   |                      |                          |
[DB Market Data] [Log/Stats DB]   [Exchange API Adapter]         [Email/Push/Telegram]
                                   (Binance, Kraken, KuCoin...)
```

## 🛠️ Stack Tecnologico

- **Framework**: FastAPI + Uvicorn
- **Database**: PostgreSQL + Redis
- **Task Queue**: Celery + Redis
- **ORM**: SQLAlchemy + Alembic
- **Autenticazione**: JWT + OAuth2
- **WebSocket**: FastAPI WebSocket
- **Monitoring**: Prometheus + Grafana
- **Container**: Docker + Docker Compose

## 📁 Struttura Progetto

```
trading-backend/
├── app/
│   ├── core/                 # Configurazione e utilities core
│   ├── api/v1/              # Endpoints API
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── tasks/               # Celery tasks
│   └── utils/               # Utilities
├── tests/                   # Test suite
├── docker/                  # Configurazione Docker
├── migrations/              # Database migrations
└── requirements.txt         # Dependencies
```

## 🚀 Quick Start

### Prerequisiti

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Installazione

1. **Clona il repository**
```bash
git clone https://github.com/your-org/altar-trader-hub-be.git
cd altar-trader-hub-be
```

2. **Configura l'ambiente**
```bash
cp env.example .env
# Modifica .env con le tue configurazioni
```

3. **Avvia con Docker Compose**
```bash
# Development
docker-compose -f docker/docker-compose.yml up -d

# Production
docker-compose -f docker/docker-compose.prod.yml up -d
```

4. **Esegui le migrazioni**
```bash
docker-compose exec api alembic upgrade head
```

5. **Verifica l'installazione**
```bash
curl http://localhost:8000/health
```

### Installazione Locale

1. **Crea virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

2. **Installa dependencies**
```bash
pip install -r requirements.txt
```

3. **Configura database**
```bash
# Crea database PostgreSQL
createdb trading_bot

# Esegui migrazioni
alembic upgrade head
```

4. **Avvia l'applicazione**
```bash
# API Server
uvicorn app.main:app --reload

# Celery Worker
celery -A app.tasks.celery_app worker --loglevel=info

# Celery Beat
celery -A app.tasks.celery_app beat --loglevel=info
```

## 📚 API Documentation

Una volta avviata l'applicazione, la documentazione API è disponibile su:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints Principali

#### Autenticazione
- `POST /api/v1/auth/register` - Registrazione utente
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Info utente corrente

#### Portfolio
- `GET /api/v1/portfolio/overview` - Overview portfolio
- `GET /api/v1/portfolio/portfolios` - Lista portfolio
- `POST /api/v1/portfolio/portfolios` - Crea portfolio
- `GET /api/v1/portfolio/positions` - Posizioni attive
- `GET /api/v1/portfolio/balances` - Balance per exchange

#### Strategie
- `GET /api/v1/strategies/` - Lista strategie
- `POST /api/v1/strategies/` - Crea strategia
- `POST /api/v1/strategies/{id}/start` - Avvia strategia
- `POST /api/v1/strategies/{id}/stop` - Ferma strategia
- `GET /api/v1/strategies/{id}/performance` - Performance metrics

#### Ordini
- `GET /api/v1/orders/` - Lista ordini
- `POST /api/v1/orders/` - Crea ordine
- `DELETE /api/v1/orders/{id}` - Cancella ordine
- `GET /api/v1/orders/trades/` - Storia trades

#### Market Data
- `GET /api/v1/market-data/symbols` - Lista simboli
- `GET /api/v1/market-data/ohlcv` - OHLCV data
- `GET /api/v1/market-data/ticker` - Ticker real-time
- `GET /api/v1/market-data/indicators` - Indicatori tecnici

#### WebSocket
- `WS /ws/portfolio` - Portfolio updates
- `WS /ws/orders` - Order updates
- `WS /ws/market-data` - Market data stream
- `WS /ws/notifications` - Notifications

## 🔧 Configurazione

### Variabili d'Ambiente

Copia `env.example` in `.env` e configura:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/trading_bot
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Exchange APIs
BINANCE_API_KEY=your-binance-key
BINANCE_SECRET_KEY=your-binance-secret
KRAKEN_API_KEY=your-kraken-key
KRAKEN_SECRET_KEY=your-kraken-secret

# Notifications
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your-email
SMTP_PASSWORD=your-password
TELEGRAM_BOT_TOKEN=your-telegram-token
```

### Exchange Configuration

Il sistema supporta multiple exchange:

- **Binance**: API Key + Secret Key
- **Kraken**: API Key + Secret Key
- **KuCoin**: API Key + Secret Key + Passphrase

Configura le tue API keys nel database tramite l'endpoint `/api/v1/auth/api-keys`.

## 🧪 Testing

```bash
# Esegui tutti i test
pytest

# Test con coverage
pytest --cov=app --cov-report=html

# Test specifici
pytest tests/test_api/test_auth.py
```

## 📊 Monitoring

### Prometheus
- **URL**: http://localhost:9090
- **Metrics**: Performance, errori, latenza

### Grafana
- **URL**: http://localhost:3000
- **Login**: admin/admin
- **Dashboards**: Trading metrics, system health

### Flower (Celery)
- **URL**: http://localhost:5555
- **Monitor**: Task queue, worker status

## 🚀 Deployment

### Docker Production

```bash
# Build e deploy
docker-compose -f docker/docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker/docker-compose.prod.yml up -d --scale celery-worker=3
```

### Kubernetes

```bash
# Applica configurazioni
kubectl apply -f k8s/

# Verifica deployment
kubectl get pods
kubectl get services
```

## 🔒 Sicurezza

- **JWT Authentication** con refresh tokens
- **Rate limiting** per prevenire abuse
- **Input validation** con Pydantic
- **SQL injection prevention** con SQLAlchemy
- **CORS configuration** per frontend
- **Audit logging** completo

## 📈 Performance

- **Response time**: < 200ms per API calls
- **WebSocket latency**: < 50ms
- **Concurrent users**: 1000+
- **Data processing**: Real-time
- **Uptime target**: 99.9%

## 🤝 Contribuire

1. Fork del repository
2. Crea feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing-feature`)
5. Apri Pull Request

## 📝 Licenza

Questo progetto è licenziato sotto la MIT License - vedi il file [LICENSE](LICENSE) per dettagli.

## 🆘 Supporto

- **Documentation**: [Wiki](https://github.com/your-org/altar-trader-hub-be/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-org/altar-trader-hub-be/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/altar-trader-hub-be/discussions)

## 🗺️ Roadmap

- [ ] Supporto per più exchange
- [ ] Machine Learning strategies
- [ ] Advanced risk management
- [ ] Mobile app API
- [ ] Social trading features
- [ ] Advanced backtesting
- [ ] Paper trading improvements
- [ ] Real-time alerts system

---

**Altar Trader Hub** - Il futuro del trading crypto automatizzato 🚀
