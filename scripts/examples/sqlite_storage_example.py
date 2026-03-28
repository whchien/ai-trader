#!/usr/bin/env python3
"""
Example: Using SQLite Persistent Data Storage with SQLModel ORM

This script demonstrates how to use the new SQLiteDataStorage layer to:
1. Cache market data in SQLite for faster access
2. Perform incremental updates (only fetch missing dates)
3. Query cached data efficiently
4. Manage the database (list, delete, clean data)

Benefits:
- Avoid redundant API calls (~40x faster on repeated fetches)
- Automatic incremental updates
- Support for multiple markets (US stocks, Taiwan stocks, crypto, forex, VIX)
- Type-safe ORM operations with SQLModel (no raw SQL)
"""

import pandas as pd
from datetime import datetime
from ai_trader.data.fetchers import USStockFetcher
from ai_trader.data.storage import SQLiteDataStorage

def example_1_basic_storage():
    """Basic example: Save and load data from SQLite"""
    print("\n" + "=" * 70)
    print("Example 1: Basic Storage - Save & Load Data")
    print("=" * 70)

    # Initialize storage
    storage = SQLiteDataStorage(db_path="data/market_data.db")
    print("✓ Storage initialized at data/market_data.db")

    # Fetch data from API
    fetcher = USStockFetcher(symbol="AAPL", start_date="2024-01-01", end_date="2024-01-31")
    df = fetcher.fetch()
    print(f"✓ Fetched {len(df)} rows for AAPL from API")

    # Save to SQLite
    rows_saved = storage.save(df=df, ticker="AAPL", market_type="us_stock")
    print(f"✓ Saved {rows_saved} rows to SQLite database")

    # Load from SQLite
    loaded_df = storage.load("AAPL", "us_stock", "2024-01-01", "2024-01-31")
    print(f"✓ Loaded {len(loaded_df)} rows from SQLite database")
    print(f"  Columns: {list(loaded_df.columns)}")
    print(f"  Date range: {loaded_df.index[0]} to {loaded_df.index[-1]}")


def example_2_incremental_updates():
    """Smart incremental updates: Only fetch missing dates"""
    print("\n" + "=" * 70)
    print("Example 2: Incremental Updates - Fetch Only Missing Data")
    print("=" * 70)

    storage = SQLiteDataStorage(db_path="data/market_data.db")

    # Check what data is already cached
    ticker = "MSFT"
    market = "us_stock"
    coverage = storage.get_coverage(ticker, market)

    if coverage:
        print(f"✓ Found cached data for {ticker}: {coverage[0]} to {coverage[1]}")

        # Calculate what needs to be fetched
        missing_ranges = storage.get_missing_ranges(
            ticker, market,
            start_date="2023-01-01",  # Want data from 2023
            end_date="2024-12-31"      # to 2024
        )

        if missing_ranges:
            print(f"✓ Missing date ranges ({len(missing_ranges)}):")
            for start, end in missing_ranges:
                print(f"  - {start} to {end}")

            # Fetch only the missing data
            print(f"  (Would fetch only these ranges from API)")
        else:
            print(f"✓ All data is cached! No API calls needed.")
    else:
        print(f"✗ No cached data for {ticker}. Would fetch everything from API.")


def example_3_list_and_manage():
    """List cached data and manage the database"""
    print("\n" + "=" * 70)
    print("Example 3: Database Management - List, Delete, Clean")
    print("=" * 70)

    storage = SQLiteDataStorage(db_path="data/market_data.db")

    # List all cached tickers
    tickers = storage.list_tickers()
    if tickers:
        print(f"✓ Cached tickers ({len(tickers)}):")
        for t in tickers:
            print(f"  • {t['ticker']:10s} ({t['market']:10s}): "
                  f"{t['from']} to {t['to']} ({t['rows']} rows)")
    else:
        print("✗ No cached data")

    # Get database statistics
    info = storage.get_database_info()
    print(f"\n✓ Database Information:")
    print(f"  Path: {info['path']}")
    print(f"  Size: {info['size_bytes']:,} bytes")
    print(f"  Total tickers: {info['total_tickers']}")
    print(f"  Tickers by market:")
    for market, count in info['tickers_by_market'].items():
        print(f"    • {market:10s}: {count} tickers")


def example_4_multi_market():
    """Working with multiple markets (US stock, crypto, etc.)"""
    print("\n" + "=" * 70)
    print("Example 4: Multi-Market Support")
    print("=" * 70)

    storage = SQLiteDataStorage(db_path="data/market_data.db")

    # Each market has its own table
    markets = ["us_stock", "tw_stock", "crypto", "forex", "vix"]
    print(f"✓ Supported markets (each has independent table):")
    for market in markets:
        print(f"  • {market}")

    # List tickers by market
    print(f"\n✓ Filtering by market type:")
    for market in markets:
        tickers = storage.list_tickers(market_type=market)
        print(f"  {market:10s}: {len(tickers)} tickers")


def example_5_cleanup():
    """Delete old data to manage database size"""
    print("\n" + "=" * 70)
    print("Example 5: Database Cleanup - Remove Old Data")
    print("=" * 70)

    storage = SQLiteDataStorage(db_path="data/market_data.db")

    # Show current size
    info_before = storage.get_database_info()
    print(f"✓ Database size before cleanup: {info_before['size_bytes']:,} bytes")

    # Delete data before a specific date (e.g., data from 2020)
    # count = storage.delete_before("us_stock", before_date="2020-01-01")
    # print(f"✓ Deleted {count} rows before 2020-01-01")

    # Or delete specific ticker
    # count = storage.delete_ticker("AAPL", "us_stock")
    # print(f"✓ Deleted all data for AAPL")

    print("\n  Note: Uncomment lines above to actually delete data")


def example_6_backtest_workflow():
    """Complete workflow: Fetch → Cache → Backtest → Use Cache"""
    print("\n" + "=" * 70)
    print("Example 6: Complete Workflow - Fetch, Cache, Backtest")
    print("=" * 70)

    from ai_trader.utils.backtest import run_backtest
    from ai_trader.backtesting.strategies.classic.sma import CrossSMAStrategy

    storage = SQLiteDataStorage(db_path="data/market_data.db")
    ticker = "AAPL"
    market = "us_stock"

    # Step 1: Check if data is cached
    print(f"\n1. Checking cache for {ticker}...")
    missing = storage.get_missing_ranges(ticker, market, "2024-01-01", "2024-12-31")

    if missing:
        print(f"   Missing data. Fetching from API...")
        fetcher = USStockFetcher(
            symbol=ticker,
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        df = fetcher.fetch()
        rows = storage.save(df=df, ticker=ticker, market_type=market)
        print(f"   ✓ Cached {rows} rows")
    else:
        print(f"   ✓ Data already cached!")

    # Step 2: Load from cache and run backtest
    print(f"\n2. Running backtest on cached data...")
    df = storage.load(ticker, market, "2024-01-01", "2024-12-31")
    print(f"   ✓ Loaded {len(df)} rows from cache")

    # Step 3: Save to CSV for backtest (if needed)
    csv_path = f"data/us_stock/{ticker}_cached.csv"
    df.to_csv(csv_path)
    print(f"   ✓ Exported to {csv_path}")

    # Step 4: Run backtest
    print(f"\n3. Running backtest...")
    try:
        results = run_backtest(
            strategy=CrossSMAStrategy,
            data_source=csv_path,
            cash=100000,
            strategy_params={"fast": 10, "slow": 30},
            print_output=False
        )
        print(f"   ✓ Backtest complete")
    except Exception as e:
        print(f"   ℹ Backtest skipped: {e}")


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("SQLite Persistent Data Storage Examples")
    print("=" * 70)
    print("""
This script demonstrates the new SQLiteDataStorage layer with SQLModel ORM.

Features:
  • Cache market data to avoid redundant API calls
  • Automatic incremental updates (only fetch missing dates)
  • Support for 5 markets: US stocks, Taiwan stocks, crypto, forex, VIX
  • Type-safe ORM operations with SQLModel (no raw SQL)
  • Database management: list, delete, clean data

Typical Usage:
  1. First call: Fetches from API, saves to SQLite (~2-3 seconds)
  2. Second call: Loads from cache (~50ms, no API call)
  3. Subsequent calls: Incremental updates on new dates only
    """)

    # Run examples
    example_1_basic_storage()
    example_2_incremental_updates()
    example_3_list_and_manage()
    example_4_multi_market()
    example_5_cleanup()
    example_6_backtest_workflow()

    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)
    print("""
Next Steps:
  1. Check data/market_data.db - SQLite database with cached data
  2. Use CLI: ai-trader data list, ai-trader data info, ai-trader data clean
  3. Fetch with cache: ai-trader fetch AAPL --market us_stock --storage sqlite
  4. Learn more: See agentic_ai_trader/trading-backtester/README.md
    """)


if __name__ == "__main__":
    main()
