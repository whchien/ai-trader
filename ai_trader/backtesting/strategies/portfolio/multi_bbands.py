"""
Multi-Asset Bollinger Bands Rotation Strategy

Implements a multi-asset portfolio rotation strategy that identifies
overbought/oversold conditions across multiple assets and concentrates
capital in the best opportunity.
"""

import backtrader as bt

from ai_trader.backtesting.strategies.base import BaseStrategy


class MultiBBandsRotationStrategy(BaseStrategy):
    """
    Multi-Asset Bollinger Bands Rotation Strategy - Dynamic mean reversion rotation.

    A portfolio strategy that applies Bollinger Bands analysis to multiple assets
    simultaneously and rotates capital to the asset with the strongest buy signal
    (furthest below upper band). Exits positions in assets with oversold signals
    (below lower band). Concentrates portfolio to top-1 opportunity.

    Entry Logic (Buy):
    - Asset's close price is above its Bollinger Band upper band (overbought)
    - Asset selected if it shows strongest overbought condition vs other candidates

    Exit Logic (Sell):
    - Asset's close price falls below its Bollinger Band lower band (oversold)
    - Position closed to preserve capital and rotate to better opportunities

    Parameters:
    - period (int): Number of periods for Bollinger Bands calculation [default: 20]

    Notes:
    - Concentrates positions in top-1 assets (k=1); can be adjusted
    - Dynamically rotates portfolio as opportunities change
    - More efficient capital deployment than equal-weight across all assets
    - Allocation uses 99% of available capital, reserves 1% as buffer
    """

    params = dict(period=20)

    def __init__(self):
        """Initialize Bollinger Bands indicators for all assets in the portfolio."""
        self.inds = {}
        for data in self.datas:
            self.inds[data] = {}
            bbands = bt.indicators.BollingerBands(data, period=self.params.period)
            self.inds[data]["buy"] = data.close - bbands.top
            self.inds[data]["sell"] = data.close - bbands.bot

    def next(self):
        """Execute portfolio rebalancing: close oversold positions, rotate to best overbought opportunity."""
        to_buy, to_sell, holding = [], [], []
        for data, ind in self.inds.items():
            if ind["buy"][0] > 0:
                to_buy.append(data)

            if ind["sell"][0] < 0:
                to_sell.append(data)

            if self.getposition(data).size > 0:
                holding.append(data)

        for sell in to_sell:
            if self.getposition(sell).size > 0:
                self.log(f"Leave: {sell.p.name}")
                self.close(sell)

        new_hold = list(set(to_buy + holding))

        for data in to_sell:
            if data in new_hold:
                new_hold.remove(data)

        k = 1
        if len(new_hold) > k:
            data_roc = {}
            for item in new_hold:
                data_roc[item] = self.inds[item]["buy"][0]
            # Sort by buy signal strength (distance from upper band)
            new_hold = sorted(data_roc.items(), key=lambda x: x[1], reverse=True)
            new_hold = new_hold[:k]
            new_hold = [item[0] for item in new_hold]

        if len(new_hold) > 0:
            weight = 1 / len(new_hold)
            for data in new_hold:
                self.order_target_percent(data, weight * 0.99)
