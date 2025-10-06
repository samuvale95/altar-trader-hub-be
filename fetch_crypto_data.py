#!/usr/bin/env python3
"""
Script per scaricare dati cripto aggiornati dal web tramite API.
"""

import requests
import json
import time
from datetime import datetime

class CryptoDataFetcher:
    """Classe per scaricare dati cripto aggiornati."""
    
    def __init__(self, base_url="http://localhost:8001", token=None):
        self.base_url = base_url
        self.token = token
        self.headers = {
            "Content-Type": "application/json"
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
    
    def start_data_collection(self, symbols=None, timeframes=None):
        """Avvia la raccolta dati dal web."""
        
        if symbols is None:
            symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOGEUSDT", "SOLUSDT"]
        
        if timeframes is None:
            timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
        
        url = f"{self.base_url}/api/v1/data-collector/start"
        data = {
            "symbols": symbols,
            "timeframes": timeframes
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Errore nell'avvio raccolta dati: {e}")
            return None
    
    def get_collection_status(self):
        """Ottieni lo stato della raccolta dati."""
        
        url = f"{self.base_url}/api/v1/data-collector/status"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Errore nel recupero stato: {e}")
            return None
    
    def get_latest_prices(self):
        """Ottieni i prezzi più recenti."""
        
        url = f"{self.base_url}/api/v1/data-collector/latest-prices"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Errore nel recupero prezzi: {e}")
            return None
    
    def get_candlestick_data(self, symbol, timeframe="1h", limit=1000):
        """Ottieni dati candlestick aggiornati."""
        
        url = f"{self.base_url}/api/v1/charts/candlestick/{symbol}"
        params = {
            "timeframe": timeframe,
            "limit": limit
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Errore nel recupero dati candlestick: {e}")
            return None
    
    def get_technical_indicators(self, symbol, timeframe="1h", limit=1000):
        """Ottieni indicatori tecnici aggiornati."""
        
        url = f"{self.base_url}/api/v1/charts/indicators/{symbol}/all"
        params = {
            "timeframe": timeframe,
            "limit": limit
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Errore nel recupero indicatori: {e}")
            return None
    
    def get_available_symbols(self):
        """Ottieni i simboli disponibili."""
        
        url = f"{self.base_url}/api/v1/charts/available-symbols"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Errore nel recupero simboli: {e}")
            return None

def main():
    """Funzione principale."""
    
    print("🚀 Download Dati Cripto dal Web")
    print("=" * 50)
    
    # Inizializza il fetcher
    fetcher = CryptoDataFetcher()
    
    # 1. Avvia raccolta dati
    print("🔄 Avvio raccolta dati dal web...")
    result = fetcher.start_data_collection()
    if result:
        print("✅ Raccolta dati avviata")
    else:
        print("❌ Errore nell'avvio raccolta dati")
    
    # 2. Verifica stato
    print("\n📊 Stato raccolta dati:")
    status = fetcher.get_collection_status()
    if status:
        print(f"   Status: {status}")
    else:
        print("   ❌ Errore nel recupero stato")
    
    # 3. Ottieni prezzi recenti
    print("\n💰 Prezzi più recenti:")
    prices = fetcher.get_latest_prices()
    if prices:
        print(f"   Prezzi: {prices}")
    else:
        print("   ❌ Errore nel recupero prezzi")
    
    # 4. Ottieni simboli disponibili
    print("\n🔍 Simboli disponibili:")
    symbols = fetcher.get_available_symbols()
    if symbols:
        print(f"   Simboli: {len(symbols.get('symbols', []))} trovati")
        for symbol in symbols.get('symbols', [])[:10]:  # Mostra primi 10
            print(f"   • {symbol}")
    else:
        print("   ❌ Errore nel recupero simboli")
    
    # 5. Ottieni dati specifici
    print("\n📈 Dati BTCUSDT:")
    btc_data = fetcher.get_candlestick_data("BTCUSDT", "1h", 100)
    if btc_data:
        print(f"   Dati candlestick: {btc_data.get('count', 0)} record")
        if btc_data.get('data'):
            latest = btc_data['data'][-1]
            print(f"   Ultimo prezzo: ${latest.get('close', 0):,.2f}")
    else:
        print("   ❌ Errore nel recupero dati BTC")

if __name__ == "__main__":
    main()
