#!/bin/bash

# Script per avviare l'applicazione in modalità sviluppo

echo "🚀 Avvio dell'applicazione Altar Trader Hub Backend..."

# Controlla se l'ambiente virtuale esiste
if [ ! -d "venv" ]; then
    echo "❌ Ambiente virtuale non trovato. Eseguire prima: python -m venv venv"
    exit 1
fi

# Attiva l'ambiente virtuale
echo "📦 Attivazione ambiente virtuale..."
source venv/bin/activate

# Controlla se Redis è in esecuzione
echo "🔍 Controllo Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis non è in esecuzione. Avviare Redis prima di continuare."
    echo "   Su macOS: brew services start redis"
    echo "   Su Ubuntu: sudo systemctl start redis"
    echo "   Con Docker: docker run -d -p 6379:6379 redis:alpine"
    exit 1
fi

echo "✅ Redis è in esecuzione"

# Controlla se le dipendenze sono installate
echo "📋 Controllo dipendenze..."
if ! python -c "import fastapi" > /dev/null 2>&1; then
    echo "❌ Dipendenze non installate. Eseguire prima: pip install -r requirements.txt"
    exit 1
fi

echo "✅ Dipendenze installate"

# Avvia l'applicazione
echo "🚀 Avvio dell'applicazione..."
echo "   API: http://localhost:8000"
echo "   Health check: http://localhost:8000/health"
echo "   Documentazione: http://localhost:8000/docs"
echo ""
echo "Premere Ctrl+C per fermare l'applicazione"
echo ""

python run.py
