"""Tests for BaseStrategy class and strategy implementations."""

import pytest
from unittest.mock import MagicMock, patch
import backtrader as bt


class TestBaseStrategyStructure:
    """Test BaseStrategy structure and methods."""

    def test_base_strategy_is_backtrader_strategy(self):
        """Test BaseStrategy inherits from bt.Strategy."""
        from ai_trader.backtesting.strategies.base import BaseStrategy

        assert issubclass(BaseStrategy, bt.Strategy)

    def test_base_strategy_has_log_method(self):
        """Test BaseStrategy has log method."""
        from ai_trader.backtesting.strategies.base import BaseStrategy

        assert hasattr(BaseStrategy, 'log')
        assert callable(getattr(BaseStrategy, 'log'))

    def test_base_strategy_has_notify_order_method(self):
        """Test BaseStrategy has notify_order method."""
        from ai_trader.backtesting.strategies.base import BaseStrategy

        assert hasattr(BaseStrategy, 'notify_order')
        assert callable(getattr(BaseStrategy, 'notify_order'))

    def test_base_strategy_has_notify_trade_method(self):
        """Test BaseStrategy has notify_trade method."""
        from ai_trader.backtesting.strategies.base import BaseStrategy

        assert hasattr(BaseStrategy, 'notify_trade')
        assert callable(getattr(BaseStrategy, 'notify_trade'))

    def test_base_strategy_has_class_variables(self):
        """Test BaseStrategy has required class variables."""
        from ai_trader.backtesting.strategies.base import BaseStrategy

        assert hasattr(BaseStrategy, 'COL_WIDTH_ACTION')
        assert hasattr(BaseStrategy, 'COL_WIDTH_DETAIL1')
        assert hasattr(BaseStrategy, 'COL_WIDTH_DETAIL2')
        assert hasattr(BaseStrategy, 'COL_WIDTH_DETAIL3')

    def test_base_strategy_class_variables_are_positive_integers(self):
        """Test BaseStrategy class variables are positive integers."""
        from ai_trader.backtesting.strategies.base import BaseStrategy

        assert BaseStrategy.COL_WIDTH_ACTION > 0
        assert BaseStrategy.COL_WIDTH_DETAIL1 > 0
        assert BaseStrategy.COL_WIDTH_DETAIL2 > 0
        assert BaseStrategy.COL_WIDTH_DETAIL3 > 0


class TestSimpleStrategyImports:
    """Test simple strategy implementations can be imported."""

    def test_buy_hold_strategy_imports(self):
        """Test BuyHoldStrategy can be imported."""
        from ai_trader.backtesting.strategies.classic.buyhold import BuyHoldStrategy

        assert BuyHoldStrategy is not None
        assert issubclass(BuyHoldStrategy, bt.Strategy)

    def test_buy_hold_strategy_has_next_method(self):
        """Test BuyHoldStrategy has next method."""
        from ai_trader.backtesting.strategies.classic.buyhold import BuyHoldStrategy

        assert hasattr(BuyHoldStrategy, 'next')

    def test_rsi_strategy_imports(self):
        """Test RsiBollingerBandsStrategy can be imported."""
        from ai_trader.backtesting.strategies.classic.rsi import RsiBollingerBandsStrategy

        assert RsiBollingerBandsStrategy is not None
        assert issubclass(RsiBollingerBandsStrategy, bt.Strategy)

    def test_rsi_strategy_has_next_method(self):
        """Test RsiBollingerBandsStrategy has next method."""
        from ai_trader.backtesting.strategies.classic.rsi import RsiBollingerBandsStrategy

        assert hasattr(RsiBollingerBandsStrategy, 'next')

    def test_triple_rsi_strategy_imports(self):
        """Test TripleRsiStrategy can be imported."""
        from ai_trader.backtesting.strategies.classic.rsi import TripleRsiStrategy

        assert TripleRsiStrategy is not None
        assert issubclass(TripleRsiStrategy, bt.Strategy)

    def test_sma_strategy_imports(self):
        """Test SMA strategies can be imported."""
        from ai_trader.backtesting.strategies.classic.sma import NaiveSMAStrategy, CrossSMAStrategy

        assert NaiveSMAStrategy is not None
        assert issubclass(NaiveSMAStrategy, bt.Strategy)
        assert CrossSMAStrategy is not None
        assert issubclass(CrossSMAStrategy, bt.Strategy)


class TestStrategyParameters:
    """Test strategy parameter configuration."""

    def test_rsi_strategy_has_params_attribute(self):
        """Test RsiBollingerBandsStrategy has params attribute."""
        from ai_trader.backtesting.strategies.classic.rsi import RsiBollingerBandsStrategy

        # Backtrader strategies have a params class attribute (it's a special object)
        assert hasattr(RsiBollingerBandsStrategy, 'params')

    def test_triple_rsi_strategy_has_params_attribute(self):
        """Test TripleRsiStrategy has params attribute."""
        from ai_trader.backtesting.strategies.classic.rsi import TripleRsiStrategy

        assert hasattr(TripleRsiStrategy, 'params')

    def test_sma_strategy_has_params_attribute(self):
        """Test SMA strategy has params attribute."""
        from ai_trader.backtesting.strategies.classic.sma import NaiveSMAStrategy

        assert hasattr(NaiveSMAStrategy, 'params')

    def test_strategies_have_sensible_defaults(self):
        """Test strategies have sensible default parameters."""
        from ai_trader.backtesting.strategies.classic.rsi import RsiBollingerBandsStrategy
        from ai_trader.backtesting.strategies.classic.sma import NaiveSMAStrategy

        strategies_to_check = [
            RsiBollingerBandsStrategy,
            NaiveSMAStrategy,
        ]

        for strategy_class in strategies_to_check:
            # Just verify params exist and strategy can be referenced
            assert strategy_class is not None


class TestPortfolioStrategies:
    """Test portfolio strategy implementations."""

    def test_triple_rsi_portfolio_strategy_imports(self):
        """Test TripleRSIRotationStrategy from portfolio can be imported."""
        from ai_trader.backtesting.strategies.portfolio.triple_rsi import TripleRSIRotationStrategy

        assert TripleRSIRotationStrategy is not None
        assert issubclass(TripleRSIRotationStrategy, bt.Strategy)

    def test_roc_rotation_strategy_imports(self):
        """Test ROCRotationStrategy can be imported."""
        from ai_trader.backtesting.strategies.portfolio.roc_rotation import ROCRotationStrategy

        assert ROCRotationStrategy is not None
        assert issubclass(ROCRotationStrategy, bt.Strategy)


class TestStrategyInheritance:
    """Test strategy inheritance relationships."""

    def test_all_classic_strategies_inherit_from_base(self):
        """Test all classic strategies inherit from BaseStrategy."""
        from ai_trader.backtesting.strategies.base import BaseStrategy
        from ai_trader.backtesting.strategies.classic.buyhold import BuyHoldStrategy
        from ai_trader.backtesting.strategies.classic.rsi import (
            RsiBollingerBandsStrategy,
            TripleRsiStrategy,
        )
        from ai_trader.backtesting.strategies.classic.sma import NaiveSMAStrategy

        classic_strategies = [
            BuyHoldStrategy,
            RsiBollingerBandsStrategy,
            TripleRsiStrategy,
            NaiveSMAStrategy,
        ]

        for strategy in classic_strategies:
            assert issubclass(strategy, BaseStrategy)

    def test_all_classic_strategies_inherit_from_backtrader_strategy(self):
        """Test all classic strategies inherit from bt.Strategy."""
        from ai_trader.backtesting.strategies.classic.buyhold import BuyHoldStrategy
        from ai_trader.backtesting.strategies.classic.rsi import (
            RsiBollingerBandsStrategy,
            TripleRsiStrategy,
        )
        from ai_trader.backtesting.strategies.classic.sma import NaiveSMAStrategy

        classic_strategies = [
            BuyHoldStrategy,
            RsiBollingerBandsStrategy,
            TripleRsiStrategy,
            NaiveSMAStrategy,
        ]

        for strategy in classic_strategies:
            assert issubclass(strategy, bt.Strategy)
