#!/usr/bin/env python3
"""
Script per riempire gap nei dati di mercato in modo selettivo.
Permette di scegliere quali simboli riempire.
"""

import asyncio
import sys
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

def find_gaps(db, symbol: str, timeframe: str) -> List[Tuple[datetime, datetime]]:
    """Trova tutti i gap nei dati per un simbolo e timeframe."""
    
    records = db.query(MarketData.timestamp).filter(
        MarketData.symbol == symbol,
        MarketData.timeframe == timeframe
    ).order_by(MarketData.timestamp).all()
    
    if not records or len(records) < 2:
        return []
    
    timestamps = [r[0] for r in records]
    delta = get_timeframe_delta(timeframe)
    gaps = []
    
    for i in range(len(timestamps) - 1):
        current = timestamps[i]
        next_expected = current + delta
        actual_next = timestamps[i + 1]
        
        if actual_next > next_expected:
            gap_start = next_expected
            gap_end = actual_next - delta
            gaps.append((gap_start, gap_end))
    
    return gaps

async def fill_gap(adapter, db, symbol: str, timeframe: str, start: datetime, end: datetime, progress_callback=None) -> int:
    """Riempie un gap specifico scaricando i dati da Binance."""
    
    inserted = 0
    max_candles = 1000
    delta = get_timeframe_delta(timeframe)
    current_start = start
    
    while current_start <= end:
        time_diff = end - current_start
        candles_needed = min(int(time_diff / delta) + 1, max_candles)
        
        if candles_needed <= 0:
            break
        
        try:
            start_ms = int(current_start.timestamp() * 1000)
            klines = adapter.get_historical_klines(
                symbol, 
                timeframe, 
                start_time=start_ms,
                limit=candles_needed
            )
            
            if not klines:
                break
            
            # Inserisci con retry logic per gestire database lock
            for kline in klines:
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
            
            # Commit con retry per database lock
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    db.commit()
                    break
                except Exception as commit_error:
                    if "database is locked" in str(commit_error) and attempt < max_retries - 1:
                        db.rollback()
                        await asyncio.sleep(1)  # Attendi 1 secondo prima di riprovare
                        continue
                    else:
                        db.rollback()
                        raise
            
            last_timestamp = klines[-1]["timestamp"]
            current_start = last_timestamp + delta
            
            if progress_callback:
                progress_callback(inserted)
            
            await asyncio.sleep(0.3)  # Rate limiting + tempo per rilasciare lock
            
        except Exception as e:
            logger.error(f"Errore: {e}")
            db.rollback()
            break
    
    return inserted

async def fill_gaps_for_symbols(symbols: List[str], timeframes: List[str] = None):
    """Riempie i gap per i simboli specificati."""
    
    if timeframes is None:
        timeframes = ['1m', '5m', '15m', '1h']
    
    print("="*80)
    print("🔄 RIEMPIMENTO GAP SELETTIVO")
    print("="*80)
    print(f"\n📊 Simboli: {', '.join(symbols)}")
    print(f"⏰ Timeframes: {', '.join(timeframes)}")
    
    db = SessionLocal()
    adapter = get_exchange_adapter("binance")
    adapter.set_sandbox(False)
    
    try:
        total_inserted = 0
        
        for symbol in symbols:
            print(f"\n{'='*80}")
            print(f"📈 {symbol}")
            print(f"{'='*80}")
            
            for timeframe in timeframes:
                # Verifica se ci sono dati
                count = db.query(func.count(MarketData.id)).filter(
                    MarketData.symbol == symbol,
                    MarketData.timeframe == timeframe
                ).scalar()
                
                if count == 0:
                    print(f"   {timeframe:5} - Nessun dato presente, skip")
                    continue
                
                # Trova gap
                gaps = find_gaps(db, symbol, timeframe)
                
                if not gaps:
                    print(f"   {timeframe:5} - ✅ Completo (nessun gap)")
                    continue
                
                # Calcola candele mancanti
                delta = get_timeframe_delta(timeframe)
                missing = sum([int((end - start) / delta) + 1 for start, end in gaps])
                
                print(f"   {timeframe:5} - {len(gaps)} gap, ~{missing} candele mancanti")
                
                # Riempi gap
                for i, (gap_start, gap_end) in enumerate(gaps, 1):
                    print(f"      Gap {i}/{len(gaps)}: {gap_start.strftime('%Y-%m-%d %H:%M')} → {gap_end.strftime('%Y-%m-%d %H:%M')}", end=" ")
                    
                    inserted = await fill_gap(adapter, db, symbol, timeframe, gap_start, gap_end)
                    total_inserted += inserted
                    
                    if inserted > 0:
                        print(f"✅ {inserted} candele")
                    else:
                        print(f"⚠️  0 candele")
        
        print(f"\n{'='*80}")
        print(f"✅ COMPLETATO: {total_inserted} candele totali inserite")
        print(f"{'='*80}")
        
    finally:
        db.close()

async def main():
    """Main function con menu interattivo."""
    
    print("="*80)
    print("🔄 RIEMPIMENTO GAP NEI DATI")
    print("="*80)
    
    print("\nOpzioni:")
    print("1. Simboli principali (BTC, ETH, BNB, XRP, ADA)")
    print("2. Top 10 simboli")
    print("3. Tutti i simboli")
    print("4. Simboli custom")
    
    # Se eseguito con argomenti, usa quelli
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("\nScegli opzione (1-4): ").strip()
    
    if choice == "1":
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"]
        timeframes = ["1m", "5m", "15m", "1h"]
    elif choice == "2":
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", 
                   "DOGEUSDT", "SOLUSDT", "DOTUSDT", "LINKUSDT", "AVAXUSDT"]
        timeframes = ["1m", "5m", "15m", "1h"]
    elif choice == "3":
        # Ottieni tutti i simboli dal database
        db = SessionLocal()
        symbols = db.query(MarketData.symbol).distinct().all()
        symbols = [s[0] for s in symbols]
        db.close()
        timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
    elif choice == "4":
        symbols_input = input("Inserisci simboli (separati da virgola): ").strip()
        symbols = [s.strip().upper() for s in symbols_input.split(",")]
        timeframes = ["1m", "5m", "15m", "1h"]
    else:
        print("❌ Opzione non valida")
        return
    
    await fill_gaps_for_symbols(symbols, timeframes)

if __name__ == "__main__":
    add_historical_method()
    asyncio.run(main())

