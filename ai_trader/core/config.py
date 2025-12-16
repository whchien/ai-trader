"""Configuration management using Pydantic for validation."""

from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class DataConfig(BaseModel):
    """Data loading configuration."""

    market: Literal["us", "tw"] = Field(default="tw", description="Market type")
    start_year: int = Field(default=2019, ge=2000, description="Start year for data")
    start_month: int = Field(default=1, ge=1, le=12, description="Start month for data")
    data_dir: Path = Field(default=Path("./data/tw_stock/"), description="Data directory")

    @field_validator("data_dir", mode="before")
    @classmethod
    def validate_data_dir(cls, v):
        """Convert string to Path."""
        if isinstance(v, str):
            return Path(v)
        return v


class BrokerConfig(BaseModel):
    """Broker configuration."""

    cash: int = Field(default=1000000, gt=0, description="Initial cash")
    commission: float = Field(default=0.001425, ge=0, lt=1, description="Commission rate")
    stake: float = Field(default=0.95, gt=0, le=1, description="Position sizing (% of capital)")

    @field_validator("cash")
    @classmethod
    def validate_cash(cls, v):
        """Ensure cash is positive."""
        if v <= 0:
            raise ValueError("Cash must be positive")
        return v


class BacktestConfig(BaseModel):
    """Backtesting configuration."""

    start_date: Optional[str] = Field(default=None, description="Backtest start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="Backtest end date (YYYY-MM-DD)")


class Config(BaseModel):
    """Main configuration for ai-trader."""

    data: DataConfig = Field(default_factory=DataConfig)
    broker: BrokerConfig = Field(default_factory=BrokerConfig)
    backtest: BacktestConfig = Field(default_factory=BacktestConfig)

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        """
        Load configuration from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            Config instance

        Example:
            >>> config = Config.from_yaml(Path("config/default.yaml"))
            >>> print(config.broker.cash)
            1000000
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(**data)

    def to_yaml(self, path: Path) -> None:
        """
        Save configuration to YAML file.

        Args:
            path: Path to save YAML file

        Example:
            >>> config = Config()
            >>> config.to_yaml(Path("config/my_config.yaml"))
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)
