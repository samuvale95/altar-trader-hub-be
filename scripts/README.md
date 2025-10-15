# 📁 Scripts Directory

Questa directory contiene script di utilità e dati per Altar Trader Hub.

## 📝 Note

Gli script di deployment per Raspberry Pi sono stati rimossi.
Per il deployment, ora si usa **Heroku** - vedi [HEROKU_DEPLOYMENT.md](../HEROKU_DEPLOYMENT.md).

## 📋 Contenuto Directory

### Script Python

- **`download_binance_symbols.py`** - Download simboli trading da Binance

### Dati Binance

File CSV e JSON con informazioni sui simboli trading:
- `binance_24hr_ticker.csv`
- `binance_bnb_pairs.csv/json`
- `binance_btc_pairs.csv/json`
- `binance_eth_pairs.csv/json`
- `binance_usdt_pairs.csv/json`

## 🚀 Deployment

Per il deployment dell'applicazione su Heroku, consulta la guida completa:
**[HEROKU_DEPLOYMENT.md](../HEROKU_DEPLOYMENT.md)**

---

**Nota**: Gli script di deployment Raspberry Pi/systemd sono stati rimossi in favore di Heroku.

