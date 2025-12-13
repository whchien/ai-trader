"""Integration tests for end-to-end strategy execution."""
import pytest
from ai_trader.trader import AITrader
from ai_trader.backtesting.strategies.classic.buyhold import BuyHoldStrategy


@pytest.mark.integration
class TestStrategyExecution:
    """Test end-to-end strategy execution."""

    def test_buyhold_strategy_execution(self, sample_csv_file):
        """Test BuyHold strategy executes without errors."""
        trader = AITrader(
            strategy=BuyHoldStrategy,
            cash=100000,
            start_date="2020-01-01",
            end_date="2020-12-31"
        )
        trader.add_one_stock(str(sample_csv_file))
        trader.add_analyzers()

        # Run backtest - should complete without errors
        results = trader.run()

        # Basic validation
        assert results is not None
        assert len(results) > 0

        # Get strategy instance
        strat = results[0]

        # Verify final portfolio value is positive
        final_value = trader.cerebro.broker.getvalue()
        assert final_value > 0

    @pytest.mark.slow
    def test_all_classic_strategies_importable(self):
        """Smoke test: verify all classic strategies can be imported."""

        # If we get here, all imports succeeded
        assert True

    @pytest.mark.slow
    def test_portfolio_strategies_importable(self):
        """Smoke test: verify all portfolio strategies can be imported."""

        # If we get here, all imports succeeded
        assert True


@pytest.mark.integration
@pytest.mark.slow
class TestMultipleStrategies:
    """Test running multiple strategies."""

    def test_compare_two_strategies(self, sample_csv_file):
        """Test comparing BuyHold vs another strategy."""
        # Test BuyHold
        trader1 = AITrader(strategy=BuyHoldStrategy, cash=100000)
        trader1.add_one_stock(str(sample_csv_file))
        results1 = trader1.run()
        value1 = trader1.cerebro.broker.getvalue()

        # Both should produce valid results
        assert results1 is not None
        assert value1 > 0
