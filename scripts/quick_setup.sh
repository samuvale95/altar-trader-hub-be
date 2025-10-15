#!/bin/bash

# Script di setup rapido per Altar Trader Hub
# Esegue tutti i passaggi necessari per configurare il deployment automatico

set -e

APP_DIR="/home/samuelevalente/altar-trader-hub-be"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Setup Rapido Altar Trader Hub Backend"
echo "========================================"
echo ""

# Controlla se siamo nel posto giusto
if [ ! -f "$SCRIPT_DIR/setup_systemd.sh" ]; then
    echo "❌ Errore: script non trovato. Esegui questo script dalla directory corretta."
    exit 1
fi

# Step 1: Verifica prerequisiti
echo "📋 Step 1/6: Verifica prerequisiti..."
echo ""

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non trovato. Installalo prima di continuare."
    exit 1
fi
echo "✅ Python 3: $(python3 --version)"

# Verifica Git
if ! command -v git &> /dev/null; then
    echo "❌ Git non trovato. Installalo prima di continuare."
    exit 1
fi
echo "✅ Git: $(git --version | head -n1)"

# Verifica PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL non trovato. Potrebbe essere necessario installarlo."
else
    echo "✅ PostgreSQL installato"
fi

# Verifica Redis
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️  Redis non trovato. Potrebbe essere necessario installarlo."
else
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis in esecuzione"
    else
        echo "⚠️  Redis installato ma non in esecuzione"
    fi
fi

echo ""
read -p "Continuare con il setup? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup annullato."
    exit 0
fi

# Step 2: Crea ambiente virtuale
echo ""
echo "📦 Step 2/6: Creazione ambiente virtuale..."
if [ ! -d "$APP_DIR/venv" ]; then
    python3 -m venv "$APP_DIR/venv"
    echo "✅ Ambiente virtuale creato"
else
    echo "✅ Ambiente virtuale già esistente"
fi

# Step 3: Installa dipendenze
echo ""
echo "🔧 Step 3/6: Installazione dipendenze..."
source "$APP_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"
echo "✅ Dipendenze installate"

# Step 4: Verifica/Crea file .env
echo ""
echo "⚙️  Step 4/6: Configurazione file .env..."
if [ ! -f "$APP_DIR/.env" ]; then
    echo "⚠️  File .env non trovato. Creazione template..."
    
    if [ -f "$APP_DIR/env.example" ]; then
        cp "$APP_DIR/env.example" "$APP_DIR/.env"
        echo "✅ File .env creato da env.example"
        echo "⚠️  IMPORTANTE: Modifica $APP_DIR/.env con le tue configurazioni!"
        echo ""
        read -p "Vuoi modificarlo ora? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} "$APP_DIR/.env"
        fi
    else
        echo "❌ env.example non trovato. Crea manualmente il file .env"
        exit 1
    fi
else
    echo "✅ File .env già esistente"
fi

# Step 5: Crea directory logs
echo ""
echo "📁 Step 5/6: Creazione directory logs..."
mkdir -p "$APP_DIR/logs"
echo "✅ Directory logs creata"

# Step 6: Setup systemd
echo ""
echo "🔧 Step 6/6: Configurazione servizio systemd..."
echo "   Questo passaggio richiede privilegi sudo"
echo ""

if [ "$EUID" -eq 0 ]; then
    # Già root
    bash "$SCRIPT_DIR/setup_systemd.sh"
    bash "$SCRIPT_DIR/configure_runner.sh"
else
    # Chiedi sudo
    sudo bash "$SCRIPT_DIR/setup_systemd.sh"
    sudo bash "$SCRIPT_DIR/configure_runner.sh"
fi

# Riepilogo finale
echo ""
echo "✨ ============================================="
echo "✨ Setup completato con successo!"
echo "✨ ============================================="
echo ""
echo "📊 Stato del servizio:"
sudo systemctl status altar-trader-hub.service --no-pager || true
echo ""
echo "🌐 L'API dovrebbe essere disponibile su:"
echo "   - Health Check: http://localhost:8001/health"
echo "   - Documentazione: http://localhost:8001/docs"
echo ""
echo "📋 Comandi utili:"
echo "   - Stato:   sudo systemctl status altar-trader-hub"
echo "   - Restart: sudo systemctl restart altar-trader-hub"
echo "   - Log:     sudo journalctl -u altar-trader-hub -f"
echo ""
echo "🚀 Prossimi passi:"
echo "   1. Verifica che l'API risponda: curl http://localhost:8001/health"
echo "   2. Configura il GitHub Actions runner se non l'hai già fatto"
echo "   3. Fai push su main per testare il deployment automatico"
echo ""
echo "📚 Consulta DEPLOYMENT_SETUP.md per maggiori informazioni"
echo ""

