# 🚀 Heroku Deployment Guide - Configurazione Economica

Guida completa per deployare Altar Trader Hub Backend su Heroku con costi minimi.

## 💰 Costo Totale: $5/mese

- **Web Dyno Eco**: $5/mese (va in sleep dopo 30min inattività, si risveglia istantaneamente)
- **PostgreSQL**: GRATUITO (database esterno: Neon, Supabase o ElephantSQL)
- **Redis**: GRATUITO (Upstash serverless Redis)
- **Background Tasks**: GRATUITO (Heroku Scheduler)

---

## 📋 Prerequisiti

1. Account Heroku gratuito: https://signup.heroku.com/
2. Heroku CLI installato: https://devcenter.heroku.com/articles/heroku-cli
3. Account GitHub (per deploy automatico)

---

## 🗄️ Step 1: Setup Database PostgreSQL Esterno

### Opzione A: Neon (Consigliato - Serverless)

1. Vai su https://neon.tech/
2. Crea account gratuito
3. Crea nuovo progetto
4. Copia la **Connection String** (formato: `postgresql://user:pass@host/db`)

**Free tier**: 3 GB storage, computazione serverless

### Opzione B: Supabase

1. Vai su https://supabase.com/
2. Crea account gratuito
3. Crea nuovo progetto
4. Vai su Settings → Database
5. Copia **Connection String** in modalità "Session"

**Free tier**: 500 MB storage, 2 GB bandwidth

### Opzione C: ElephantSQL

1. Vai su https://www.elephantsql.com/
2. Crea account gratuito
3. Crea istanza "Tiny Turtle" (gratuita)
4. Copia **URL** dalla dashboard

**Free tier**: 20 MB storage, 5 connessioni

---

## 🔴 Step 2: Setup Redis Esterno (Opzionale ma Consigliato)

### Upstash Redis (Serverless)

1. Vai su https://upstash.com/
2. Crea account gratuito
3. Crea database Redis
4. Seleziona regione (preferibilmente vicina a Heroku US/EU)
5. Copia **UPSTASH_REDIS_REST_URL** o **Redis URL**

**Free tier**: 10,000 comandi/giorno, 256MB storage

---

## 🚀 Step 3: Deploy su Heroku

### 3.1 Crea App Heroku

```bash
# Login a Heroku
heroku login

# Crea nuova app (sostituisci con nome univoco)
heroku create altar-trader-hub

# Oppure usa un nome specifico
heroku create your-app-name
```

### 3.2 Configura Variabili Ambiente

```bash
# Database PostgreSQL (usa l'URL da Step 1)
heroku config:set DATABASE_URL="postgresql://user:password@host:5432/database"

# Redis (usa l'URL da Step 2 - opzionale)
heroku config:set REDIS_URL="redis://default:password@host:port"

# Secret key (genera una chiave random sicura)
heroku config:set SECRET_KEY="$(openssl rand -hex 32)"

# Environment
heroku config:set ENVIRONMENT="production"
heroku config:set DEBUG="false"

# CORS (aggiungi il dominio del tuo frontend)
heroku config:set ALLOWED_ORIGINS="https://your-frontend.com,https://www.your-frontend.com"

# Exchange API Keys (opzionali - configurali quando necessario)
heroku config:set BINANCE_API_KEY="your-key"
heroku config:set BINANCE_SECRET_KEY="your-secret"
heroku config:set BINANCE_TESTNET="true"
```

### 3.3 Deploy da GitHub (Consigliato)

```bash
# Connetti il repository GitHub
heroku git:remote -a your-app-name

# Deploy
git push heroku main
```

Oppure configura **Automatic Deploys** dalla dashboard Heroku:

1. Vai su https://dashboard.heroku.com/apps/your-app-name/deploy/github
2. Connetti il tuo repository GitHub
3. Abilita "Automatic deploys" dal branch `main`
4. (Opzionale) Abilita "Wait for CI to pass before deploy"

### 3.4 Verifica Deploy

```bash
# Controlla i log
heroku logs --tail

# Apri l'app
heroku open

# Test API
curl https://your-app-name.herokuapp.com/health
```

---

## ⏰ Step 4: Setup Heroku Scheduler per Background Tasks

Heroku Scheduler è **gratuito** e permette di eseguire task periodici.

### 4.1 Installa Addon

```bash
heroku addons:create scheduler:standard
```

### 4.2 Configura Jobs

```bash
# Apri la dashboard dello scheduler
heroku addons:open scheduler
```

Nella dashboard, aggiungi questi job:

#### Job 1: Raccolta Dati Crypto (ogni 10 minuti)
- **Frequency**: Every 10 minutes
- **Command**: `python heroku_scheduler.py collect_crypto_data`

#### Job 2: Cleanup Dati Vecchi (giornaliero)
- **Frequency**: Daily at 3:00 AM UTC
- **Command**: `python heroku_scheduler.py cleanup_old_data`

#### Job 3: Esecuzione Strategie (ogni 10 minuti)
- **Frequency**: Every 10 minutes
- **Command**: `python heroku_scheduler.py execute_strategies`

#### Job 4: Health Check (ogni ora)
- **Frequency**: Every hour at :00
- **Command**: `python heroku_scheduler.py health_check`

#### Job 5: Aggiornamento Simboli Exchange (giornaliero)
- **Frequency**: Daily at 1:00 AM UTC
- **Command**: `python heroku_scheduler.py update_exchange_symbols`

---

## 🔧 Comandi Utili

### Gestione App

```bash
# Visualizza info app
heroku info

# Visualizza configurazione
heroku config

# Modifica variabile ambiente
heroku config:set VARIABLE_NAME="value"

# Rimuovi variabile
heroku config:unset VARIABLE_NAME
```

### Log e Debugging

```bash
# Log in tempo reale
heroku logs --tail

# Ultimi 200 log
heroku logs -n 200

# Log dell'app (non system)
heroku logs --source app

# Log con filtro
heroku logs --tail | grep ERROR
```

### Database

```bash
# Connessione al database
heroku pg:psql

# Info database
heroku pg:info

# Backup database
heroku pg:backups:capture

# Restore backup
heroku pg:backups:restore
```

### Dyno Management

```bash
# Scala dyno (cambia tipo)
heroku ps:scale web=1:eco

# Riavvia app
heroku restart

# Esegui comando one-off
heroku run python migrate.py

# Apri shell Python
heroku run python

# Bash shell
heroku run bash
```

### Migrazioni Database

```bash
# Esegui migrazioni
heroku run python migrate.py

# Oppure usa release command (già configurato nel Procfile)
# Le migrazioni vengono eseguite automaticamente ad ogni deploy
```

---

## 📊 Monitoring e Performance

### Metriche App

```bash
# Visualizza metriche
heroku metrics

# Dashboard web
heroku dashboard
```

### Evitare Sleep del Dyno Eco

Il dyno Eco va in sleep dopo 30 minuti di inattività. Opzioni:

1. **Accettare il sleep** (risveglio in ~10 secondi alla prima richiesta)
2. **Usare Uptime Robot** (gratuito): https://uptimerobot.com/
   - Crea monitor HTTP che pinga la tua app ogni 5 minuti
3. **Upgrade a Basic dyno** ($7/mese - sempre attivo)

---

## 🔒 Sicurezza

### Best Practices

```bash
# 1. Usa sempre HTTPS (Heroku lo fornisce gratuitamente)

# 2. Genera SECRET_KEY forte
heroku config:set SECRET_KEY="$(openssl rand -hex 32)"

# 3. Limita CORS
heroku config:set ALLOWED_ORIGINS="https://yourdomain.com"

# 4. Non esporre chiavi API nel codice
# Usa sempre variabili ambiente

# 5. Abilita 2FA su Heroku
# Account Settings → Enable Two-Factor Authentication
```

---

## 🐛 Troubleshooting

### App non si avvia

```bash
# 1. Controlla i log
heroku logs --tail

# 2. Verifica buildpack Python
heroku buildpacks

# 3. Verifica variabili ambiente
heroku config

# 4. Test locale
heroku local web
```

### Database connection error

```bash
# 1. Verifica DATABASE_URL
heroku config:get DATABASE_URL

# 2. Test connessione
heroku run python -c "from app.core.database import engine; engine.connect()"

# 3. Verifica che il formato sia corretto
# Heroku fornisce postgres:// ma SQLAlchemy vuole postgresql://
# Il codice fa già la conversione automatica
```

### Redis non raggiungibile

```bash
# 1. Verifica REDIS_URL
heroku config:get REDIS_URL

# 2. Test connessione
heroku run python -c "import redis; r=redis.from_url('your-redis-url'); r.ping()"

# 3. Redis è opzionale - l'app funziona anche senza
```

### Scheduler non esegue job

```bash
# 1. Verifica addon installato
heroku addons

# 2. Controlla log scheduler
heroku logs --source scheduler

# 3. Test manuale comando
heroku run python heroku_scheduler.py collect_crypto_data
```

### Memoria insufficiente (R14 error)

```bash
# 1. Riduci pool_size database in database.py
# pool_size=3 invece di 5

# 2. Ottimizza query database

# 3. Considera upgrade a dyno superiore
```

---

## 💡 Tips & Tricks

### 1. Environment Locale Identico

```bash
# Usa heroku local per testare in locale
heroku local web

# Crea .env locale con le stesse variabili
cp .env.example .env
# Modifica .env con credenziali di test
```

### 2. Review Apps per PR

Configura Review Apps per creare app temporanee per ogni Pull Request:

1. Dashboard → Deploy → Review Apps
2. Enable Review Apps
3. Configura auto-deploy da PR

### 3. CI/CD con GitHub Actions

Il workflow `.github/workflows/ci.yml` già presente esegue test automatici.
Heroku può attendere che i test passino prima del deploy.

### 4. Backup Automatici Database

Se usi PostgreSQL esterno:
- **Neon**: Backup automatici inclusi nel free tier
- **Supabase**: Backup giornalieri automatici
- **ElephantSQL**: Backup manuali

### 5. Monitoring Errori

Aggiungi Sentry (free tier disponibile):

```bash
# Installa Sentry
pip install sentry-sdk

# Configura
heroku config:set SENTRY_DSN="your-sentry-dsn"
```

---

## 🎯 Prossimi Passi Dopo il Deploy

1. ✅ Testa tutti gli endpoint API: `https://your-app.herokuapp.com/docs`
2. ✅ Configura Heroku Scheduler per i background tasks
3. ✅ Setup monitoring con Uptime Robot
4. ✅ Configura domain custom (opzionale)
5. ✅ Abilita SSL (già incluso gratuitamente)
6. ✅ Setup Sentry per error tracking (opzionale)
7. ✅ Configura backup automatici database

---

## 📚 Risorse Utili

- [Heroku Python Documentation](https://devcenter.heroku.com/categories/python-support)
- [Heroku Scheduler](https://devcenter.heroku.com/articles/scheduler)
- [Neon PostgreSQL](https://neon.tech/docs/introduction)
- [Upstash Redis](https://docs.upstash.com/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/docker/)

---

## 🆘 Supporto

Se incontri problemi:

1. Controlla i log: `heroku logs --tail`
2. Verifica configurazione: `heroku config`
3. Test manuale: `heroku run bash`
4. Consulta la documentazione Heroku
5. Apri issue su GitHub

---

**✨ Deployment completato! La tua app è live su Heroku con costi minimi!** 🎉

