#!/usr/bin/env python3
"""
Script per scaricare gli ultimi dati delle cripto.
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.core.config import settings
from app.services.data_feeder import data_feeder
from app.core.database import SessionLocal
from app.models.market_data import MarketData

def get_latest_crypto_data(symbol: str = "BTCUSDT", timeframe: str = "1h", limit: int = 100):
    """Scarica gli ultimi dati delle cripto."""
    
    print(f"🔄 Scaricando dati per {symbol} {timeframe}...")
    
    # Avvia la raccolta dati
    try:
        data_feeder.collect_market_data()
        print("✅ Raccolta dati completata")
    except Exception as e:
        print(f"⚠️ Errore nella raccolta dati: {e}")
    
    # Ottieni i dati dal database
    db = SessionLocal()
    try:
        market_data = db.query(MarketData).filter(
            MarketData.symbol == symbol.upper(),
            MarketData.timeframe == timeframe
        ).order_by(MarketData.timestamp.desc()).limit(limit).all()
        
        if not market_data:
            print(f"❌ Nessun dato trovato per {symbol} {timeframe}")
            return None
        
        print(f"📊 Trovati {len(market_data)} record")
        
        # Mostra i dati più recenti
        latest = market_data[0]
        print(f"\n📈 Ultimo prezzo {symbol}:")
        print(f"   Timestamp: {latest.timestamp}")
        print(f"   Prezzo: ${latest.close_price:,.2f}")
        print(f"   Volume: {latest.volume:,.2f}")
        print(f"   High: ${latest.high_price:,.2f}")
        print(f"   Low: ${latest.low_price:,.2f}")
        
        return market_data
        
    finally:
        db.close()

def get_available_symbols():
    """Ottieni i simboli disponibili."""
    
    print("🔍 Simboli disponibili:")
    
    db = SessionLocal()
    try:
        symbols = db.query(MarketData.symbol).distinct().all()
        symbols = [s[0] for s in symbols]
        
        for symbol in sorted(symbols):
            print(f"   • {symbol}")
        
        return symbols
        
    finally:
        db.close()

def get_latest_prices():
    """Ottieni i prezzi più recenti per tutti i simboli."""
    
    print("💰 Prezzi più recenti:")
    
    db = SessionLocal()
    try:
        # Ottieni l'ultimo prezzo per ogni simbolo
        subquery = db.query(
            MarketData.symbol,
            db.func.max(MarketData.timestamp).label('max_timestamp')
        ).group_by(MarketData.symbol).subquery()
        
        latest_prices = db.query(MarketData).join(
            subquery,
            (MarketData.symbol == subquery.c.symbol) & 
            (MarketData.timestamp == subquery.c.max_timestamp)
        ).all()
        
        for data in latest_prices:
            print(f"   {data.symbol}: ${data.close_price:,.2f} ({data.timestamp})")
        
        return latest_prices
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Download Dati Cripto")
    print("=" * 50)
    
    # Mostra simboli disponibili
    get_available_symbols()
    print()
    
    # Mostra prezzi più recenti
    get_latest_prices()
    print()
    
    # Scarica dati specifici
    get_latest_crypto_data("BTCUSDT", "1h", 10)
    print()
    
    get_latest_crypto_data("ETHUSDT", "1h", 10)
