#!/usr/bin/env python3
import argparse
import csv
import json
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


DEFAULT_SYMBOLS = {
    "us": [
        "AAPL",
        "MSFT",
        "NVDA",
        "TSLA",
        "AMZN",
        "GOOGL",
        "META",
        "AMD",
        "NFLX",
        "JPM",
    ],
    "kr": [
        "005930.KS",
        "000660.KS",
        "035420.KS",
        "005380.KS",
        "051910.KS",
        "006400.KS",
        "068270.KS",
        "373220.KS",
        "207940.KS",
        "035720.KS",
    ],
    "crypto": [
        "BTC-USD",
        "ETH-USD",
        "SOL-USD",
        "XRP-USD",
        "BNB-USD",
        "ADA-USD",
        "DOGE-USD",
        "AVAX-USD",
        "LINK-USD",
        "DOT-USD",
    ],
}


CSV_HEADER = ["Ticker", "Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download Korea stocks, US stocks, and crypto OHLCV data from Yahoo Finance."
    )
    parser.add_argument("--start", default="2024-01-01", help="Start date, YYYY-MM-DD.")
    parser.add_argument("--end", default=str(date.today()), help="End date, YYYY-MM-DD.")
    parser.add_argument(
        "--groups",
        default="us,kr,crypto",
        help="Comma-separated groups: us, kr, crypto.",
    )
    parser.add_argument(
        "--symbols",
        default="",
        help="Optional comma-separated symbols. If set, downloads only these symbols.",
    )
    parser.add_argument(
        "--output-dir",
        default="downloads",
        help="Folder for generated CSV files. Relative paths are based on this script folder.",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=0.25,
        help="Seconds to wait between symbols.",
    )
    return parser.parse_args()


def date_to_epoch_seconds(value):
    parsed = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(parsed.timestamp())


def yahoo_chart_url(symbol, start_date, end_date):
    period1 = date_to_epoch_seconds(start_date)
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date() + timedelta(days=1)
    period2 = date_to_epoch_seconds(end_dt.isoformat())
    encoded_symbol = quote(symbol, safe="")
    return (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded_symbol}"
        f"?period1={period1}&period2={period2}&interval=1d&includePrePost=false"
    )


def fetch_json(url):
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def number_or_blank(values, index):
    if not values or index >= len(values):
        return ""
    value = values[index]
    return "" if value is None else value


def rows_for_symbol(symbol, start_date, end_date):
    payload = fetch_json(yahoo_chart_url(symbol, start_date, end_date))
    chart = payload.get("chart", {})
    error = chart.get("error")
    if error:
        raise RuntimeError(error.get("description") or error)

    results = chart.get("result") or []
    if not results:
        raise RuntimeError("No chart result returned.")

    result = results[0]
    timestamps = result.get("timestamp") or []
    quote_data = (result.get("indicators", {}).get("quote") or [{}])[0]
    adjclose_data = (result.get("indicators", {}).get("adjclose") or [{}])[0]

    opens = quote_data.get("open", [])
    highs = quote_data.get("high", [])
    lows = quote_data.get("low", [])
    closes = quote_data.get("close", [])
    volumes = quote_data.get("volume", [])
    adj_closes = adjclose_data.get("adjclose") or closes

    rows = []
    for index, timestamp in enumerate(timestamps):
        day = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")
        rows.append(
            [
                symbol,
                day,
                number_or_blank(opens, index),
                number_or_blank(highs, index),
                number_or_blank(lows, index),
                number_or_blank(closes, index),
                number_or_blank(adj_closes, index),
                number_or_blank(volumes, index),
            ]
        )
    return rows


def selected_symbols(args):
    if args.symbols.strip():
        return {"custom": [item.strip() for item in args.symbols.split(",") if item.strip()]}

    selected = {}
    for group in [item.strip().lower() for item in args.groups.split(",") if item.strip()]:
        if group not in DEFAULT_SYMBOLS:
            raise ValueError(f"Unknown group: {group}")
        selected[group] = DEFAULT_SYMBOLS[group]
    return selected


def make_output_root(script_dir, output_dir):
    output_path = Path(output_dir)
    if not output_path.is_absolute():
        output_path = script_dir / output_path
    run_dir = output_path / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_HEADER)
        writer.writerows(rows)


def main():
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    run_dir = make_output_root(script_dir, args.output_dir)
    failures = []

    try:
        groups = selected_symbols(args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"Output folder: {run_dir}")
    print(f"Period: {args.start} to {args.end}")

    for group, symbols in groups.items():
        group_rows = []
        print(f"\n[{group}] {len(symbols)} symbols")
        for position, symbol in enumerate(symbols, start=1):
            print(f"  {position:02d}/{len(symbols):02d} {symbol}", end="", flush=True)
            try:
                rows = rows_for_symbol(symbol, args.start, args.end)
                group_rows.extend(rows)
                print(f" -> {len(rows)} rows")
            except (HTTPError, URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
                failures.append((group, symbol, str(exc)))
                print(f" -> failed: {exc}")
            time.sleep(args.pause)

        csv_path = run_dir / f"{group}_{args.start}_{args.end}.csv"
        write_csv(csv_path, group_rows)
        print(f"Saved: {csv_path}")

    if failures:
        failure_path = run_dir / "failures.txt"
        with failure_path.open("w", encoding="utf-8") as handle:
            for group, symbol, reason in failures:
                handle.write(f"{group},{symbol},{reason}\n")
        print(f"\nFailures saved: {failure_path}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
