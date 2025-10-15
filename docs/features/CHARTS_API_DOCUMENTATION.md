# Charts API Documentation

This document describes the comprehensive Charts API endpoints for creating price charts and technical analysis data for the frontend.

## Overview

The Charts API provides endpoints for:
- **Candlestick Charts**: OHLCV data for candlestick visualization
- **Price History**: Line chart data for price trends
- **Volume Charts**: Volume and trading activity data
- **Technical Indicators**: RSI, MACD, Bollinger Bands, Moving Averages, etc.
- **Chart Summary**: Current price, 24h change, volume statistics
- **Comprehensive Data**: All chart data in a single request

## Base URL

```
http://localhost:8000/api/v1/charts
```

## Authentication

All endpoints require authentication. Include the Bearer token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

## Endpoints

### 1. Available Symbols

Get list of available trading symbols with data.

**Endpoint:** `GET /available-symbols`

**Response:**
```json
{
  "symbols": [
    {
      "symbol": "BTCUSDT",
      "data_points": 15000,
      "latest_price": 45000.50,
      "latest_timestamp": "2024-01-15T10:30:00Z",
      "price_change_24h": 1250.75,
      "price_change_percentage_24h": 2.85
    }
  ],
  "total_symbols": 50
}
```

### 2. Available Timeframes

Get available timeframes for a specific symbol.

**Endpoint:** `GET /timeframes/{symbol}`

**Parameters:**
- `symbol` (path): Trading symbol (e.g., BTCUSDT)

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "timeframes": [
    {
      "timeframe": "1m",
      "data_points": 100000,
      "latest_timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "timeframe": "1h",
      "data_points": 8760,
      "latest_timestamp": "2024-01-15T10:00:00Z"
    }
  ],
  "total_timeframes": 6
}
```

### 3. Candlestick Data

Get OHLCV data for candlestick charts.

**Endpoint:** `GET /candlestick/{symbol}`

**Parameters:**
- `symbol` (path): Trading symbol
- `timeframe` (query): Timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)
- `limit` (query): Number of candles (max 2000, default 1000)
- `start_date` (query): Start date in ISO format (optional)
- `end_date` (query): End date in ISO format (optional)

**Example Request:**
```
GET /candlestick/BTCUSDT?timeframe=1h&limit=100&start_date=2024-01-01T00:00:00Z
```

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "data": [
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "open": 44800.50,
      "high": 45100.25,
      "low": 44750.00,
      "close": 45000.50,
      "volume": 125.75
    }
  ],
  "count": 100,
  "start_time": "2024-01-15T10:00:00Z",
  "end_time": "2024-01-15T10:00:00Z"
}
```

### 4. Price History

Get price history data for line charts.

**Endpoint:** `GET /price-history/{symbol}`

**Parameters:** Same as candlestick data

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "prices": [
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "price": 45000.50,
      "volume": 125.75,
      "open": 44800.50,
      "high": 45100.25,
      "low": 44750.00,
      "close": 45000.50
    }
  ],
  "count": 100,
  "start_time": "2024-01-15T10:00:00Z",
  "end_time": "2024-01-15T10:00:00Z"
}
```

### 5. Volume Data

Get volume and trading activity data.

**Endpoint:** `GET /volume/{symbol}`

**Parameters:** Same as candlestick data

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "data": [
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "volume": 125.75,
      "quote_volume": 5650000.25,
      "trades_count": 1250
    }
  ],
  "count": 100
}
```

### 6. Technical Indicators

Get specific technical indicator data.

**Endpoint:** `GET /indicators/{symbol}/{indicator_name}`

**Parameters:**
- `symbol` (path): Trading symbol
- `indicator_name` (path): Indicator name (RSI, MACD, BB, SMA_20, SMA_50, EMA_12, EMA_26, STOCH, ATR)
- `timeframe` (query): Timeframe
- `limit` (query): Number of data points (max 2000)
- `start_date` (query): Start date (optional)
- `end_date` (query): End date (optional)

**Example Request:**
```
GET /indicators/BTCUSDT/RSI?timeframe=1h&limit=100
```

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "indicator_name": "RSI",
  "data": [
    {
      "timestamp": "2024-01-15T10:00:00Z",
      "value": 65.5,
      "signal": "hold",
      "signal_strength": 0.31
    }
  ],
  "count": 100,
  "overbought_level": 70,
  "oversold_level": 30
}
```

### 7. All Technical Indicators

Get all available technical indicators for a symbol.

**Endpoint:** `GET /indicators/{symbol}/all`

**Parameters:**
- `symbol` (path): Trading symbol
- `timeframe` (query): Timeframe
- `limit` (query): Number of data points

**Response:**
```json
{
  "RSI": {
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "indicator_name": "RSI",
    "data": [...],
    "count": 100,
    "overbought_level": 70,
    "oversold_level": 30
  },
  "MACD": {
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "indicator_name": "MACD",
    "data": [...],
    "count": 100
  }
}
```

### 8. Chart Summary

Get current price and 24h statistics.

**Endpoint:** `GET /summary/{symbol}`

**Parameters:**
- `symbol` (path): Trading symbol
- `timeframe` (query): Timeframe

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "current_price": 45000.50,
  "price_change": 1250.75,
  "price_change_percentage": 2.85,
  "volume_24h": 15000.25,
  "high_24h": 45500.00,
  "low_24h": 44200.00,
  "open_24h": 43750.00,
  "close_24h": 45000.50,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

### 9. Comprehensive Chart Data

Get all chart data in a single request.

**Endpoint:** `POST /comprehensive/{symbol}`

**Request Body:**
```json
{
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "limit": 1000,
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-15T23:59:59Z",
  "indicators": ["RSI", "MACD", "SMA_20", "SMA_50"]
}
```

**Response:**
```json
{
  "candlestick": {
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "data": [...],
    "count": 1000,
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2024-01-15T23:00:00Z"
  },
  "volume": {
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "data": [...],
    "count": 1000
  },
  "summary": {
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "current_price": 45000.50,
    "price_change": 1250.75,
    "price_change_percentage": 2.85,
    "volume_24h": 15000.25,
    "high_24h": 45500.00,
    "low_24h": 44200.00,
    "open_24h": 43750.00,
    "close_24h": 45000.50,
    "last_updated": "2024-01-15T10:30:00Z"
  },
  "indicators": {
    "RSI": {...},
    "MACD": {...},
    "SMA_20": {...},
    "SMA_50": {...}
  },
  "metadata": {
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "requested_indicators": ["RSI", "MACD", "SMA_20", "SMA_50"],
    "available_indicators": ["RSI", "MACD", "SMA_20", "SMA_50"],
    "data_points": 1000
  }
}
```

## Available Technical Indicators

| Indicator | Description | Parameters |
|-----------|-------------|------------|
| RSI | Relative Strength Index | Period: 14, Overbought: 70, Oversold: 30 |
| MACD | Moving Average Convergence Divergence | Fast: 12, Slow: 26, Signal: 9 |
| BB | Bollinger Bands | Period: 20, Std Dev: 2.0 |
| SMA_20 | Simple Moving Average | Period: 20 |
| SMA_50 | Simple Moving Average | Period: 50 |
| EMA_12 | Exponential Moving Average | Period: 12 |
| EMA_26 | Exponential Moving Average | Period: 26 |
| STOCH | Stochastic Oscillator | K: 14, D: 3, Overbought: 80, Oversold: 20 |
| ATR | Average True Range | Period: 14 |

## Error Responses

### 404 Not Found
```json
{
  "detail": "No data found for BTCUSDT 1h"
}
```

### 400 Bad Request
```json
{
  "detail": "Timeframe must be one of: ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w']"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to get candlestick data: Database connection error"
}
```

## Frontend Integration Examples

### React/JavaScript Example

```javascript
// Get candlestick data
const getCandlestickData = async (symbol, timeframe, limit = 1000) => {
  const response = await fetch(
    `/api/v1/charts/candlestick/${symbol}?timeframe=${timeframe}&limit=${limit}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  return await response.json();
};

// Get comprehensive chart data
const getComprehensiveData = async (symbol, timeframe, indicators = []) => {
  const response = await fetch(`/api/v1/charts/comprehensive/${symbol}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      symbol,
      timeframe,
      limit: 1000,
      indicators
    })
  });
  return await response.json();
};
```

### Chart.js Integration Example

```javascript
// Prepare data for Chart.js
const prepareCandlestickData = (chartData) => {
  return {
    labels: chartData.data.map(d => d.timestamp),
    datasets: [{
      label: 'Price',
      data: chartData.data.map(d => ({
        x: d.timestamp,
        o: d.open,
        h: d.high,
        l: d.low,
        c: d.close
      })),
      type: 'candlestick'
    }]
  };
};

// Create candlestick chart
const createChart = (chartData) => {
  const ctx = document.getElementById('chart').getContext('2d');
  new Chart(ctx, {
    type: 'candlestick',
    data: prepareCandlestickData(chartData),
    options: {
      responsive: true,
      scales: {
        x: {
          type: 'time',
          time: {
            unit: 'hour'
          }
        },
        y: {
          beginAtZero: false
        }
      }
    }
  });
};
```

## Testing

Run the test script to verify all endpoints:

```bash
python test_charts_api.py
```

This will test all chart API endpoints and provide detailed output about their functionality.

## Performance Considerations

- **Limit**: Maximum 2000 data points per request
- **Caching**: Consider implementing client-side caching for frequently accessed data
- **Pagination**: Use date ranges to paginate through large datasets
- **Real-time**: Consider WebSocket connections for real-time updates

## Rate Limiting

- Standard rate limiting applies to all endpoints
- Consider implementing exponential backoff for retry logic
- Monitor response times for large data requests
