#!/bin/bash

# Script per installare i prerequisiti sul Raspberry Pi (NON INTERATTIVO)

set -e

export DEBIAN_FRONTEND=noninteractive

echo "🔧 Installazione prerequisiti per Altar Trader Hub"
echo "=================================================="
echo ""

# Aggiorna i repository
echo "📦 Aggiornamento repository..."
sudo apt-get update -qq

# Installa Git
echo ""
echo "📥 Installazione Git..."
sudo apt-get install -y -qq git

# Installa Python 3 e pip (se non già presenti)
echo ""
echo "🐍 Verifica Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "Installazione Python 3..."
    sudo apt-get install -y -qq python3 python3-pip python3-venv
else
    echo "✅ Python 3 già installato: $(python3 --version)"
fi

# Installa PostgreSQL development files (necessari per psycopg2)
echo ""
echo "🗄️  Installazione librerie PostgreSQL..."
sudo apt-get install -y -qq libpq-dev python3-dev

# Installa Redis
echo ""
echo "📦 Installazione Redis..."
if ! command -v redis-cli &> /dev/null; then
    sudo apt-get install -y -qq redis-server
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
    echo "✅ Redis installato e avviato"
else
    echo "✅ Redis già installato"
    # Assicurati che sia in esecuzione
    sudo systemctl start redis-server 2>/dev/null || true
fi

# Installa PostgreSQL
echo ""
echo "🐘 Installazione PostgreSQL..."
if ! command -v psql &> /dev/null; then
    sudo apt-get install -y -qq postgresql postgresql-contrib
    sudo systemctl enable postgresql
    sudo systemctl start postgresql
    echo "✅ PostgreSQL installato e avviato"
else
    echo "✅ PostgreSQL già installato"
    # Assicurati che sia in esecuzione
    sudo systemctl start postgresql 2>/dev/null || true
fi

# Installa rsync (necessario per il workflow GitHub Actions)
echo ""
echo "🔄 Installazione rsync..."
if ! command -v rsync &> /dev/null; then
    sudo apt-get install -y -qq rsync
    echo "✅ rsync installato"
else
    echo "✅ rsync già installato"
fi

# Installa curl (per test API)
echo ""
echo "🌐 Verifica curl..."
if ! command -v curl &> /dev/null; then
    sudo apt-get install -y -qq curl
    echo "✅ curl installato"
else
    echo "✅ curl già installato"
fi

echo ""
echo "✨ ================================================"
echo "✨ Prerequisiti installati con successo!"
echo "✨ ================================================"
echo ""
echo "Versioni installate:"
echo "  - Git: $(git --version)"
echo "  - Python: $(python3 --version)"
echo "  - pip: $(pip3 --version)"
echo ""
echo "Servizi attivi:"
if systemctl is-active --quiet redis-server; then
    echo "  ✅ Redis: attivo"
else
    echo "  ⚠️  Redis: non attivo"
fi
if systemctl is-active --quiet postgresql; then
    echo "  ✅ PostgreSQL: attivo"
else
    echo "  ⚠️  PostgreSQL: non attivo"
fi
echo ""
echo "🎯 Ora puoi eseguire il deployment con:"
echo "   ./deploy_all.sh"
echo ""

