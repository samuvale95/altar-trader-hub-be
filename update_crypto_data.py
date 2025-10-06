#!/usr/bin/env python3
"""
Script per aggiornare automaticamente i dati delle cripto.
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
from app.core.database import SessionLocal
from app.models.market_data import MarketData

def update_crypto_data():
    """Aggiorna i dati delle cripto."""
    
    print(f"🔄 Aggiornamento dati alle {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Avvia la raccolta dati
        data_feeder.collect_market_data()
        
        # Verifica i dati aggiornati
        db = SessionLocal()
        try:
            latest_data = db.query(MarketData).order_by(
                MarketData.timestamp.desc()
            ).limit(5).all()
            
            print("📊 Ultimi dati aggiornati:")
            for data in latest_data:
                print(f"   {data.symbol} {data.timeframe}: ${data.close_price:,.2f} ({data.timestamp})")
                
        finally:
            db.close()
            
        print("✅ Aggiornamento completato")
        
    except Exception as e:
        print(f"❌ Errore nell'aggiornamento: {e}")

def main():
    """Funzione principale."""
    
    print("🚀 Avvio aggiornamento automatico dati cripto")
    print("=" * 50)
    
    # Aggiorna immediatamente
    update_crypto_data()
    
    # Programma aggiornamenti automatici
    schedule.every(5).minutes.do(update_crypto_data)  # Ogni 5 minuti
    schedule.every().hour.do(update_crypto_data)      # Ogni ora
    
    print("⏰ Aggiornamenti programmati:")
    print("   • Ogni 5 minuti")
    print("   • Ogni ora")
    print("   • Premi Ctrl+C per fermare")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Controlla ogni minuto
            
    except KeyboardInterrupt:
        print("\n🛑 Aggiornamento fermato")

if __name__ == "__main__":
    main()


