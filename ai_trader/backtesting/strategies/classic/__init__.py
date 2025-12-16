"""Classic trading strategies for single stocks."""

from ai_trader.backtesting.strategies.classic.bbands import BBandsStrategy
from ai_trader.backtesting.strategies.classic.buyhold import BuyHoldStrategy
from ai_trader.backtesting.strategies.classic.double_top import DoubleTopStrategy
from ai_trader.backtesting.strategies.classic.macd import MACDStrategy
from ai_trader.backtesting.strategies.classic.momentum import MomentumStrategy
from ai_trader.backtesting.strategies.classic.risk_averse import RiskAverseStrategy
from ai_trader.backtesting.strategies.classic.roc import (
    NaiveROCStrategy,
    ROCMAStrategy,
    ROCStochStrategy,
)
from ai_trader.backtesting.strategies.classic.rsi import (
    RsiBollingerBandsStrategy,
    TripleRsiStrategy,
)
from ai_trader.backtesting.strategies.classic.rsrs import RSRSStrategy
from ai_trader.backtesting.strategies.classic.sma import CrossSMAStrategy, NaiveSMAStrategy
from ai_trader.backtesting.strategies.classic.turtle import TurtleTradingStrategy
from ai_trader.backtesting.strategies.classic.vcp import VCPStrategy

__all__ = [
    "BBandsStrategy",
    "BuyHoldStrategy",
    "CrossSMAStrategy",
    "DoubleTopStrategy",
    "MACDStrategy",
    "MomentumStrategy",
    "NaiveROCStrategy",
    "NaiveSMAStrategy",
    "RiskAverseStrategy",
    "ROCMAStrategy",
    "ROCStochStrategy",
    "RsiBollingerBandsStrategy",
    "RSRSStrategy",
    "TripleRsiStrategy",
    "TurtleTradingStrategy",
    "VCPStrategy",
]
