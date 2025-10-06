#!/usr/bin/env python3
"""
Sistema di monitoraggio per il cronjob di raccolta dati cripto.
"""

import sys
import os
import time
from datetime import datetime, timedelta

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.core.database import SessionLocal
from app.models.market_data import MarketData

def get_system_status():
    """Ottieni lo stato del sistema."""
    
    db = SessionLocal()
    try:
        # Statistiche generali
        total_records = db.query(MarketData).count()
        unique_symbols = db.query(MarketData.symbol).distinct().count()
        
        # Ultimi aggiornamenti
        latest_data = db.query(MarketData).order_by(
            MarketData.timestamp.desc()
        ).first()
        
        # Dati degli ultimi 5 minuti
        five_min_ago = datetime.now() - timedelta(minutes=5)
        recent_data = db.query(MarketData).filter(
            MarketData.timestamp >= five_min_ago
        ).count()
        
        # Simboli più attivi
        active_symbols = db.query(
            MarketData.symbol,
            db.func.count(MarketData.id).label('count')
        ).filter(
            MarketData.timestamp >= five_min_ago
        ).group_by(MarketData.symbol).order_by(
            db.func.count(MarketData.id).desc()
        ).limit(10).all()
        
        return {
            "total_records": total_records,
            "unique_symbols": unique_symbols,
            "recent_updates": recent_data,
            "latest_data": latest_data,
            "active_symbols": active_symbols
        }
        
    finally:
        db.close()

def monitor_cronjob():
    """Monitora il cronjob."""
    
    print("📊 Monitor Cronjob Raccolta Dati Cripto")
    print("=" * 60)
    
    while True:
        try:
            status = get_system_status()
            
            # Pulisci lo schermo
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print("📊 Monitor Cronjob Raccolta Dati Cripto")
            print("=" * 60)
            print(f"🕐 Ultimo aggiornamento: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # Statistiche generali
            print("📈 STATISTICHE GENERALI:")
            print(f"   📊 Record totali: {status['total_records']:,}")
            print(f"   🏷️  Simboli unici: {status['unique_symbols']}")
            print(f"   🔄 Aggiornamenti ultimi 5 min: {status['recent_updates']}")
            print()
            
            # Ultimo dato
            if status['latest_data']:
                latest = status['latest_data']
                print("💎 ULTIMO DATO:")
                print(f"   🏷️  Simbolo: {latest.symbol}")
                print(f"   💰 Prezzo: ${latest.close_price:,.2f}")
                print(f"   📊 Volume: {latest.volume:,.2f}")
                print(f"   ⏰ Timestamp: {latest.timestamp}")
                print()
            
            # Simboli più attivi
            if status['active_symbols']:
                print("🔥 SIMBOLI PIÙ ATTIVI (ultimi 5 min):")
                for symbol, count in status['active_symbols']:
                    print(f"   • {symbol}: {count} aggiornamenti")
                print()
            
            # Stato del cronjob
            if status['recent_updates'] > 0:
                print("✅ CRONJOB: Attivo e funzionante")
            else:
                print("⚠️  CRONJOB: Nessun aggiornamento recente")
            
            print("\n⏹️  Premi Ctrl+C per fermare il monitor")
            
            # Aspetta 30 secondi
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n🛑 Monitor fermato")
            break
        except Exception as e:
            print(f"❌ Errore nel monitor: {e}")
            time.sleep(30)

if __name__ == "__main__":
    monitor_cronjob()

