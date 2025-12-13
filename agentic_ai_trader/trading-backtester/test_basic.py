"""Basic test to verify ai_trader integration without Google ADK."""

import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent.parent))  # For ai_trader


def test_ai_trader_basic():
    """Test basic ai_trader functionality."""
    try:
        print("Testing ai_trader imports...")
        
        # Test basic imports
        import ai_trader
        print(f"✓ ai_trader version: {ai_trader.__version__}")
        
        # Test utility imports
        import ai_trader.utils.backtest as backtest_utils
        print("✓ Imported backtest utilities")
        
        # Test strategy imports
        import ai_trader.backtesting.strategies.classic.sma as sma_module
        print("✓ Imported SMA strategy")
        
        # Test creating cerebro
        cerebro = backtest_utils.create_cerebro(cash=100000, commission=0.001)
        print(f"✓ Created cerebro with cash: ${cerebro.broker.getvalue():,}")
        
        # Test data fetcher
        import ai_trader.data.fetchers.base as base_fetcher
        print("✓ Imported data fetchers")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trading_backtester_utils():
    """Test trading backtester utilities without ADK."""
    try:
        print("\nTesting trading backtester utilities...")
        
        # Test configuration (without Google ADK dependencies)
        import os
        os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "test-project")
        os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        from trading_backtester.core.config import config
        print(f"✓ Configuration loaded")
        print(f"  Default cash: ${config.get('backtesting.default_cash'):,}")
        
        # Test utils
        from trading_backtester.core.utils import (
            validate_date_range,
            generate_parameter_grid,
            format_performance_summary,
            get_available_strategies,
        )
        print("✓ Imported utility functions")
        
        # Test date validation
        start, end = validate_date_range("2023-01-01", "2023-12-31")
        assert start == "2023-01-01"
        print("✓ Date validation works")
        
        # Test parameter grid
        grid = generate_parameter_grid({"a": [1, 2], "b": [3, 4]})
        assert len(grid) == 4
        print("✓ Parameter grid generation works")
        
        # Test performance summary
        metrics = {"total_return": 15.5, "sharpe_ratio": 1.2}
        summary = format_performance_summary(metrics)
        assert "15.50%" in summary
        print("✓ Performance summary formatting works")
        
        # Test getting available strategies
        strategies = get_available_strategies()
        print(f"✓ Found {len(strategies)} available strategies")
        if strategies:
            sample_names = list(strategies.keys())[:3]
            print(f"  Sample strategies: {', '.join(sample_names)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run basic tests."""
    print("=" * 60)
    print("BASIC INTEGRATION TEST (No Google ADK)")
    print("=" * 60)
    
    ai_trader_ok = test_ai_trader_basic()
    backtester_ok = test_trading_backtester_utils()
    
    print("\n" + "=" * 60)
    if ai_trader_ok and backtester_ok:
        print("✓ BASIC INTEGRATION SUCCESSFUL!")
        print("\nThe trading backtester can successfully:")
        print("- Import and use ai_trader components")
        print("- Access trading strategies")
        print("- Create backtesting infrastructure")
        print("- Manage configuration and utilities")
        print("\nNext: Set up Google Cloud credentials and test with ADK")
    else:
        print("✗ INTEGRATION ISSUES DETECTED")
    print("=" * 60)


if __name__ == "__main__":
    main()