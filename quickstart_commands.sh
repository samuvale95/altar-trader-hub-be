#!/bin/bash

# Quick Start Commands for Heroku Deployment
# Run this script to deploy Altar Trader Hub to Heroku

set -e

echo "🚀 ================================================"
echo "🚀 Altar Trader Hub - Heroku Deployment"
echo "🚀 ================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI not found. Install it first:"
    echo "   https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

# Check if logged in
if ! heroku auth:whoami &> /dev/null; then
    echo "🔐 Please login to Heroku:"
    heroku login
fi

# App name
echo ""
echo "${YELLOW}Enter your Heroku app name (leave empty for auto-generated):${NC}"
read -p "App name: " APP_NAME

# Create app
echo ""
echo "📱 Creating Heroku app..."
if [ -z "$APP_NAME" ]; then
    heroku create
else
    heroku create $APP_NAME
fi

# Get app name
APP_NAME=$(heroku apps:info --json | python3 -c "import sys, json; print(json.load(sys.stdin)['app']['name'])" 2>/dev/null || echo "")

if [ -z "$APP_NAME" ]; then
    echo "❌ Failed to get app name. Please create manually:"
    echo "   heroku create your-app-name"
    exit 1
fi

echo "${GREEN}✅ App created: ${APP_NAME}${NC}"

# Database URL
echo ""
echo "${YELLOW}Database Configuration${NC}"
echo "You need a PostgreSQL database. Free options:"
echo "  1. Neon (https://neon.tech/) - 3GB free"
echo "  2. Supabase (https://supabase.com/) - 500MB free"
echo "  3. ElephantSQL (https://www.elephantsql.com/) - 20MB free"
echo ""
echo "Enter your PostgreSQL connection string:"
echo "Format: postgresql://user:password@host:port/database"
read -p "DATABASE_URL: " DATABASE_URL

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL is required"
    exit 1
fi

heroku config:set DATABASE_URL="$DATABASE_URL" -a $APP_NAME
echo "${GREEN}✅ Database configured${NC}"

# Redis URL (optional)
echo ""
echo "${YELLOW}Redis Configuration (Optional)${NC}"
echo "Redis is optional. Free option:"
echo "  - Upstash (https://upstash.com/) - 10k commands/day free"
echo ""
echo "Enter Redis URL (leave empty to skip):"
read -p "REDIS_URL: " REDIS_URL

if [ ! -z "$REDIS_URL" ]; then
    heroku config:set REDIS_URL="$REDIS_URL" -a $APP_NAME
    echo "${GREEN}✅ Redis configured${NC}"
else
    echo "ℹ️  Skipping Redis (app will work without it)"
fi

# Secret key
echo ""
echo "${YELLOW}Generating SECRET_KEY...${NC}"
SECRET_KEY=$(openssl rand -hex 32)
heroku config:set SECRET_KEY="$SECRET_KEY" -a $APP_NAME
echo "${GREEN}✅ SECRET_KEY generated${NC}"

# Environment
echo ""
echo "${YELLOW}Setting environment to production...${NC}"
heroku config:set ENVIRONMENT="production" -a $APP_NAME
heroku config:set DEBUG="false" -a $APP_NAME
echo "${GREEN}✅ Environment configured${NC}"

# Scheduler backend
echo ""
echo "${YELLOW}Scheduler Backend${NC}"
echo "Choose scheduler backend:"
echo "  1. APScheduler (default) - $7/month (runs in web dyno)"
echo "  2. Celery - $14/month (requires separate worker dyno)"
read -p "Enter choice (1 or 2, default: 1): " SCHEDULER_CHOICE

if [ "$SCHEDULER_CHOICE" = "2" ]; then
    heroku config:set SCHEDULER_BACKEND="celery" -a $APP_NAME
    echo "${GREEN}✅ Celery selected${NC}"
    echo "${YELLOW}Remember to:${NC}"
    echo "  1. Uncomment 'worker:' line in Procfile"
    echo "  2. Scale worker: heroku ps:scale worker=1:basic -a $APP_NAME"
else
    heroku config:set SCHEDULER_BACKEND="apscheduler" -a $APP_NAME
    echo "${GREEN}✅ APScheduler selected (default)${NC}"
fi

# CORS
echo ""
echo "${YELLOW}CORS Configuration${NC}"
echo "Enter allowed origins (comma-separated, or * for all):"
read -p "ALLOWED_ORIGINS (default: *): " ALLOWED_ORIGINS
ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-*}
heroku config:set ALLOWED_ORIGINS="$ALLOWED_ORIGINS" -a $APP_NAME
echo "${GREEN}✅ CORS configured${NC}"

# Deploy
echo ""
echo "${YELLOW}Deploying to Heroku...${NC}"
git push heroku main

echo ""
echo "${GREEN}✅ Deployment initiated${NC}"

# Scale to Basic dyno
echo ""
echo "${YELLOW}Scaling to Basic dyno (recommended for scheduler)...${NC}"
echo "Basic dyno costs $7/month and never sleeps"
read -p "Scale to Basic dyno? (y/n, default: y): " SCALE_BASIC
SCALE_BASIC=${SCALE_BASIC:-y}

if [ "$SCALE_BASIC" = "y" ] || [ "$SCALE_BASIC" = "Y" ]; then
    heroku ps:scale web=1:basic -a $APP_NAME
    echo "${GREEN}✅ Scaled to Basic dyno${NC}"
else
    echo "ℹ️  Keeping Eco dyno (will sleep after 30min)"
    heroku ps:scale web=1:eco -a $APP_NAME
fi

# Wait for deployment
echo ""
echo "${YELLOW}Waiting for deployment to complete...${NC}"
sleep 10

# Verify
echo ""
echo "${YELLOW}Verifying deployment...${NC}"
heroku logs --tail -n 50 -a $APP_NAME | head -20

# Final summary
echo ""
echo "✨ ================================================"
echo "✨ DEPLOYMENT COMPLETED!"
echo "✨ ================================================"
echo ""
echo "📊 App Information:"
echo "  - Name: $APP_NAME"
echo "  - URL: https://$APP_NAME.herokuapp.com"
echo "  - Docs: https://$APP_NAME.herokuapp.com/docs"
echo ""
echo "💰 Estimated Cost:"
if [ "$SCHEDULER_CHOICE" = "2" ]; then
    echo "  - Web dyno (Basic): $7/month"
    echo "  - Worker dyno (Basic): $7/month"
    echo "  - Total: $14/month"
else
    if [ "$SCALE_BASIC" = "y" ] || [ "$SCALE_BASIC" = "Y" ]; then
        echo "  - Web dyno (Basic): $7/month"
    else
        echo "  - Web dyno (Eco): $5/month"
    fi
fi
echo ""
echo "🔍 Useful Commands:"
echo "  - View logs: heroku logs --tail -a $APP_NAME"
echo "  - Restart: heroku restart -a $APP_NAME"
echo "  - Config: heroku config -a $APP_NAME"
echo "  - Scale: heroku ps:scale web=1:basic -a $APP_NAME"
echo ""
echo "📚 Documentation:"
echo "  - QUICKSTART_HEROKU.md - Quick start guide"
echo "  - HEROKU_DEPLOYMENT.md - Complete deployment guide"
echo "  - SCHEDULER_GUIDE.md - Scheduler documentation"
echo "  - MIGRATION_SUMMARY.md - Migration summary"
echo ""
echo "🎯 Next Steps:"
echo "  1. Test API: curl https://$APP_NAME.herokuapp.com/health"
echo "  2. Open docs: open https://$APP_NAME.herokuapp.com/docs"
echo "  3. Check logs: heroku logs --tail -a $APP_NAME"
echo "  4. Create trading strategies via API"
echo ""
echo "✨ Happy Trading! 🚀"

