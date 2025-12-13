"""
Custom Backtrader analyzer for lunar strategy performance tracking.
"""

from datetime import datetime
import backtrader as bt


class BasePerformanceAnalyzer(bt.Analyzer):
    """
    Custom analyzer that tracks lunar strategy trade details.

    Captures entry/exit dates, moon phase at entry, hold period,
    position size, and per-trade P&L for detailed analysis.
    """

    def __init__(self):
        """Initialize analyzer state."""
        super(BasePerformanceAnalyzer, self).__init__()
        self.trades = []
        self.current_trade = {}

    def notify_order(self, order):
        """
        Track order execution.

        Args:
            order: Backtrader order object
        """
        if order.status in [order.Completed]:
            if order.isbuy():
                # Start tracking new trade
                self.current_trade = {
                    'entry_date': self.strategy.data.datetime.date(0).isoformat(),
                    'entry_price': order.executed.price,
                    'entry_phase': self.strategy.moon_phase_angle[0],
                    'size': order.executed.size,
                    'entry_value': order.executed.value,
                    'entry_comm': order.executed.comm,
                }
            elif order.issell():
                # Complete trade record
                if self.current_trade:
                    exit_date = self.strategy.data.datetime.date(0)
                    entry_date_obj = datetime.fromisoformat(self.current_trade['entry_date']).date()

                    self.current_trade.update({
                        'exit_date': exit_date.isoformat(),
                        'exit_price': order.executed.price,
                        'exit_value': order.executed.value,
                        'exit_comm': order.executed.comm,
                        'hold_days': (exit_date - entry_date_obj).days,
                    })

                    # Calculate P&L
                    pnl = (
                        (self.current_trade['exit_price'] / self.current_trade['entry_price']) - 1
                    )
                    self.current_trade['pnl'] = pnl
                    self.current_trade['pnl_pct'] = pnl * 100

                    # Add to trades list
                    self.trades.append(self.current_trade.copy())
                    self.current_trade = {}

    def get_analysis(self):
        """
        Return analysis results.

        Returns:
            dict with 'trades' list and 'summary' statistics
        """
        if not self.trades:
            return {
                'trades': [],
                'summary': {
                    'total_trades': 0,
                    'avg_return': 0.0,
                    'avg_hold_days': 0.0,
                    'avg_entry_phase': 0.0,
                    'win_rate': 0.0,
                    'best_trade': 0.0,
                    'worst_trade': 0.0,
                }
            }

        # Calculate summary statistics
        total_trades = len(self.trades)
        returns = [t['pnl'] for t in self.trades]
        hold_days = [t['hold_days'] for t in self.trades]
        entry_phases = [t['entry_phase'] for t in self.trades]
        wins = sum(1 for r in returns if r > 0)

        summary = {
            'total_trades': total_trades,
            'avg_return': sum(returns) / total_trades,
            'avg_return_pct': (sum(returns) / total_trades) * 100,
            'avg_hold_days': sum(hold_days) / total_trades,
            'avg_entry_phase': sum(entry_phases) / total_trades,
            'win_rate': wins / total_trades,
            'win_rate_pct': (wins / total_trades) * 100,
            'best_trade': max(returns),
            'best_trade_pct': max(returns) * 100,
            'worst_trade': min(returns),
            'worst_trade_pct': min(returns) * 100,
            'winning_trades': wins,
            'losing_trades': total_trades - wins,
        }

        return {
            'trades': self.trades,
            'summary': summary
        }
