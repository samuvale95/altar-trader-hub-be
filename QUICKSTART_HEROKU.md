# 🚀 Quick Start - Heroku Deployment

Guida rapida per deployare su Heroku in 5 minuti.

## ⚡ Setup Ultra-Rapido

### 1. Database PostgreSQL Gratuito (Neon)

1. Vai su https://neon.tech/
2. Signup gratuito
3. Crea progetto → Copia **Connection String**
4. Esempio: `postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb`

### 2. Redis Gratuito (Upstash) - Opzionale

1. Vai su https://upstash.com/
2. Signup gratuito  
3. Crea database Redis → Copia **Redis URL**
4. Esempio: `redis://default:xxx@us1-xxx.upstash.io:6379`

### 3. Deploy su Heroku

```bash
# 1. Login Heroku
heroku login

# 2. Crea app
heroku create your-app-name

# 3. Configura database
heroku config:set DATABASE_URL="YOUR_NEON_URL"

# 4. Configura Redis (opzionale)
heroku config:set REDIS_URL="YOUR_UPSTASH_URL"

# 5. Genera secret key sicura
heroku config:set SECRET_KEY="$(openssl rand -hex 32)"

# 6. Ambiente produzione
heroku config:set ENVIRONMENT="production"
heroku config:set DEBUG="false"

# 7. CORS (modifica con il tuo dominio frontend)
heroku config:set ALLOWED_ORIGINS="*"

# 8. Deploy!
git push heroku main

# 9. Apri app
heroku open
```

### 4. Verifica Deployment

```bash
# Controlla log
heroku logs --tail

# Test API
curl https://your-app-name.herokuapp.com/health

# Apri documentazione
open https://your-app-name.herokuapp.com/docs
```

### 5. Setup Background Tasks (Heroku Scheduler)

```bash
# Installa addon (gratuito)
heroku addons:create scheduler:standard

# Apri dashboard scheduler
heroku addons:open scheduler
```

**Aggiungi questi job nella dashboard:**

| Frequenza | Comando |
|-----------|---------|
| Every 10 minutes | `python heroku_scheduler.py collect_crypto_data` |
| Daily at 3:00 AM | `python heroku_scheduler.py cleanup_old_data` |
| Every 10 minutes | `python heroku_scheduler.py execute_strategies` |
| Every hour | `python heroku_scheduler.py health_check` |

---

## ✅ Completato!

La tua app è live su:
- **API**: `https://your-app-name.herokuapp.com`
- **Docs**: `https://your-app-name.herokuapp.com/docs`

**Costo totale**: $5/mese (solo Web Dyno Eco)

---

## 🧪 Test Locale Prima del Deploy

```bash
# 1. Crea .env con le tue credenziali
cp env.example .env

# 2. Modifica .env
nano .env

# 3. Installa dipendenze
pip install -r requirements.txt

# 4. Test con Heroku Local
heroku local web

# 5. Apri browser
open http://localhost:5000
```

---

## 🔧 Configurazione Opzionale

### Exchange API Keys (quando necessario)

```bash
# Binance
heroku config:set BINANCE_API_KEY="your-key"
heroku config:set BINANCE_SECRET_KEY="your-secret"
heroku config:set BINANCE_TESTNET="true"

# Kraken
heroku config:set KRAKEN_API_KEY="your-key"
heroku config:set KRAKEN_SECRET_KEY="your-secret"

# KuCoin
heroku config:set KUCOIN_API_KEY="your-key"
heroku config:set KUCOIN_SECRET_KEY="your-secret"
heroku config:set KUCOIN_PASSPHRASE="your-passphrase"
```

### Notifiche Email/Telegram

```bash
# Email (SMTP)
heroku config:set SMTP_HOST="smtp.gmail.com"
heroku config:set SMTP_PORT="587"
heroku config:set SMTP_USERNAME="your-email@gmail.com"
heroku config:set SMTP_PASSWORD="your-app-password"

# Telegram
heroku config:set TELEGRAM_BOT_TOKEN="your-bot-token"
heroku config:set TELEGRAM_CHAT_ID="your-chat-id"
```

---

## 🎯 Next Steps

1. ✅ Configura custom domain (opzionale)
2. ✅ Setup monitoring con Uptime Robot
3. ✅ Configura backup database automatici
4. ✅ Testa tutti gli endpoint API
5. ✅ Configura strategie trading

---

## 📚 Documentazione Completa

Per informazioni dettagliate, vedi:
- [HEROKU_DEPLOYMENT.md](HEROKU_DEPLOYMENT.md) - Guida completa
- [README.md](README.md) - Documentazione generale

---

## 🆘 Problemi?

### App non si avvia

```bash
# Controlla log
heroku logs --tail

# Verifica variabili
heroku config

# Riavvia app
heroku restart
```

### Database connection error

```bash
# Verifica DATABASE_URL
heroku config:get DATABASE_URL

# Test connessione
heroku run python -c "from app.core.database import engine; print('OK')"
```

### Redis non funziona

Redis è opzionale - l'app funziona anche senza.
Se vuoi usarlo, verifica:

```bash
heroku config:get REDIS_URL
```

---

**🎉 Pronto! Buon trading!**

