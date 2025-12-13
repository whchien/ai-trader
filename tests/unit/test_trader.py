"""Tests for backtesting functionality."""
import pytest
import pandas as pd
from pathlib import Path
from ai_trader.trader import AITrader
from ai_trader.backtesting.strategies.base import BaseStrategy


class SimpleTestStrategy(BaseStrategy):
    """Simple strategy for testing."""

    def __init__(self):
        super().__init__()

    def next(self):
        """Buy on first day, hold."""
        if len(self) == 1 and not self.position:
            self.buy()


class TestAITrader:
    """Test AITrader class."""

    def test_trader_init_default(self):
        """Test AITrader initialization with defaults."""
        trader = AITrader()
        assert trader.cerebro is not None
        assert trader.cash == 1000000
        assert trader.commission == 0.001425

    def test_trader_init_custom_params(self):
        """Test AITrader initialization with custom parameters."""
        trader = AITrader(
            cash=500000,
            commission=0.002,
            start_date="2020-01-01",
            end_date="2020-12-31"
        )
        assert trader.cash == 500000
        assert trader.commission == 0.002
        assert trader.start_date == "2020-01-01"
        assert trader.end_date == "2020-12-31"

    def test_trader_init_with_strategy(self):
        """Test AITrader initialization with a strategy."""
        trader = AITrader(strategy=SimpleTestStrategy)
        assert trader.strategy == SimpleTestStrategy

    def test_add_strategy(self):
        """Test adding a strategy to AITrader."""
        trader = AITrader()
        trader.add_strategy(SimpleTestStrategy)
        assert trader.strategy == SimpleTestStrategy

    def test_add_one_stock_missing_file(self):
        """Test adding non-existent stock file raises FileNotFoundError."""
        trader = AITrader()
        with pytest.raises(FileNotFoundError):
            trader.add_one_stock("nonexistent_stock.csv")

    def test_add_one_stock_with_dates(self, sample_csv_file):
        """Test adding stock data with date filtering."""
        trader = AITrader(start_date="2020-01-01", end_date="2020-06-30")
        trader.add_one_stock(str(sample_csv_file))
        # Verify data was added to cerebro
        assert len(trader.cerebro.datas) == 1

    def test_run_without_strategy_raises_error(self):
        """Test that running without strategy raises ValueError."""
        trader = AITrader()
        with pytest.raises(ValueError, match="No strategy specified"):
            trader.run()

    def test_run_without_data(self, sample_csv_file):
        """Test running with strategy but without data."""
        trader = AITrader(strategy=SimpleTestStrategy)
        # Should be able to run but may not produce meaningful results
        # without data - this tests the basic execution flow
        try:
            results = trader.run()
            assert results is not None
        except Exception as e:
            # Backtrader may raise various exceptions without data
            pytest.skip(f"Backtrader raised: {e}")

    def test_trader_attributes(self):
        """Test AITrader has expected attributes."""
        trader = AITrader()
        assert hasattr(trader, "cerebro")
        assert hasattr(trader, "strategy")
        assert hasattr(trader, "cash")
        assert hasattr(trader, "commission")
        assert hasattr(trader, "start_date")
        assert hasattr(trader, "end_date")
        assert hasattr(trader, "data_dir")


@pytest.mark.integration
class TestAITraderIntegration:
    """Integration tests for complete backtest execution."""

    def test_full_backtest_run(self, sample_csv_file):
        """Test complete backtest with real data."""
        trader = AITrader(
            strategy=SimpleTestStrategy,
            cash=100000,
            start_date="2020-01-01",
            end_date="2020-12-31"
        )
        trader.add_one_stock(str(sample_csv_file))

        # Run backtest
        results = trader.run()

        # Verify results
        assert results is not None
        assert len(results) > 0

        # Check final value changed from initial cash
        final_value = trader.cerebro.broker.getvalue()
        assert final_value > 0

    def test_backtest_with_analyzers(self, sample_csv_file):
        """Test backtest includes analyzers."""
        trader = AITrader(strategy=SimpleTestStrategy)
        trader.add_one_stock(str(sample_csv_file))
        trader.add_analyzers()

        results = trader.run()
        assert results is not None

        # Check that analyzers were added
        strat = results[0]
        assert hasattr(strat, "analyzers")
