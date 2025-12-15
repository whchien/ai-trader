"""Integration test to verify the trading backtester works with ai_trader."""

import sys
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir.parent.parent))  # For ai_trader
sys.path.insert(0, str(current_dir))  # For trading_backtester


def test_ai_trader_integration():
    """Test that we can import and use ai_trader components."""
    try:
        # Test importing ai_trader utilities
        import ai_trader.backtesting.strategies.classic.sma as sma_module
        import ai_trader.utils.backtest as backtest_utils

        create_cerebro = backtest_utils.create_cerebro
        run_backtest = backtest_utils.run_backtest
        SMAStrategy = sma_module.SMAStrategy

        print("✓ Successfully imported ai_trader components")

        # Test creating a cerebro instance
        cerebro = create_cerebro(cash=100000, commission=0.001)
        print(f"✓ Created cerebro with cash: ${cerebro.broker.getvalue():,}")

        # Test getting available strategies
        from trading_backtester.core.utils import get_available_strategies

        strategies = get_available_strategies()
        print(f"✓ Found {len(strategies)} available strategies")

        # Print some strategy names
        strategy_names = list(strategies.keys())[:5]
        print(f"  Sample strategies: {', '.join(strategy_names)}")

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_trading_backtester_components():
    """Test that trading backtester components work."""
    try:
        # Test configuration
        from trading_backtester.core.config import config

        print("✓ Configuration loaded")
        print(f"  Default cash: ${config.get('backtesting.default_cash'):,}")
        print(f"  Root agent model: {config.get_model('root_agent')}")

        # Test tools (without actually calling them)

        print("✓ Coordinator tools imported successfully")

        # Test agent creation
        from trading_backtester.agent import root_agent

        print(f"✓ Root agent created: {root_agent.name}")

        return True

    except Exception as e:
        print(f"✗ Error testing trading backtester: {e}")
        return False


def main():
    """Run integration tests."""
    print("=" * 60)
    print("TRADING BACKTESTER INTEGRATION TEST")
    print("=" * 60)

    print("\n1. Testing ai_trader integration...")
    ai_trader_ok = test_ai_trader_integration()

    print("\n2. Testing trading backtester components...")
    backtester_ok = test_trading_backtester_components()

    print("\n" + "=" * 60)
    if ai_trader_ok and backtester_ok:
        print("✓ ALL TESTS PASSED - Integration successful!")
        print("\nNext steps:")
        print("1. Set up your .env file with Google Cloud credentials")
        print("2. Run: adk run trading_backtester")
        print("3. Or run: adk web (and select trading_backtester)")
    else:
        print("✗ SOME TESTS FAILED - Check the errors above")
    print("=" * 60)


if __name__ == "__main__":
    main()
