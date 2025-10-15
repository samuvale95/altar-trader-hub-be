#!/bin/bash

# Script per configurare i permessi del runner GitHub Actions

set -e

RUNNER_USER="samuelevalente"
SERVICE_NAME="altar-trader-hub"

echo "🔧 Configurazione permessi per GitHub Actions runner..."

# Verifica che lo script sia eseguito con permessi sudo
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Questo script richiede privilegi sudo"
    echo "   Riprova con: sudo bash $0"
    exit 1
fi

# Crea un file sudoers per permettere al runner di riavviare il servizio senza password
echo "📝 Configurazione permessi sudo per il runner..."
cat > /etc/sudoers.d/github-runner << EOF
# Permetti all'utente del runner di gestire il servizio altar-trader-hub senza password
$RUNNER_USER ALL=(ALL) NOPASSWD: /bin/systemctl start $SERVICE_NAME.service
$RUNNER_USER ALL=(ALL) NOPASSWD: /bin/systemctl stop $SERVICE_NAME.service
$RUNNER_USER ALL=(ALL) NOPASSWD: /bin/systemctl restart $SERVICE_NAME.service
$RUNNER_USER ALL=(ALL) NOPASSWD: /bin/systemctl status $SERVICE_NAME.service
$RUNNER_USER ALL=(ALL) NOPASSWD: /bin/systemctl is-active $SERVICE_NAME.service
$RUNNER_USER ALL=(ALL) NOPASSWD: /bin/journalctl -u $SERVICE_NAME*
EOF

# Imposta i permessi corretti per il file sudoers
chmod 440 /etc/sudoers.d/github-runner

# Verifica la configurazione
if visudo -c -f /etc/sudoers.d/github-runner; then
    echo "✅ Configurazione sudoers verificata e installata"
else
    echo "❌ Errore nella configurazione sudoers"
    rm -f /etc/sudoers.d/github-runner
    exit 1
fi

echo ""
echo "✅ Configurazione completata!"
echo ""
echo "Il runner può ora gestire il servizio $SERVICE_NAME con sudo senza password."

