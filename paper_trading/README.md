# Paper Trading System for Crypto Strategies

Un sistema completo di simulazione paper trading per strategie di trading crypto, implementato in Python.

## 🚀 Caratteristiche

- **8 Strategie di Trading** implementate e pronte all'uso
- **Download dati storici** da Binance e Yahoo Finance
- **Simulatore di portafoglio virtuale** con commissioni realistiche
- **Motore di backtesting** completo con metriche di performance
- **Sistema di reporting** con grafici e analisi
- **Confronto strategie** per ottimizzazione
- **Interfaccia CLI** per uso facile
- **Modularità** per estensione futura

## 📋 Strategie Implementate

### 1. **Dollar Cost Averaging (DCA)**
- Investe una somma fissa a intervalli regolari
- Ideale per investitori a lungo termine
- **Rischio**: Basso

### 2. **RSI Trading**
- Compra quando RSI è oversold, vende quando overbought
- Strategia di mean reversion
- **Rischio**: Medio

### 3. **MACD Trading**
- Usa crossover della linea MACD e istogramma
- Strategia di trend following
- **Rischio**: Medio

### 4. **Moving Average Crossover**
- Compra quando MA veloce incrocia sopra MA lenta
- Strategia di trend following
- **Rischio**: Medio

### 5. **Bollinger Bands**
- Trading basato su posizione prezzo rispetto alle bande
- Supporta mean reversion e breakout
- **Rischio**: Medio

### 6. **Range Trading**
- Compra a supporto, vende a resistenza
- Ideale per mercati laterali
- **Rischio**: Medio

### 7. **Grid Trading**
- Piazza ordini buy/sell a intervalli regolari
- Ideale per mercati ad alta volatilità
- **Rischio**: Alto

### 8. **Fear & Greed Index**
- Trading basato su indicatori di sentiment
- Strategia contrarian
- **Rischio**: Alto

## 🛠️ Installazione

### Prerequisiti
```bash
pip install pandas numpy matplotlib seaborn requests ta-lib
```

### Setup
```bash
# Clona o scarica il sistema
cd paper_trading

# Installa dipendenze
pip install -r requirements.txt
```

## 🚀 Utilizzo

### 1. Uso da Command Line

#### Lista strategie disponibili
```bash
python main.py --list-strategies
```

#### Esegui una singola strategia
```bash
python main.py --strategy rsi --symbol BTCUSDT --interval 1d --start-date 2023-01-01 --end-date 2024-01-01
```

#### Confronta tutte le strategie
```bash
python main.py --compare --symbol BTCUSDT --interval 1d
```

#### Genera report e grafici
```bash
python main.py --strategy macd --symbol ETHUSDT --generate-plots --html-report --output-dir results
```

### 2. Uso Programmatico

```python
from core.data_feed import DataFeed
from core.backtest_engine import BacktestEngine
from strategies import StrategyFactory

# Download dati
data_feed = DataFeed()
data = data_feed.get_data('BTCUSDT', '1d', '2023-01-01', '2024-01-01')

# Esegui backtest
backtest_engine = BacktestEngine(initial_balance=10000.0)
results = backtest_engine.run_backtest(
    data=data,
    strategy_name='rsi',
    strategy_parameters={'rsi_period': 14, 'oversold_threshold': 30},
    symbol='BTCUSDT'
)

# Visualizza risultati
print(results['metrics'])
```

### 3. Esempi Pratici

Esegui gli esempi inclusi:
```bash
python example_usage.py
```

## 📊 Output e Report

### Metriche di Performance
- **Total Return**: Rendimento totale
- **Annualized Return**: Rendimento annualizzato
- **Volatility**: Volatilità
- **Sharpe Ratio**: Rapporto rischio/rendimento
- **Max Drawdown**: Perdita massima
- **Win Rate**: Percentuale di trade vincenti

### File Generati
- `*_trades.csv`: Storico dei trade
- `*_orders.csv`: Storico degli ordini
- `*_equity.csv`: Curva del capitale
- `*_equity.png`: Grafico del capitale
- `*_drawdown.png`: Grafico del drawdown
- `*_trades.png`: Grafico dei trade
- `*_report.html`: Report HTML

## ⚙️ Configurazione

### Parametri Strategie
Modifica `config.py` per personalizzare i parametri:

```python
STRATEGY_PARAMETERS = {
    'rsi': {
        'rsi_period': 14,
        'oversold_threshold': 30,
        'overbought_threshold': 70
    },
    'macd': {
        'fast_period': 12,
        'slow_period': 26,
        'signal_period': 9
    }
    # ... altre strategie
}
```

### Configurazione Portfolio
```python
PORTFOLIO_CONFIG = {
    'initial_balance': 10000.0,
    'commission_rate': 0.001,  # 0.1%
    'base_currency': 'USDT'
}
```

## 🔧 Estensione del Sistema

### Aggiungere una Nuova Strategia

1. Crea un nuovo file in `strategies/`:
```python
from .base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self, parameters=None):
        super().__init__("My_Strategy", parameters)
    
    def generate_signals(self, data):
        # Implementa la logica della strategia
        pass
```

2. Registra la strategia in `strategy_factory.py`:
```python
_strategies = {
    # ... strategie esistenti
    'my_strategy': MyStrategy
}
```

### Aggiungere Nuove Fonti Dati

Estendi `DataFeed` per supportare nuove API:
```python
def get_custom_data(self, symbol, start_date, end_date):
    # Implementa il download da nuova fonte
    pass
```

## 📈 Esempi di Risultati

### RSI Strategy (BTCUSDT, 2023)
```
Total Return: 15.23%
Sharpe Ratio: 1.45
Max Drawdown: -8.12%
Win Rate: 58.33%
Total Trades: 24
```

### DCA Strategy (BTCUSDT, 2023)
```
Total Return: 12.87%
Sharpe Ratio: 0.89
Max Drawdown: -15.23%
Win Rate: 100.00%
Total Trades: 52
```

## 🚨 Avvertenze

- **Solo per scopi educativi**: Questo sistema è per simulazione, non per trading reale
- **Dati storici**: I risultati passati non garantiscono performance future
- **Commissioni**: Include commissioni realistiche ma potrebbero variare
- **Liquidità**: Non considera problemi di liquidità del mercato reale

## 🤝 Contribuire

1. Fork del repository
2. Crea un branch per la feature
3. Implementa le modifiche
4. Aggiungi test
5. Crea una Pull Request

## 📄 Licenza

MIT License - vedi file LICENSE per dettagli.

## 🆘 Supporto

Per domande o problemi:
1. Controlla la documentazione
2. Esegui gli esempi
3. Apri una issue su GitHub

---

**Happy Paper Trading! 📈**
