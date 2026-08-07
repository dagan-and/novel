# Finance Fetcher

Small Yahoo Finance downloader for Korea stocks, US stocks, and crypto.

## Run

```bash
python3 download_finance.py
```

By default it downloads:

- US stocks: `AAPL`, `MSFT`, `NVDA`, `TSLA`, `AMZN`, `GOOGL`, `META`, `AMD`, `NFLX`, `JPM`
- Korea stocks: `005930.KS`, `000660.KS`, `035420.KS`, `005380.KS`, `051910.KS`, `006400.KS`, `068270.KS`, `373220.KS`, `207940.KS`, `035720.KS`
- Crypto: `BTC-USD`, `ETH-USD`, `SOL-USD`, `XRP-USD`, `BNB-USD`, `ADA-USD`, `DOGE-USD`, `AVAX-USD`, `LINK-USD`, `DOT-USD`

CSV files are saved under `downloads/YYYYMMDD_HHMMSS/`.

## Examples

```bash
python3 download_finance.py --start 2024-01-01 --end 2024-12-31
python3 download_finance.py --groups kr,us
python3 download_finance.py --symbols 005930.KS,AAPL,BTC-USD --start 2024-01-01 --end 2024-01-31
```

## Symbol Notes

- Korea KOSPI examples usually end with `.KS`, such as `005930.KS`.
- Korea KOSDAQ examples usually end with `.KQ`.
- US stocks usually use the ticker directly, such as `AAPL`.
- Crypto on Yahoo usually uses `COIN-USD`, such as `BTC-USD`.
