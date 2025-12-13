import backtrader as bt
import glob
import os
import pandas as pd
import warnings
from pathlib import Path
from typing import Optional, List, Type, Union

from ai_trader.core.logging import get_logger
from ai_trader.core.utils import extract_ticker_from_path
from ai_trader.data.fetchers.base import load_example

logger = get_logger(__name__)


class AITrader:
    """
    AITrader is a wrapper for Backtrader functions.

    .. deprecated:: 0.2.0
        AITrader is deprecated and will be removed in version 0.3.0.
        Use the utility functions in `ai_trader.utils.backtest` instead:

        - `run_backtest()` for quick backtests
        - `create_cerebro()`, `add_stock_data()`, etc. for step-by-step control
        - CLI tool: `ai-trader run config.yaml` for config-driven backtests

        See examples in `scripts/examples/` and docs for migration guide.

    This class still works but adds unnecessary abstraction over Backtrader.
    Direct Backtrader usage with utility functions is recommended.
    """

    def __init__(
        self,
        strategy: Optional[Type[bt.Strategy]] = None,
        cash: int = 1000000,
        commission: float = 0.001425,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        data_dir: Optional[str] = "./data/tw_stock/",
    ):
        """
        Initializes the AITrader with the given parameters.

        .. deprecated:: 0.2.0
            Use `ai_trader.utils.backtest.run_backtest()` or utility functions instead.

        Args:
            strategy: Strategy class (optional)
            cash: Initial cash amount
            commission: Commission rate
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)
            data_dir: Directory for loading portfolio data
        """
        # Emit deprecation warning
        warnings.warn(
            "AITrader is deprecated and will be removed in v0.3.0. "
            "Use ai_trader.utils.backtest functions instead. "
            "See scripts/examples/ for migration examples.",
            DeprecationWarning,
            stacklevel=2,
        )

        self.cash = cash
        self.commission = commission
        self.start_date = start_date
        self.end_date = end_date
        self.strategy = strategy
        self.strategy_params = {}
        self.data_dir = data_dir
        self.cerebro = bt.Cerebro()

        # State tracking
        self._broker_configured = False
        self._sizer_configured = False
        self._analyzers_configured = False

        logger.warning(
            f"AITrader is deprecated. Consider using ai_trader.utils.backtest instead. "
            f"Initialized: cash=${cash:,}, commission={commission:.4f}"
        )

    def log(self, txt: str) -> None:
        """
        Logs a message (deprecated - use logging instead).
        """
        logger.info(txt)

    def add_strategy(self, strategy: Type[bt.Strategy], **strategy_params) -> None:
        """
        Adds a trading strategy to the cerebro instance.

        Args:
            strategy: Strategy class (not instance)
            **strategy_params: Parameters to pass to the strategy

        Example:
            >>> trader.add_strategy(SMAStrategy, fast_period=10, slow_period=30)
        """
        self.strategy = strategy
        self.strategy_params = strategy_params
        self.cerebro.addstrategy(strategy, **strategy_params)
        logger.info(f"Added strategy: {strategy.__name__} with params: {strategy_params}")

    def add_one_stock(self, df: Optional[pd.DataFrame] = None, file_path: Optional[str] = None) -> None:
        """
        Loads single stock data into the cerebro instance.

        Args:
            df: DataFrame with stock data (optional)
            file_path: Path to CSV file (optional)
        """
        if df is None and file_path is None:
            df = load_example()
        elif file_path is not None:
            # Load from file
            date_col = "date" if "tw" in self.data_dir.lower() else "Date"
            df = pd.read_csv(file_path, parse_dates=[date_col], index_col=[date_col])

        if self.start_date or self.end_date:
            df = df[self.start_date : self.end_date]

        feed = bt.feeds.PandasData(
            dataname=df,
            openinterest=None,
            timeframe=bt.TimeFrame.Days,
        )
        self.cerebro.adddata(feed)
        logger.info(f"Added single stock data: {len(df)} rows")

    def add_stocks(self, date_col: str = "date") -> None:
        """
        Loads portfolio data for multiple stocks into the cerebro instance.
        """
        files = glob.glob(os.path.join(self.data_dir, "*.csv"))

        for file in files:
            df = pd.read_csv(file, parse_dates=[date_col], index_col=[date_col])
            df = df[self.start_date : self.end_date]
            ticker = extract_ticker_from_path(file)
            data = bt.feeds.PandasData(
                dataname=df, name=ticker, timeframe=bt.TimeFrame.Days, plot=False
            )
            self.cerebro.adddata(data, name=ticker)

    def add_analyzers(self, analyzers: Optional[List[str]] = None) -> None:
        """
        Adds analyzers to the cerebro instance.

        Args:
            analyzers: List of analyzer names or None for defaults
                      Supported: 'sharpe', 'drawdown', 'returns', 'trades', 'sqn'

        Example:
            >>> trader.add_analyzers(['sharpe', 'drawdown', 'trades'])
        """
        if analyzers is None:
            analyzers = ['sharpe', 'drawdown', 'returns']

        analyzer_map = {
            'sharpe': (bt.analyzers.SharpeRatio, "SharpeRatio"),
            'drawdown': (bt.analyzers.DrawDown, "DrawDown"),
            'returns': (bt.analyzers.Returns, "Returns"),
            'trades': (bt.analyzers.TradeAnalyzer, "TradeAnalyzer"),
            'sqn': (bt.analyzers.SQN, "SQN"),
        }

        for name in analyzers:
            if name in analyzer_map:
                analyzer_class, analyzer_name = analyzer_map[name]
                self.cerebro.addanalyzer(analyzer_class, _name=analyzer_name)

        self._analyzers_configured = True
        logger.debug(f"Added analyzers: {analyzers}")

    def add_broker(self) -> None:
        """
        Configures the broker settings.
        """
        self.cerebro.broker.setcash(self.cash)
        self.cerebro.broker.setcommission(commission=self.commission)
        self._broker_configured = True
        logger.debug(f"Broker configured: Starting Value ${self.cerebro.broker.getvalue():,}")

    def add_sizer(self, sizer_type: str = "percent", **sizer_params) -> None:
        """
        Sets the sizer for position sizing.

        Args:
            sizer_type: Type of sizer ('percent' or 'fixed')
            **sizer_params: Parameters for the sizer

        Example:
            >>> trader.add_sizer("percent", percents=90)
            >>> trader.add_sizer("fixed", stake=100)
        """
        if sizer_type == "percent":
            percents = sizer_params.get("percents", 95)
            self.cerebro.addsizer(bt.sizers.PercentSizer, percents=percents)
            logger.debug(f"Sizer set to {percents}% of capital")
        elif sizer_type == "fixed":
            stake = sizer_params.get("stake", 10)
            self.cerebro.addsizer(bt.sizers.FixedSize, stake=stake)
            logger.debug(f"Sizer set to fixed stake of {stake}")
        else:
            # Default to percent
            self.cerebro.addsizer(bt.sizers.PercentSizer, percents=95)
            logger.debug("Sizer set to default 95%")

        self._sizer_configured = True

    def analyze(self, result: List[bt.Strategy]) -> None:
        """
        Analyzes the results of the backtest.
        """
        self.log(f"Ending value: {round(self.cerebro.broker.getvalue())}")

        returns = result[0].analyzers.Returns.get_analysis()
        self.log(f"Total Returns: {round(returns['rtot'], 2)}")
        self.log(f"Normalized Returns: {round(returns['rnorm'], 2)}")

        sharpe = result[0].analyzers.SharpeRatio.get_analysis().get("sharperatio")
        if sharpe:
            self.log(f"Sharpe Ratio: {round(sharpe, 2)}")

        drawdown = (
            result[0].analyzers.DrawDown.get_analysis().get("max", {}).get("drawdown")
        )
        if drawdown:
            self.log(f"Max Drawdown: {round(drawdown, 2)}")

    def run(self, auto_setup: Optional[bool] = None) -> List[bt.Strategy]:
        """
        Runs the backtest with optional automatic setup.

        Args:
            auto_setup: If True, automatically configure broker/sizer/analyzers.
                       If None (default), enables backward compatibility mode.
                       If False, user must call setup methods manually.

        Returns:
            List of strategy instances with results

        Raises:
            ValueError: If no strategy specified or no data loaded

        Example:
            >>> # Modern explicit workflow (recommended)
            >>> trader = AITrader()
            >>> trader.add_one_stock("data/AAPL.csv")
            >>> trader.add_strategy(SMAStrategy, period=20)
            >>> results = trader.run(auto_setup=True)
            >>>
            >>> # Manual control
            >>> trader.add_broker()
            >>> trader.add_sizer("percent", percents=90)
            >>> trader.add_analyzers(['sharpe', 'trades'])
            >>> results = trader.run(auto_setup=False)
        """
        # Backward compatibility: detect old usage pattern
        if auto_setup is None:
            # Check if data was explicitly loaded
            if not self.cerebro.datas and self.data_dir and self.strategy:
                warnings.warn(
                    "Calling run() without loading data is deprecated. "
                    "The auto-loading from data_dir will be removed in v0.3.0. "
                    "Please call add_stocks() or add_one_stock() explicitly before run().",
                    DeprecationWarning,
                    stacklevel=2
                )
                # Backward compatible behavior - auto-load stocks
                self.add_stocks()
                auto_setup = True
            else:
                auto_setup = True

        # Validation
        if not self.strategy:
            raise ValueError(
                "No strategy specified. Call add_strategy() before run()."
            )

        if not self.cerebro.datas:
            raise ValueError(
                "No data loaded. Call add_one_stock() or add_stocks() before run()."
            )

        # Auto-setup if requested
        if auto_setup:
            if not self._broker_configured:
                self.add_broker()
            if not self._sizer_configured:
                self.add_sizer()
            if not self._analyzers_configured:
                self.add_analyzers()

        # Run backtest
        logger.info(f"Running backtest with {self.strategy.__name__}")
        logger.info(f"Starting portfolio value: ${self.cerebro.broker.getvalue():,.2f}")

        result = self.cerebro.run()

        # Analyze results
        logger.info(f"Backtest complete: Final value ${self.cerebro.broker.getvalue():,.2f}")
        self.analyze(result)

        return result

    def plot(self) -> None:
        """
        Plots the results of the backtest.
        """
        self.cerebro.plot()
