#!/bin/bash

# Script per riavviare il servizio Altar Trader Hub

set -e

SERVICE_NAME="altar-trader-hub"
APP_DIR="/home/samuelevalente/altar-trader-hub-be"
VENV_DIR="$APP_DIR/venv"
PID_FILE="$APP_DIR/altar-trader-hub.pid"

echo "🔄 Riavvio servizio Altar Trader Hub..."

# Funzione per fermare il servizio
stop_service() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "🛑 Fermando processo esistente (PID: $PID)..."
            kill -TERM $PID
            
            # Aspetta che il processo si fermi
            for i in {1..10}; do
                if ! ps -p $PID > /dev/null 2>&1; then
                    break
                fi
                echo "   Attesa terminazione processo..."
                sleep 1
            done
            
            # Forza la terminazione se ancora in esecuzione
            if ps -p $PID > /dev/null 2>&1; then
                echo "   Forzando terminazione processo..."
                kill -9 $PID
            fi
        fi
        rm -f "$PID_FILE"
    else
        # Prova a trovare il processo in esecuzione
        PIDS=$(pgrep -f "uvicorn app.main:app")
        if [ ! -z "$PIDS" ]; then
            echo "🛑 Fermando processi uvicorn esistenti..."
            echo "$PIDS" | xargs kill -TERM
            sleep 2
        fi
    fi
}

# Funzione per avviare il servizio
start_service() {
    echo "🚀 Avvio nuovo servizio..."
    cd "$APP_DIR"
    
    # Verifica che il venv esista
    if [ ! -d "$VENV_DIR" ]; then
        echo "❌ Errore: ambiente virtuale non trovato in $VENV_DIR"
        exit 1
    fi
    
    # Attiva venv e avvia l'applicazione
    source "$VENV_DIR/bin/activate"
    
    # Verifica che uvicorn sia installato
    if ! command -v uvicorn &> /dev/null; then
        echo "❌ Errore: uvicorn non trovato"
        exit 1
    fi
    
    # Avvia l'applicazione in background
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4 > "$APP_DIR/logs/app.log" 2>&1 &
    
    # Salva il PID
    echo $! > "$PID_FILE"
    
    echo "✅ Servizio avviato con PID: $(cat $PID_FILE)"
}

# Crea la directory dei log se non esiste
mkdir -p "$APP_DIR/logs"

# Ferma il servizio esistente
stop_service

# Aspetta un momento
sleep 2

# Avvia il nuovo servizio
start_service

# Verifica che il servizio sia attivo
sleep 3
if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo "✅ Servizio riavviato con successo!"
    echo "📊 Log disponibili in: $APP_DIR/logs/app.log"
    echo "🌐 API disponibile su: http://localhost:8001"
    echo "📚 Documentazione: http://localhost:8001/docs"
else
    echo "❌ Errore: il servizio non si è avviato correttamente"
    echo "📋 Controlla i log in: $APP_DIR/logs/app.log"
    exit 1
fi

