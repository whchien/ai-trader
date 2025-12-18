"""Integration tests for backtest workflows."""

import pytest
import pandas as pd
import tempfile
from pathlib import Path


class TestBacktestPipeline:
    """Test end-to-end backtest workflows."""

    def test_backtest_with_sample_data(self, sample_ohlcv_data):
        """Test running a backtest with sample data."""
        from ai_trader.utils.backtest import create_cerebro
        from ai_trader.backtesting.strategies.classic.buyhold import BuyHoldStrategy

        # Create cerebro environment
        cerebro = create_cerebro(cash=10000, commission=0.001)

        # Add sample data as PandasData
        from backtrader.feeds import PandasData
        data = PandasData(dataname=sample_ohlcv_data)
        cerebro.adddata(data)

        # Add strategy
        cerebro.addstrategy(BuyHoldStrategy)

        # Run backtest
        cerebro.run()

        # Verify cerebro completed without errors
        assert cerebro is not None


    def test_backtest_with_multiple_strategies(self, sample_ohlcv_data):
        """Test running multiple strategies on same data."""
        from ai_trader.utils.backtest import create_cerebro
        from ai_trader.backtesting.strategies.classic.buyhold import BuyHoldStrategy
        from ai_trader.backtesting.strategies.classic.sma import NaiveSMAStrategy

        strategies = [BuyHoldStrategy, NaiveSMAStrategy]

        for strategy_class in strategies:
            # Create fresh cerebro for each strategy
            cerebro = create_cerebro(cash=10000, commission=0.001)

            # Add data
            from backtrader.feeds import PandasData
            data = PandasData(dataname=sample_ohlcv_data)
            cerebro.adddata(data)

            # Add strategy
            cerebro.addstrategy(strategy_class)

            # Run backtest
            results = cerebro.run()

            # Verify execution completed
            assert results is not None
            assert len(results) > 0


class TestStrategyParameterization:
    """Test strategy parameter variations."""

    def test_strategy_with_extended_data(self):
        """Test strategies with sufficient data for indicator calculations."""
        from ai_trader.utils.backtest import create_cerebro
        from ai_trader.backtesting.strategies.classic.buyhold import BuyHoldStrategy
        import pandas as pd

        # Create data with sufficient length for indicators (e.g., 200+ bars)
        dates = pd.date_range("2022-01-01", periods=250)
        data = pd.DataFrame({
            'open': [100.0 + i * 0.1 for i in range(250)],
            'high': [105.0 + i * 0.1 for i in range(250)],
            'low': [95.0 + i * 0.1 for i in range(250)],
            'close': [100.0 + i * 0.1 for i in range(250)],
            'volume': [1000000] * 250,
        }, index=dates)
        data.index.name = 'Date'

        cerebro = create_cerebro(cash=10000, commission=0.001)

        # Add data
        from backtrader.feeds import PandasData
        feed = PandasData(dataname=data)
        cerebro.adddata(feed)

        # Add simple strategy
        cerebro.addstrategy(BuyHoldStrategy)

        # Run backtest
        results = cerebro.run()

        # Verify execution
        assert results is not None


class TestBacktestConfiguration:
    """Test backtest configuration variations."""

    def test_backtest_with_different_cash_amounts(self, sample_ohlcv_data):
        """Test backtest with different initial cash amounts."""
        from ai_trader.utils.backtest import create_cerebro
        from ai_trader.backtesting.strategies.classic.buyhold import BuyHoldStrategy

        cash_amounts = [1000, 10000, 100000]

        for cash in cash_amounts:
            cerebro = create_cerebro(cash=cash, commission=0.001)

            # Add data
            from backtrader.feeds import PandasData
            data = PandasData(dataname=sample_ohlcv_data)
            cerebro.adddata(data)

            # Add strategy
            cerebro.addstrategy(BuyHoldStrategy)

            # Run backtest
            results = cerebro.run()

            # Verify execution
            assert results is not None

    def test_backtest_with_different_commission_rates(self, sample_ohlcv_data):
        """Test backtest with different commission rates."""
        from ai_trader.utils.backtest import create_cerebro
        from ai_trader.backtesting.strategies.classic.buyhold import BuyHoldStrategy

        commission_rates = [0.0, 0.001, 0.005]

        for commission in commission_rates:
            cerebro = create_cerebro(cash=10000, commission=commission)

            # Add data
            from backtrader.feeds import PandasData
            data = PandasData(dataname=sample_ohlcv_data)
            cerebro.adddata(data)

            # Add strategy
            cerebro.addstrategy(BuyHoldStrategy)

            # Run backtest
            results = cerebro.run()

            # Verify execution
            assert results is not None


class TestAnalyzerIntegration:
    """Test analyzer integration with backtest."""

    def test_backtest_with_analyzers(self, sample_ohlcv_data):
        """Test running backtest with various analyzers."""
        from ai_trader.utils.backtest import create_cerebro
        from ai_trader.backtesting.strategies.classic.buyhold import BuyHoldStrategy
        import backtrader as bt

        cerebro = create_cerebro(cash=10000, commission=0.001)

        # Add data
        from backtrader.feeds import PandasData
        data = PandasData(dataname=sample_ohlcv_data)
        cerebro.adddata(data)

        # Add strategy
        cerebro.addstrategy(BuyHoldStrategy)

        # Add analyzers
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')

        # Run backtest
        results = cerebro.run()

        # Verify analyzers were added
        assert len(cerebro.analyzers) >= 3
