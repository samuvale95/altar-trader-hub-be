# 📁 Scripts di Deployment

Questa directory contiene gli script per configurare e gestire il deployment automatico di Altar Trader Hub.

## 🚀 Quick Start

Per configurare tutto in un solo comando:

```bash
cd /home/samuelevalente/altar-trader-hub-be
bash scripts/quick_setup.sh
```

Questo script eseguirà automaticamente tutti i passaggi necessari.

## 📋 Script Disponibili

### `quick_setup.sh` - Setup Completo Automatico
Esegue tutti i passaggi necessari per configurare il deployment:
- Verifica prerequisiti
- Crea ambiente virtuale
- Installa dipendenze
- Configura file .env
- Configura servizio systemd
- Configura permessi per GitHub runner

**Utilizzo:**
```bash
bash scripts/quick_setup.sh
```

### `setup_systemd.sh` - Configura Servizio Systemd
Installa e configura il servizio systemd per l'avvio automatico.

**Utilizzo:**
```bash
sudo bash scripts/setup_systemd.sh
```

### `configure_runner.sh` - Configura Permessi Runner
Configura i permessi sudo per permettere al GitHub runner di gestire il servizio.

**Utilizzo:**
```bash
sudo bash scripts/configure_runner.sh
```

### `restart_service.sh` - Riavvio Manuale
Riavvia il servizio manualmente senza usare systemd.

**Utilizzo:**
```bash
bash scripts/restart_service.sh
```

### `altar-trader-hub.service` - File Systemd
File di configurazione per il servizio systemd. Non eseguire direttamente.

## 🔄 Workflow GitHub Actions

Il deployment automatico è gestito da `.github/workflows/deploy.yml`.

### Come Funziona

1. **Trigger**: Push su branch `main`
2. **Runner**: Self-hosted (sul tuo Raspberry Pi)
3. **Passi**:
   - Checkout codice
   - Sincronizzazione in `/home/samuelevalente/altar-trader-hub-be`
   - Installazione/aggiornamento dipendenze
   - Esecuzione migrazioni database
   - Riavvio servizio con systemd
   - Verifica stato servizio

### File Esclusi dalla Sincronizzazione

- `venv/` - ambiente virtuale
- `__pycache__/` - cache Python
- `.git/` - directory Git
- `trading_bot.db` - database esistente
- `.env` - configurazione locale

## 📊 Gestione del Servizio

### Comandi Systemd

```bash
# Avvia il servizio
sudo systemctl start altar-trader-hub

# Ferma il servizio
sudo systemctl stop altar-trader-hub

# Riavvia il servizio
sudo systemctl restart altar-trader-hub

# Stato del servizio
sudo systemctl status altar-trader-hub

# Abilita avvio automatico
sudo systemctl enable altar-trader-hub

# Disabilita avvio automatico
sudo systemctl disable altar-trader-hub
```

### Log

```bash
# Log in tempo reale
sudo journalctl -u altar-trader-hub -f

# Ultime 100 righe
sudo journalctl -u altar-trader-hub -n 100

# Log dall'ultima ora
sudo journalctl -u altar-trader-hub --since "1 hour ago"

# Log di oggi
sudo journalctl -u altar-trader-hub --since today
```

### Verifica Funzionamento

```bash
# Health check
curl http://localhost:8001/health

# Documentazione API
curl http://localhost:8001/docs

# Verifica processo
ps aux | grep uvicorn

# Verifica porta in ascolto
sudo netstat -tlnp | grep 8001
```

## 🐛 Troubleshooting

### Il servizio non parte

```bash
# Controlla i log
sudo journalctl -u altar-trader-hub -n 50

# Verifica la configurazione
sudo systemctl cat altar-trader-hub

# Testa manualmente
cd /home/samuelevalente/altar-trader-hub-be
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Errori di permessi

```bash
# Ri-configura i permessi
sudo bash scripts/configure_runner.sh

# Verifica i permessi sudo
sudo cat /etc/sudoers.d/github-runner
```

### Database non raggiungibile

```bash
# Verifica PostgreSQL
sudo systemctl status postgresql

# Verifica Redis
sudo systemctl status redis
redis-cli ping

# Controlla il file .env
cat /home/samuelevalente/altar-trader-hub-be/.env
```

### Il deployment GitHub fallisce

1. Controlla che il runner sia attivo:
   ```bash
   cd ~/actions-runner
   sudo ./svc.sh status
   ```

2. Verifica i log del workflow su GitHub

3. Verifica i permessi della directory:
   ```bash
   ls -la /home/samuelevalente/altar-trader-hub-be
   ```

## 🔐 Sicurezza

- Il servizio gira con l'utente `samuelevalente` (non root)
- I permessi sudo sono limitati solo ai comandi necessari
- Il file `.env` non viene mai committato su Git
- Le variabili sensibili sono isolate nel servizio

## 📚 Documentazione Completa

Per la guida completa al deployment, consulta:
- `DEPLOYMENT_SETUP.md` - Guida dettagliata al deployment

## 🆘 Supporto

Se riscontri problemi:

1. Controlla i log: `sudo journalctl -u altar-trader-hub -f`
2. Verifica lo stato: `sudo systemctl status altar-trader-hub`
3. Testa manualmente: `bash scripts/restart_service.sh`
4. Consulta la documentazione completa

---

**✨ Configurato una volta, funziona per sempre!**

