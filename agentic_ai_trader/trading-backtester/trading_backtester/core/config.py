"""Configuration management for the trading backtester."""

import os
import sys
from pathlib import Path
from typing import Any, Dict

import yaml


class Config:
    """Configuration manager for the trading backtester."""

    def __init__(self):
        self._config = self._load_config()
        self._setup_ai_trader_path()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        return {
            # Google Cloud Configuration
            "google_cloud_project": os.getenv("GOOGLE_CLOUD_PROJECT"),
            "google_cloud_location": os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            "use_vertex_ai": os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "1") == "1",
            # Model Configuration
            "models": {
                "root_agent": os.getenv("ROOT_AGENT_MODEL", "gemini-2.5-flash"),
                "strategy_analysis": os.getenv("STRATEGY_ANALYSIS_MODEL", "gemini-2.5-pro"),
                "backtesting_execution": os.getenv(
                    "BACKTESTING_EXECUTION_MODEL", "gemini-2.5-flash"
                ),
                "performance_evaluation": os.getenv(
                    "PERFORMANCE_EVALUATION_MODEL", "gemini-2.5-pro"
                ),
                "risk_assessment": os.getenv("RISK_ASSESSMENT_MODEL", "gemini-2.5-pro"),
                "optimization": os.getenv("OPTIMIZATION_MODEL", "gemini-2.5-pro"),
            },
            # Data Configuration
            "data": {
                "default_dir": os.getenv("DEFAULT_DATA_DIR", "../../data"),
                "ai_trader_path": os.getenv("AI_TRADER_PATH", "../../ai_trader"),
            },
            # Backtesting Configuration
            "backtesting": {
                "default_cash": float(os.getenv("DEFAULT_CASH", "1000000")),
                "default_commission": float(os.getenv("DEFAULT_COMMISSION", "0.001425")),
                "max_parallel_backtests": int(os.getenv("MAX_PARALLEL_BACKTESTS", "4")),
            },
            # Logging Configuration
            "logging": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
            },
            # Optional integrations
            "wandb": {
                "project_id": os.getenv("WANDB_PROJECT_ID"),
                "api_key": os.getenv("WANDB_API_KEY"),
            },
        }

    def _setup_ai_trader_path(self):
        """Add ai_trader to Python path for imports."""
        ai_trader_path = Path(self._config["data"]["ai_trader_path"]).resolve()
        if ai_trader_path.exists() and str(ai_trader_path.parent) not in sys.path:
            sys.path.insert(0, str(ai_trader_path.parent))

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)."""
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_model(self, agent_name: str) -> str:
        """Get model name for a specific agent."""
        return self.get(f"models.{agent_name}", "gemini-2.5-flash")

    def validate(self) -> bool:
        """Validate required configuration."""
        required_fields = [
            "google_cloud_project",
            "google_cloud_location",
        ]

        for field in required_fields:
            if not self.get(field):
                raise ValueError(f"Required configuration field '{field}' is missing")

        return True


# Global configuration instance
config = Config()


def load_strategy_config(config_path: str) -> Dict[str, Any]:
    """Load strategy configuration from YAML file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def save_strategy_config(config_data: Dict[str, Any], config_path: str) -> None:
    """Save strategy configuration to YAML file."""
    with open(config_path, "w") as f:
        yaml.dump(config_data, f, default_flow_style=False, indent=2)
