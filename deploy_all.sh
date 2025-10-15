#!/bin/bash

# Script completo per deployment automatico su Raspberry Pi
# Questo script:
# 1. Committa e pusha i file locali su GitHub
# 2. Si connette al Raspberry Pi
# 3. Clona/aggiorna il repository
# 4. Esegue la configurazione automatica

set -e

# Configurazione
RASPBERRY_PI_HOST="samuelevalente@raspberrypi.local"
DEPLOY_DIR="/home/samuelevalente/altar-trader-hub-be"
GITHUB_REPO_URL="https://github.com/samuelevalente/altar-trader-hub-be.git"  # Modifica se necessario

echo "🚀 ================================================"
echo "🚀 Deployment Automatico Altar Trader Hub"
echo "🚀 ================================================"
echo ""

# Step 1: Commit e Push locale
echo "📦 Step 1: Commit e Push dei file su GitHub..."
echo "----------------------------------------"

# Verifica se ci sono modifiche
if [[ -n $(git status -s) ]]; then
    echo "✅ Modifiche rilevate, eseguo commit..."
    
    git add .github/workflows/deploy.yml
    git add scripts/
    git add .gitignore
    git add DEPLOYMENT_SETUP.md
    git add deploy_all.sh
    
    git commit -m "Add automatic deployment configuration

- Updated GitHub Actions workflow for self-hosted deployment
- Added systemd service configuration
- Added setup and restart scripts
- Added comprehensive deployment documentation
- Added deploy_all.sh for one-command deployment"
    
    echo "📤 Push su GitHub..."
    git push origin main
    
    echo "✅ Codice pushato su GitHub"
else
    echo "ℹ️  Nessuna modifica locale da committare"
fi

echo ""
echo "⏳ Attendo 3 secondi per permettere a GitHub di processare il push..."
sleep 3
echo ""

# Step 2: Deployment su Raspberry Pi
echo "🔧 Step 2: Deployment su Raspberry Pi..."
echo "----------------------------------------"

# Crea uno script temporaneo da eseguire sul Raspberry Pi
REMOTE_SCRIPT=$(cat << 'EOF'
#!/bin/bash
set -e

DEPLOY_DIR="/home/samuelevalente/altar-trader-hub-be"
GITHUB_REPO_URL="https://github.com/samuelevalente/altar-trader-hub-be.git"

echo ""
echo "🎯 Deployment su Raspberry Pi"
echo "=============================="
echo ""

# Crea directory se non esiste
if [ ! -d "$DEPLOY_DIR" ]; then
    echo "📁 Creazione directory $DEPLOY_DIR..."
    mkdir -p "$DEPLOY_DIR"
fi

cd "$DEPLOY_DIR"

# Clone o pull del repository
if [ -d ".git" ]; then
    echo "🔄 Aggiornamento repository esistente..."
    git fetch --all
    git reset --hard origin/main
    git pull origin main
else
    echo "📥 Clone del repository..."
    git clone "$GITHUB_REPO_URL" .
fi

echo "✅ Codice aggiornato"
echo ""

# Rendi eseguibili gli script
echo "🔧 Configurazione permessi script..."
chmod +x scripts/*.sh
echo "✅ Script configurati"
echo ""

# Verifica se il file .env esiste
if [ ! -f ".env" ]; then
    echo "⚠️  File .env non trovato!"
    if [ -f "env.example" ]; then
        echo "📋 Creazione .env da env.example..."
        cp env.example .env
        echo "⚠️  IMPORTANTE: Configura il file .env prima di proseguire!"
        echo ""
        read -p "Vuoi configurare .env ora? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            nano .env
        else
            echo "⚠️  Ricordati di configurare .env manualmente!"
        fi
    else
        echo "❌ env.example non trovato. Crea manualmente il file .env"
        exit 1
    fi
fi

echo ""
echo "🚀 Esecuzione setup automatico..."
echo "=================================="
echo ""

# Esegui il setup automatico
bash scripts/quick_setup.sh

echo ""
echo "✨ ================================================"
echo "✨ Deployment completato con successo!"
echo "✨ ================================================"
echo ""
EOF
)

# Esegui lo script sul Raspberry Pi
echo "🔗 Connessione al Raspberry Pi..."
echo ""

ssh -t "$RASPBERRY_PI_HOST" "bash -s" << EOF
$REMOTE_SCRIPT
EOF

# Verifica finale
echo ""
echo "🔍 Verifica finale..."
echo "----------------------------------------"

ssh "$RASPBERRY_PI_HOST" << 'VERIFY_EOF'
echo ""
echo "📊 Stato del servizio:"
sudo systemctl status altar-trader-hub.service --no-pager || echo "⚠️  Servizio non ancora attivo (normale al primo setup)"

echo ""
echo "🌐 Test connessione API..."
sleep 2
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ API risponde correttamente!"
else
    echo "⚠️  API non risponde ancora (potrebbe richiedere qualche secondo)"
fi

echo ""
VERIFY_EOF

# Riepilogo finale
echo ""
echo "✨ ================================================"
echo "✨ DEPLOYMENT COMPLETATO!"
echo "✨ ================================================"
echo ""
echo "📊 Il servizio dovrebbe essere attivo su:"
echo "   - Health Check: http://raspberrypi.local:8001/health"
echo "   - Documentazione: http://raspberrypi.local:8001/docs"
echo ""
echo "🔍 Per verificare lo stato:"
echo "   ssh $RASPBERRY_PI_HOST 'sudo systemctl status altar-trader-hub'"
echo ""
echo "📋 Per vedere i log:"
echo "   ssh $RASPBERRY_PI_HOST 'sudo journalctl -u altar-trader-hub -f'"
echo ""
echo "🎯 Prossimi passi:"
echo "   1. Verifica che l'API risponda"
echo "   2. Configura il GitHub Actions runner se non l'hai ancora fatto"
echo "   3. Ogni push su main eseguirà il deployment automatico!"
echo ""
echo "📚 Consulta DEPLOYMENT_SETUP.md per maggiori informazioni"
echo ""

