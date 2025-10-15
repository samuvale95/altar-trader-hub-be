#!/bin/bash

# Script completo di setup da eseguire sul Raspberry Pi
# Questo script deve essere eseguito DIRETTAMENTE sul Raspberry Pi

set -e

APP_DIR="/home/samuelevalente/altar-trader-hub-be"

echo "🚀 ================================================"
echo "🚀 Setup Completo Altar Trader Hub su Raspberry Pi"
echo "🚀 ================================================"
echo ""

cd "$APP_DIR"

# Step 1: Verifica file .env
echo "⚙️  Step 1/5: Verifica configurazione..."
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ File .env creato da env.example"
        echo "⚠️  IMPORTANTE: Configura il file .env con le tue impostazioni prima dell'uso in produzione!"
    else
        echo "❌ env.example non trovato!"
        exit 1
    fi
else
    echo "✅ File .env già presente"
fi

# Step 2: Crea/aggiorna virtual environment
echo ""
echo "📦 Step 2/5: Configurazione ambiente virtuale..."
if [ ! -d "venv" ]; then
    echo "Creazione virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "✅ Virtual environment attivato"

# Step 3: Installa dipendenze
echo ""
echo "🔧 Step 3/5: Installazione dipendenze Python..."
echo "   (Questo può richiedere alcuni minuti...)"
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Dipendenze installate"

# Step 4: Crea directory necessarie
echo ""
echo "📁 Step 4/5: Creazione directory..."
mkdir -p logs
mkdir -p data
echo "✅ Directory create"

# Step 5: Configura servizio systemd
echo ""
echo "🔧 Step 5/5: Configurazione servizio systemd..."
if [ "$EUID" -eq 0 ]; then
    # Già root
    bash scripts/setup_systemd.sh
    bash scripts/configure_runner.sh
else
    # Richiedi sudo
    sudo bash scripts/setup_systemd.sh
    sudo bash scripts/configure_runner.sh
fi

echo ""
echo "✨ ================================================"
echo "✨ Setup completato con successo!"
echo "✨ ================================================"
echo ""

# Verifica stato servizio
echo "📊 Stato del servizio:"
sudo systemctl status altar-trader-hub.service --no-pager || echo "⚠️  Servizio non ancora attivo"

echo ""
echo "🌐 Test API..."
sleep 3
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ API risponde correttamente!"
    echo "   Health: http://localhost:8001/health"
    echo "   Docs: http://localhost:8001/docs"
else
    echo "⚠️  API non risponde ancora (potrebbe richiedere alcuni secondi)"
    echo "   Controlla i log con: sudo journalctl -u altar-trader-hub -f"
fi

echo ""
echo "📋 Comandi utili:"
echo "   - Stato:   sudo systemctl status altar-trader-hub"
echo "   - Restart: sudo systemctl restart altar-trader-hub"
echo "   - Log:     sudo journalctl -u altar-trader-hub -f"
echo ""
echo "🎯 Deployment automatico configurato!"
echo "   Ogni push su 'main' eseguirà il deployment automatico tramite GitHub Actions"
echo ""

