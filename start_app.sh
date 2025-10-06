#!/bin/bash

# Script per avviare l'applicazione Altar Trader Hub

echo "🚀 Avvio Altar Trader Hub Backend..."

# Vai nella directory del progetto
cd "$(dirname "$0")"

# Attiva l'ambiente virtuale
source venv/bin/activate

# Verifica che l'ambiente virtuale sia attivo
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Ambiente virtuale attivato: $VIRTUAL_ENV"
else
    echo "❌ Errore: Ambiente virtuale non attivato"
    exit 1
fi

# Verifica che le dipendenze siano installate
echo "📦 Verifica dipendenze..."
python -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Dipendenze OK"
else
    echo "❌ Dipendenze mancanti. Installa con: pip install -r requirements.txt"
    exit 1
fi

# Avvia l'applicazione
echo "🌐 Avvio server su http://localhost:8001"
echo "📚 Documentazione API: http://localhost:8001/docs"
echo "🛑 Per fermare: Ctrl+C"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
