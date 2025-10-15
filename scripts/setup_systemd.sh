#!/bin/bash

# Script per configurare il servizio systemd per Altar Trader Hub

set -e

SERVICE_NAME="altar-trader-hub"
SERVICE_FILE="altar-trader-hub.service"
SYSTEMD_DIR="/etc/systemd/system"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔧 Configurazione servizio systemd per Altar Trader Hub..."

# Verifica che lo script sia eseguito con permessi adeguati
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Questo script richiede privilegi sudo"
    echo "   Riprova con: sudo bash $0"
    exit 1
fi

# Copia il file del servizio
echo "📋 Installazione file del servizio..."
cp "$SCRIPT_DIR/$SERVICE_FILE" "$SYSTEMD_DIR/$SERVICE_FILE"
chmod 644 "$SYSTEMD_DIR/$SERVICE_FILE"

# Ricarica systemd
echo "🔄 Ricarica configurazione systemd..."
systemctl daemon-reload

# Abilita il servizio all'avvio
echo "✅ Abilitazione servizio all'avvio..."
systemctl enable $SERVICE_NAME.service

# Avvia il servizio
echo "🚀 Avvio servizio..."
systemctl start $SERVICE_NAME.service

# Verifica lo stato
echo ""
echo "📊 Stato del servizio:"
systemctl status $SERVICE_NAME.service --no-pager

echo ""
echo "✅ Configurazione completata!"
echo ""
echo "Comandi utili:"
echo "  - Stato servizio:    sudo systemctl status $SERVICE_NAME"
echo "  - Avvia servizio:    sudo systemctl start $SERVICE_NAME"
echo "  - Ferma servizio:    sudo systemctl stop $SERVICE_NAME"
echo "  - Riavvia servizio:  sudo systemctl restart $SERVICE_NAME"
echo "  - Log servizio:      sudo journalctl -u $SERVICE_NAME -f"
echo "  - Disabilita avvio:  sudo systemctl disable $SERVICE_NAME"

