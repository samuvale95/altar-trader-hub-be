"""
Cronjob per scaricare automaticamente i dati delle cripto.
"""

from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timedelta
import asyncio
from typing import List, Optional

from app.core.logging import get_logger
from app.services.data_feeder import data_feeder
from app.services.symbol_manager import symbol_manager
from app.core.database import SessionLocal
from app.models.market_data import MarketData

logger = get_logger(__name__)

# Configurazione Celery
celery_app = Celery('crypto_data_cronjob')
celery_app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    timezone='UTC',
    enable_utc=True,
)

# Simboli principali da monitorare
MAIN_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT", "XRPUSDT",
    "SOLUSDT", "DOGEUSDT", "DOTUSDT", "AVAXUSDT", "LINKUSDT",
    "MATICUSDT", "LTCUSDT", "BCHUSDT", "UNIUSDT", "ATOMUSDT"
]

# Timeframe da monitorare
TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]

@celery_app.task
def collect_crypto_data():
    """Task per raccogliere dati delle cripto."""
    
    logger.info("🔄 Avvio raccolta dati cripto automatica")
    
    try:
        # Avvia la raccolta dati
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            data_feeder.collect_market_data(MAIN_SYMBOLS, TIMEFRAMES)
        )
        
        loop.close()
        
        logger.info(f"✅ Raccolta dati completata: {result}")
        return {"status": "success", "timestamp": datetime.now().isoformat()}
        
    except Exception as e:
        logger.error(f"❌ Errore nella raccolta dati: {e}")
        return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

@celery_app.task
def collect_high_volume_symbols():
    """Task per raccogliere dati dei simboli con alto volume."""
    
    logger.info("📊 Raccolta dati simboli ad alto volume")
    
    try:
        # Ottieni simboli con alto volume
        symbols = symbol_manager.get_top_volume_symbols(limit=50)
        
        if not symbols:
            logger.warning("Nessun simbolo ad alto volume trovato")
            return {"status": "no_data"}
        
        # Avvia la raccolta dati
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            data_feeder.collect_market_data(symbols, ["1m", "5m", "1h"])
        )
        
        loop.close()
        
        logger.info(f"✅ Raccolta simboli ad alto volume completata: {len(symbols)} simboli")
        return {"status": "success", "symbols_count": len(symbols)}
        
    except Exception as e:
        logger.error(f"❌ Errore nella raccolta simboli ad alto volume: {e}")
        return {"status": "error", "error": str(e)}

@celery_app.task
def cleanup_old_data():
    """Task per pulire i dati vecchi."""
    
    logger.info("🧹 Pulizia dati vecchi")
    
    try:
        db = SessionLocal()
        
        # Rimuovi dati più vecchi di 30 giorni
        cutoff_date = datetime.now() - timedelta(days=30)
        
        deleted_count = db.query(MarketData).filter(
            MarketData.timestamp < cutoff_date
        ).delete()
        
        db.commit()
        db.close()
        
        logger.info(f"✅ Pulizia completata: {deleted_count} record rimossi")
        return {"status": "success", "deleted_count": deleted_count}
        
    except Exception as e:
        logger.error(f"❌ Errore nella pulizia dati: {e}")
        return {"status": "error", "error": str(e)}

@celery_app.task
def update_symbol_list():
    """Task per aggiornare la lista dei simboli."""
    
    logger.info("🔄 Aggiornamento lista simboli")
    
    try:
        # Aggiorna la lista dei simboli
        symbol_manager.refresh_symbols()
        
        logger.info("✅ Lista simboli aggiornata")
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"❌ Errore nell'aggiornamento simboli: {e}")
        return {"status": "error", "error": str(e)}

# Configurazione del cronjob
celery_app.conf.beat_schedule = {
    # Raccolta dati principali ogni 5 minuti
    'collect-main-crypto-data': {
        'task': 'app.tasks.crypto_data_cronjob.collect_crypto_data',
        'schedule': crontab(minute='*/5'),  # Ogni 5 minuti
    },
    
    # Raccolta simboli ad alto volume ogni 15 minuti
    'collect-high-volume-symbols': {
        'task': 'app.tasks.crypto_data_cronjob.collect_high_volume_symbols',
        'schedule': crontab(minute='*/15'),  # Ogni 15 minuti
    },
    
    # Aggiornamento lista simboli ogni ora
    'update-symbol-list': {
        'task': 'app.tasks.crypto_data_cronjob.update_symbol_list',
        'schedule': crontab(minute=0),  # Ogni ora
    },
    
    # Pulizia dati vecchi ogni giorno alle 2:00
    'cleanup-old-data': {
        'task': 'app.tasks.crypto_data_cronjob.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0),  # Ogni giorno alle 2:00
    },
}

# Configurazione per esecuzione immediata (per test)
if __name__ == "__main__":
    # Test del cronjob
    print("🧪 Test cronjob raccolta dati cripto")
    
    # Esegui immediatamente
    result = collect_crypto_data.delay()
    print(f"Task avviato: {result.id}")
    
    # Aspetta il risultato
    print("⏳ Attesa completamento...")
    print(f"Risultato: {result.get(timeout=60)}")

