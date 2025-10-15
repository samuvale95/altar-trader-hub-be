# 🚀 Guida al Deployment Automatico - Altar Trader Hub

Questa guida spiega come configurare il deployment automatico del progetto Altar Trader Hub Backend usando GitHub Actions e un self-hosted runner.

## 📋 Prerequisiti

- Raspberry Pi (o server Linux) con:
  - Ubuntu/Debian/Raspbian OS
  - Python 3.11+
  - Git installato
  - PostgreSQL e Redis installati e configurati
  - GitHub Actions self-hosted runner configurato

## 🔧 Setup Iniziale (Esegui una volta sola)

### 1. Configura la directory di destinazione

Sul tuo Raspberry Pi, crea la directory di destinazione se non esiste:

```bash
mkdir -p /home/samuelevalente/altar-trader-hub-be
cd /home/samuelevalente/altar-trader-hub-be
```

### 2. Clona il repository manualmente (prima volta)

```bash
git clone https://github.com/TUO_USERNAME/altar-trader-hub-be.git /home/samuelevalente/altar-trader-hub-be
cd /home/samuelevalente/altar-trader-hub-be
```

### 3. Crea il file .env

Crea un file `.env` nella directory principale con le tue configurazioni:

```bash
nano /home/samuelevalente/altar-trader-hub-be/.env
```

Contenuto esempio:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/trading_bot
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
DEBUG=false
```

### 4. Configura il servizio systemd

Esegui lo script di configurazione systemd (richiede sudo):

```bash
cd /home/samuelevalente/altar-trader-hub-be
chmod +x scripts/*.sh
sudo bash scripts/setup_systemd.sh
```

Questo script:
- ✅ Installa il servizio systemd
- ✅ Abilita l'avvio automatico al boot
- ✅ Avvia il servizio

### 5. Configura i permessi per il runner GitHub

Per permettere al runner di riavviare il servizio senza chiedere la password:

```bash
sudo bash scripts/configure_runner.sh
```

### 6. Verifica che tutto funzioni

Controlla lo stato del servizio:

```bash
sudo systemctl status altar-trader-hub.service
```

Visualizza i log:

```bash
sudo journalctl -u altar-trader-hub -f
```

Testa l'API:

```bash
curl http://localhost:8001/health
```

## 🤖 GitHub Actions Runner

### Configurazione del Self-Hosted Runner

Se non hai ancora configurato il runner:

1. Vai su GitHub → Repository → Settings → Actions → Runners
2. Clicca "New self-hosted runner"
3. Segui le istruzioni per il tuo OS
4. Assicurati che il runner sia in esecuzione:

```bash
cd ~/actions-runner
./run.sh
```

O avvialo come servizio:

```bash
cd ~/actions-runner
sudo ./svc.sh install
sudo ./svc.sh start
sudo ./svc.sh status
```

## 🔄 Come Funziona il Deployment Automatico

Ogni volta che fai push su `main`:

1. **Il runner GitHub Actions** si attiva automaticamente
2. **Checkout del codice** nella directory temporanea del runner
3. **Sincronizzazione** → Il codice viene copiato in `/home/samuelevalente/altar-trader-hub-be`
4. **Installazione dipendenze** → Aggiorna il virtual environment
5. **Migrazioni database** → Esegue eventuali migrazioni pendenti
6. **Riavvio servizio** → Riavvia l'applicazione con systemd
7. **Verifica** → Controlla che il servizio sia attivo

### Workflow GitHub Actions

Il file `.github/workflows/deploy.yml` gestisce tutto automaticamente:

- ✅ Esclude file non necessari (venv, cache, .git)
- ✅ Mantiene il file `.env` esistente
- ✅ Mantiene il database esistente
- ✅ Aggiorna solo il codice e le dipendenze
- ✅ Esegue le migrazioni in modo sicuro
- ✅ Riavvia il servizio automaticamente

## 📊 Comandi Utili

### Gestione del Servizio

```bash
# Stato del servizio
sudo systemctl status altar-trader-hub

# Avvia il servizio
sudo systemctl start altar-trader-hub

# Ferma il servizio
sudo systemctl stop altar-trader-hub

# Riavvia il servizio
sudo systemctl restart altar-trader-hub

# Log in tempo reale
sudo journalctl -u altar-trader-hub -f

# Log delle ultime 100 righe
sudo journalctl -u altar-trader-hub -n 100
```

### Riavvio Manuale (senza systemd)

Se preferisci non usare systemd:

```bash
cd /home/samuelevalente/altar-trader-hub-be
bash scripts/restart_service.sh
```

### Verifica Deployment

```bash
# Controlla l'ultimo commit deployato
cd /home/samuelevalente/altar-trader-hub-be
git log -1

# Testa l'API
curl http://localhost:8001/health
curl http://localhost:8001/docs

# Verifica i processi in esecuzione
ps aux | grep uvicorn
```

## 🐛 Troubleshooting

### Il servizio non si avvia

1. Controlla i log:
```bash
sudo journalctl -u altar-trader-hub -n 50
```

2. Verifica le dipendenze:
```bash
cd /home/samuelevalente/altar-trader-hub-be
source venv/bin/activate
python -c "import fastapi, uvicorn, sqlalchemy"
```

3. Controlla PostgreSQL e Redis:
```bash
sudo systemctl status postgresql
sudo systemctl status redis
redis-cli ping
```

### Il deployment fallisce

1. Controlla i log di GitHub Actions nel repository
2. Verifica che il runner sia attivo:
```bash
cd ~/actions-runner
./run.sh status
# oppure
sudo ./svc.sh status
```

3. Verifica i permessi:
```bash
ls -la /home/samuelevalente/altar-trader-hub-be
```

### Errori di permessi

Se il runner non riesce a riavviare il servizio:

```bash
# Ri-esegui la configurazione dei permessi
sudo bash /home/samuelevalente/altar-trader-hub-be/scripts/configure_runner.sh

# Verifica il file sudoers
sudo cat /etc/sudoers.d/github-runner
```

### Database non raggiungibile

Verifica che PostgreSQL sia in ascolto:

```bash
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT version();"
```

Controlla la stringa di connessione nel file `.env`.

## 📝 Note Importanti

- ⚠️ Il file `.env` non viene sovrascritto durante il deployment
- ⚠️ Il database `trading_bot.db` viene mantenuto (se usi SQLite)
- ⚠️ I log dell'applicazione sono in `logs/app.log` se usi lo script manuale
- ⚠️ I log systemd sono visibili con `journalctl`
- ✅ Il servizio si riavvia automaticamente in caso di crash (configurazione systemd)
- ✅ Il servizio si avvia automaticamente al boot del sistema

## 🔐 Sicurezza

- Il file `.env` contiene dati sensibili → **non committarlo mai su Git**
- Il servizio gira con l'utente `samuelevalente` (non root)
- I permessi sudo sono limitati solo ai comandi necessari
- Le variabili d'ambiente sono isolate nel servizio

## 🎯 Prossimi Passi

1. Configura SSL/TLS con nginx come reverse proxy
2. Configura backup automatici del database
3. Configura monitoring con Prometheus/Grafana
4. Configura alerting per i crash del servizio

## 🆘 Supporto

In caso di problemi:

1. Controlla i log: `sudo journalctl -u altar-trader-hub -f`
2. Verifica lo stato: `sudo systemctl status altar-trader-hub`
3. Testa manualmente: `bash scripts/restart_service.sh`
4. Controlla i workflow su GitHub Actions

---

**✨ Una volta configurato, ogni push su main eseguirà il deployment automatico!**

