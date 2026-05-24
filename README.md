# SoSo Signal Copilot FULL

A live AI x On-Chain Finance research terminal for Wave 2.

## Data sources

- SoSoValue API for market, ETF, news, and SSI research data.
- SoDEX public API for live spot/perps market data.
- No demo data.
- No fake fallback.
- No CoinGecko.

If the SoSoValue key is invalid, the app clearly shows the real key/API error. SoDEX can still run as the live market/action layer.

## Modules

- Command Center
- Market Intelligence
- Narrative Radar
- Signal Engine
- SSI Builder
- Portfolio Risk
- API Console

## Vercel

Framework Preset: Other  
Build Command: empty  
Output Directory: empty  
Root Directory: ./

Environment Variables:

```env
SOSO_API_KEY=your_private_sosovalue_api_key
SOSO_BASE_URL=https://openapi.sosovalue.com/openapi/v1
```

Optional exact paths from SoSoValue docs:

```env
SOSO_MARKET_PATHS=/real/path
SOSO_ETF_PATHS=/real/path
SOSO_NEWS_PATHS=/real/path
SOSO_SSI_PATHS=/real/path
```

## Test

```txt
/api/health
/api/soso?resource=all
/api/sodex?resource=all
```

Research only. Not financial advice.
