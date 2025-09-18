#!/bin/bash

# Script per eseguire tutti i test

echo "🧪 Esecuzione test per Altar Trader Hub Backend..."

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

# Avvia l'applicazione in background
echo "🚀 Avvio dell'applicazione in background..."
python -c "import uvicorn; from app.main import app; uvicorn.run(app, host='0.0.0.0', port=8001)" &
APP_PID=$!

# Aspetta che l'applicazione si avvii
echo "⏳ Attesa avvio applicazione..."
sleep 5

# Esegui i test
echo "🧪 Esecuzione test API..."
python test_api.py

# Ferma l'applicazione
echo "🛑 Fermata applicazione..."
kill $APP_PID

echo "✅ Test completati!"
