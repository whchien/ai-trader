"""Pydantic models for MCP server requests and responses."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# ==================== Request Models ====================


class RunBacktestRequest(BaseModel):
    """Request model for running a backtest from YAML configuration."""

    config_file: str = Field(..., description="Path to YAML configuration file")
    strategy: Optional[str] = Field(None, description="Override strategy class name")
    cash: Optional[float] = Field(None, description="Override initial cash amount")
    commission: Optional[float] = Field(None, description="Override commission rate")


class QuickBacktestRequest(BaseModel):
    """Request model for quick backtest without configuration file."""

    strategy_name: str = Field(..., description="Strategy class name (e.g., SMAStrategy)")
    data_file: str = Field(..., description="Path to CSV data file")
    cash: float = Field(1000000, description="Initial cash amount")
    commission: float = Field(0.001425, description="Commission rate")
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format")


class FetchDataRequest(BaseModel):
    """Request model for fetching market data."""

    symbols: List[str] = Field(..., description="List of symbols to fetch (e.g., ['AAPL', 'MSFT'])")
    market: Literal["us_stock", "tw_stock", "crypto", "forex", "vix"] = Field(
        "us_stock", description="Market type"
    )
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: Optional[str] = Field(
        None, description="End date in YYYY-MM-DD format (defaults to today)"
    )
    output_dir: str = Field("./data", description="Output directory for saved CSV files")


class ListStrategiesRequest(BaseModel):
    """Request model for listing strategies."""

    strategy_type: Literal["classic", "portfolio", "all"] = Field(
        "all", description="Type of strategies to list"
    )


# ==================== Response Models ====================


class AnalyzerResults(BaseModel):
    """Analyzer metrics from a backtest."""

    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    total_return: Optional[float] = Field(None, description="Total return percentage")
    annualized_return: Optional[float] = Field(None, description="Annualized return percentage")
    max_drawdown: Optional[float] = Field(None, description="Maximum drawdown percentage")
    total_trades: Optional[int] = Field(None, description="Total number of trades")
    won_trades: Optional[int] = Field(None, description="Number of winning trades")
    lost_trades: Optional[int] = Field(None, description="Number of losing trades")
    win_rate: Optional[float] = Field(None, description="Win rate percentage")


class BacktestResult(BaseModel):
    """Result of a completed backtest."""

    strategy_name: str = Field(..., description="Name of the strategy used")
    initial_value: float = Field(..., description="Initial portfolio value")
    final_value: float = Field(..., description="Final portfolio value")
    profit_loss: float = Field(..., description="Absolute profit/loss amount")
    return_pct: float = Field(..., description="Return percentage")
    analyzers: AnalyzerResults = Field(..., description="Analyzer metrics")
    execution_time_seconds: float = Field(..., description="Backtest execution time in seconds")


class FetchedSymbol(BaseModel):
    """Information about a fetched symbol."""

    symbol: str = Field(..., description="Symbol that was fetched")
    filepath: str = Field(..., description="Path to saved CSV file")
    rows: int = Field(..., description="Number of rows in the data")


class FetchResult(BaseModel):
    """Result of data fetching operation."""

    successful_symbols: List[str] = Field(..., description="List of successfully fetched symbols")
    failed_symbols: List[str] = Field(..., description="List of symbols that failed to fetch")
    files_saved: List[FetchedSymbol] = Field(..., description="Details of saved files")
    total_symbols: int = Field(..., description="Total number of symbols requested")
    success_count: int = Field(..., description="Number of successfully fetched symbols")


class StrategyInfo(BaseModel):
    """Information about a single strategy."""

    name: str = Field(..., description="Strategy class name")
    description: str = Field(..., description="Short description of the strategy")
    type: Literal["classic", "portfolio"] = Field(..., description="Strategy type")


class StrategiesResult(BaseModel):
    """Result of listing strategies."""

    classic_strategies: List[StrategyInfo] = Field(
        ..., description="List of classic (single-stock) strategies"
    )
    portfolio_strategies: List[StrategyInfo] = Field(
        ..., description="List of portfolio (multi-stock) strategies"
    )
