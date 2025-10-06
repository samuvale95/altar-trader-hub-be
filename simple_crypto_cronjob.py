#!/usr/bin/env python3
"""
Cronjob semplice per scaricare dati cripto ogni tot secondi.
"""

import sys
import os
import time
import schedule
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.services.data_feeder import data_feeder
from app.services.symbol_manager import symbol_manager
from app.core.database import SessionLocal
from app.models.market_data import MarketData

# Configurazione
MAIN_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT", "XRPUSDT",
    "SOLUSDT", "DOGEUSDT", "DOTUSDT", "AVAXUSDT", "LINKUSDT"
]

TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]

def collect_crypto_data():
    """Raccoglie dati delle cripto."""
    
    print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Raccolta dati cripto...")
    
    try:
        # Avvia la raccolta dati
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            data_feeder.collect_market_data(MAIN_SYMBOLS, TIMEFRAMES)
        )
        
        loop.close()
        
        print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Raccolta completata")
        return result
        
    except Exception as e:
        print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Errore: {e}")
        return None

def collect_high_volume_symbols():
    """Raccoglie dati dei simboli ad alto volume."""
    
    print(f"📊 [{datetime.now().strftime('%H:%M:%S')}] Raccolta simboli ad alto volume...")
    
    try:
        # Ottieni simboli con alto volume
        symbols = symbol_manager.get_top_volume_symbols(limit=30)
        
        if not symbols:
            print("⚠️ Nessun simbolo ad alto volume trovato")
            return
        
        # Avvia la raccolta dati
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            data_feeder.collect_market_data(symbols, ["1m", "5m", "1h"])
        )
        
        loop.close()
        
        print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Raccolta simboli completata: {len(symbols)} simboli")
        
    except Exception as e:
        print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Errore simboli: {e}")

def update_symbol_list():
    """Aggiorna la lista dei simboli."""
    
    print(f"🔄 [{datetime.now().strftime('%H:%M:%S')}] Aggiornamento lista simboli...")
    
    try:
        symbol_manager.refresh_symbols()
        print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Lista simboli aggiornata")
        
    except Exception as e:
        print(f"❌ [{datetime.now().strftime('%H:%M:%S')}] Errore aggiornamento: {e}")

def show_status():
    """Mostra lo stato del sistema."""
    
    print(f"📊 [{datetime.now().strftime('%H:%M:%S')}] Stato sistema:")
    
    try:
        db = SessionLocal()
        
        # Conta i record totali
        total_records = db.query(MarketData).count()
        
        # Conta i simboli unici
        unique_symbols = db.query(MarketData.symbol).distinct().count()
        
        # Ultimo aggiornamento
        latest_data = db.query(MarketData).order_by(
            MarketData.timestamp.desc()
        ).first()
        
        db.close()
        
        print(f"   📈 Record totali: {total_records:,}")
        print(f"   🏷️  Simboli unici: {unique_symbols}")
        
        if latest_data:
            print(f"   ⏰ Ultimo aggiornamento: {latest_data.timestamp}")
            print(f"   💰 Ultimo prezzo ({latest_data.symbol}): ${latest_data.close_price:,.2f}")
        
    except Exception as e:
        print(f"   ❌ Errore nel recupero stato: {e}")

def main():
    """Funzione principale."""
    
    print("🚀 Cronjob Raccolta Dati Cripto")
    print("=" * 50)
    
    # Programma i task
    schedule.every(30).seconds.do(collect_crypto_data)  # Ogni 30 secondi
    schedule.every(5).minutes.do(collect_high_volume_symbols)  # Ogni 5 minuti
    schedule.every(30).minutes.do(update_symbol_list)  # Ogni 30 minuti
    schedule.every(10).minutes.do(show_status)  # Ogni 10 minuti
    
    print("⏰ Schedule configurato:")
    print("   • Raccolta dati principali: ogni 30 secondi")
    print("   • Simboli ad alto volume: ogni 5 minuti")
    print("   • Aggiornamento simboli: ogni 30 minuti")
    print("   • Stato sistema: ogni 10 minuti")
    print("\n⏹️  Premi Ctrl+C per fermare")
    
    # Esegui immediatamente
    collect_crypto_data()
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Cronjob fermato")

if __name__ == "__main__":
    import asyncio
    main()

