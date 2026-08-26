# Mehta 3/3 NSE Screener — FAST FIX

Run:

```bash
pip install -r requirements.txt
python mehta_screener.py
```

## FAST MODE changes
- Yahoo price history uses larger batches and Yahoo's internal threads.
- Yahoo retries reduced to 2 and timeouts reduced to avoid long stalls.
- yfinance's noisy ERROR logging is suppressed; unavailable benchmark indexes are handled as warnings.
- Benchmark failures never stop the stock scan.
- PAT is fetched from Screener.in only for stocks that can still reach at least 2/3 or 3/3. Stocks that already score 0 on price + relative strength do not waste a web request on PAT.
- Stock processing uses 16 workers by default.

The current configured NSE source is Nifty 500, so if it returns 500 valid symbols the run screens 500 stocks. `top_n` remains configurable in `config.json`.
