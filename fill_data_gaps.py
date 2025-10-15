#!/usr/bin/env python3
"""
Script per riempire tutti i gap nei dati di mercato tra il primo e l'ultimo record.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Tuple
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.market_data import MarketData
from app.services.exchange_adapters import get_exchange_adapter
from app.core.logging import get_logger

logger = get_logger(__name__)

# Mapping timeframe -> minuti
TIMEFRAME_MINUTES = {
    '1m': 1,
    '5m': 5,
    '15m': 15,
    '30m': 30,
    '1h': 60,
    '4h': 240,
    '1d': 1440,
    '1w': 10080
}

def get_timeframe_delta(timeframe: str) -> timedelta:
    """Ottiene il timedelta per un timeframe."""
    minutes = TIMEFRAME_MINUTES.get(timeframe, 1)
    return timedelta(minutes=minutes)

def find_gaps(db, symbol: str, timeframe: str) -> List[Tuple[datetime, datetime]]:
    """Trova tutti i gap nei dati per un simbolo e timeframe."""
    
    # Ottieni tutti i timestamp ordinati
    records = db.query(MarketData.timestamp).filter(
        MarketData.symbol == symbol,
        MarketData.timeframe == timeframe
    ).order_by(MarketData.timestamp).all()
    
    if not records or len(records) < 2:
        return []
    
    timestamps = [r[0] for r in records]
    delta = get_timeframe_delta(timeframe)
    gaps = []
    
    # Trova i gap
    for i in range(len(timestamps) - 1):
        current = timestamps[i]
        next_expected = current + delta
        actual_next = timestamps[i + 1]
        
        # Se c'è un gap maggiore di un periodo
        if actual_next > next_expected:
            gap_start = next_expected
            gap_end = actual_next - delta
            gaps.append((gap_start, gap_end))
    
    return gaps

async def fill_gap(adapter, db, symbol: str, timeframe: str, start: datetime, end: datetime) -> int:
    """Riempie un gap specifico scaricando i dati da Binance."""
    
    inserted = 0
    
    # Binance limita a 1000 candele per chiamata
    max_candles = 1000
    delta = get_timeframe_delta(timeframe)
    
    current_start = start
    
    while current_start <= end:
        # Calcola quante candele servono
        time_diff = end - current_start
        candles_needed = min(int(time_diff / delta) + 1, max_candles)
        
        if candles_needed <= 0:
            break
        
        try:
            # Scarica i dati
            # Converti datetime in millisecondi per Binance
            start_ms = int(current_start.timestamp() * 1000)
            
            # Usa get_klines con startTime
            klines = adapter.get_historical_klines(
                symbol, 
                timeframe, 
                start_time=start_ms,
                limit=candles_needed
            )
            
            if not klines:
                logger.warning(f"Nessun dato ricevuto per {symbol} {timeframe} da {current_start}")
                break
            
            # Inserisci nel database
            for kline in klines:
                # Verifica se esiste già
                existing = db.query(MarketData).filter(
                    MarketData.symbol == symbol,
                    MarketData.timeframe == timeframe,
                    MarketData.timestamp == kline["timestamp"]
                ).first()
                
                if not existing:
                    market_data = MarketData(
                        symbol=symbol,
                        timeframe=timeframe,
                        open_price=kline["open"],
                        high_price=kline["high"],
                        low_price=kline["low"],
                        close_price=kline["close"],
                        volume=kline["volume"],
                        quote_volume=kline.get("quote_volume", 0),
                        trades_count=kline.get("trades_count", 0),
                        taker_buy_volume=kline.get("taker_buy_volume", 0),
                        taker_buy_quote_volume=kline.get("taker_buy_quote_volume", 0),
                        timestamp=kline["timestamp"]
                    )
                    db.add(market_data)
                    inserted += 1
            
            db.commit()
            
            # Aggiorna per la prossima iterazione
            last_timestamp = klines[-1]["timestamp"]
            current_start = last_timestamp + delta
            
            # Pausa per rispettare i rate limits
            await asyncio.sleep(0.2)
            
        except Exception as e:
            logger.error(f"Errore durante il riempimento gap {symbol} {timeframe}: {e}")
            break
    
    return inserted

async def fill_all_gaps():
    """Riempie tutti i gap trovati nel database."""
    
    print("="*80)
    print("🔄 RIEMPIMENTO GAP NEI DATI DI MERCATO")
    print("="*80)
    
    db = SessionLocal()
    adapter = get_exchange_adapter("binance")
    adapter.set_sandbox(False)  # Usa mainnet
    
    try:
        # 1. Ottieni tutti i simboli e timeframe unici
        print("\n1️⃣  ANALISI DATABASE")
        print("-"*80)
        
        symbols_timeframes = db.query(
            MarketData.symbol,
            MarketData.timeframe
        ).distinct().all()
        
        print(f"   Trovati {len(symbols_timeframes)} combinazioni simbolo/timeframe")
        
        # 2. Per ogni combinazione, trova i gap
        print("\n2️⃣  RICERCA GAP")
        print("-"*80)
        
        all_gaps = []
        
        for symbol, timeframe in symbols_timeframes:
            # Ottieni primo e ultimo timestamp
            first = db.query(func.min(MarketData.timestamp)).filter(
                MarketData.symbol == symbol,
                MarketData.timeframe == timeframe
            ).scalar()
            
            last = db.query(func.max(MarketData.timestamp)).filter(
                MarketData.symbol == symbol,
                MarketData.timeframe == timeframe
            ).scalar()
            
            count = db.query(func.count(MarketData.id)).filter(
                MarketData.symbol == symbol,
                MarketData.timeframe == timeframe
            ).scalar()
            
            # Calcola quante candele dovrebbero esserci
            if first and last:
                delta = get_timeframe_delta(timeframe)
                expected_candles = int((last - first) / delta) + 1
                missing = expected_candles - count
                
                if missing > 0:
                    gaps = find_gaps(db, symbol, timeframe)
                    if gaps:
                        all_gaps.append((symbol, timeframe, gaps, missing))
                        print(f"   {symbol:15} {timeframe:5} - {len(gaps)} gap, ~{missing} candele mancanti")
        
        if not all_gaps:
            print("   ✅ Nessun gap trovato! I dati sono completi.")
            return
        
        print(f"\n   Totale: {len(all_gaps)} simboli/timeframe con gap")
        
        # 3. Riempi i gap
        print("\n3️⃣  RIEMPIMENTO GAP")
        print("-"*80)
        
        total_inserted = 0
        
        for symbol, timeframe, gaps, missing in all_gaps:
            print(f"\n   📊 {symbol} {timeframe} - {len(gaps)} gap da riempire")
            
            for i, (gap_start, gap_end) in enumerate(gaps, 1):
                gap_duration = gap_end - gap_start
                print(f"      Gap {i}/{len(gaps)}: {gap_start} → {gap_end} ({gap_duration})")
                
                inserted = await fill_gap(adapter, db, symbol, timeframe, gap_start, gap_end)
                total_inserted += inserted
                
                if inserted > 0:
                    print(f"      ✅ Inserite {inserted} candele")
                else:
                    print(f"      ⚠️  Nessuna candela inserita")
        
        print("\n" + "="*80)
        print(f"✅ COMPLETATO: {total_inserted} candele inserite")
        print("="*80)
        
        # 4. Verifica finale
        print("\n4️⃣  VERIFICA FINALE")
        print("-"*80)
        
        for symbol, timeframe, _, _ in all_gaps[:5]:  # Primi 5
            remaining_gaps = find_gaps(db, symbol, timeframe)
            status = "✅ COMPLETO" if not remaining_gaps else f"⚠️  {len(remaining_gaps)} gap rimasti"
            print(f"   {symbol:15} {timeframe:5} - {status}")
        
    finally:
        db.close()

# Aggiungi metodo helper all'adapter se non esiste
def add_historical_method():
    """Aggiunge il metodo get_historical_klines se non esiste."""
    from app.services.exchange_adapters.binance import BinanceAdapter
    
    if not hasattr(BinanceAdapter, 'get_historical_klines'):
        def get_historical_klines(self, symbol: str, interval: str, start_time: int = None, limit: int = 1000):
            """Get historical klines with start_time."""
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': min(limit, 1000)
            }
            
            if start_time:
                params['startTime'] = start_time
            
            data = self._make_request('GET', '/api/v3/klines', params)
            
            klines = []
            for candle in data:
                klines.append({
                    'timestamp': datetime.fromtimestamp(candle[0] / 1000),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5]),
                    'quote_volume': float(candle[7]),
                    'trades_count': int(candle[8]),
                    'taker_buy_volume': float(candle[9]),
                    'taker_buy_quote_volume': float(candle[10])
                })
            
            return klines
        
        BinanceAdapter.get_historical_klines = get_historical_klines

if __name__ == "__main__":
    print("🚀 Inizio riempimento gap nei dati...\n")
    
    # Aggiungi il metodo helper
    add_historical_method()
    
    # Esegui il riempimento
    asyncio.run(fill_all_gaps())
    
    print("\n✨ Script completato!")

