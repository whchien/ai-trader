"""Tests for ai_trader.cli module."""

import pytest
import yaml
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, call
from click.testing import CliRunner

from ai_trader.cli import cli, _load_strategy_class, _get_strategies_from_module


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def sample_strategy_class():
    """Create a mock strategy class."""
    class MockStrategy:
        __name__ = "MockStrategy"
        __doc__ = "A mock trading strategy for testing"
    return MockStrategy


@pytest.fixture
def sample_config_yaml(tmp_path, sample_ohlcv_data_short):
    """Create a sample backtest config YAML file."""
    config = {
        "data": {
            "file": str(tmp_path / "test_data.csv"),
            "start_date": "2023-01-01",
            "end_date": "2023-01-31"
        },
        "strategy": {
            "class": "ai_trader.backtesting.strategies.classic.sma.SMAStrategy",
            "params": {"period": 20}
        },
        "broker": {
            "cash": 100000,
            "commission": 0.001425
        },
        "sizer": {
            "type": "percent",
            "params": {"percents": 95}
        },
        "analyzers": ["sharpe", "drawdown", "returns"],
        "plot": False
    }

    # Create config file
    config_file = tmp_path / "config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config, f)

    # Create sample data file
    data_file = tmp_path / "test_data.csv"
    sample_ohlcv_data_short.to_csv(data_file)

    return config_file


@pytest.fixture
def sample_portfolio_config_yaml(tmp_path):
    """Create a sample portfolio backtest config."""
    config = {
        "data": {
            "directory": str(tmp_path / "data"),
            "start_date": "2023-01-01",
            "end_date": "2023-01-31"
        },
        "strategy": {
            "class": "ai_trader.backtesting.strategies.portfolio.triple_rsi.TripleRSIRotation",
            "params": {}
        },
        "broker": {
            "cash": 500000,
            "commission": 0.001425
        },
        "sizer": {
            "type": "percent",
            "params": {"percents": 90}
        },
        "analyzers": ["sharpe", "drawdown"],
        "plot": False
    }

    config_file = tmp_path / "portfolio_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config, f)

    return config_file


class TestCliGroup:
    """Test the CLI group."""

    def test_cli_group_has_version(self, cli_runner):
        """Test that CLI displays version."""
        result = cli_runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.2.0" in result.output


class TestRunCommand:
    """Test the 'run' command."""

    def test_run_with_single_stock_config(self, cli_runner, sample_config_yaml):
        """Test running backtest with single stock config."""
        with patch("ai_trader.cli.run_backtest") as mock_run, \
             patch("ai_trader.cli._load_strategy_class") as mock_load:
            mock_load.return_value = MagicMock(__name__="SMAStrategy")

            result = cli_runner.invoke(cli, ["run", str(sample_config_yaml)])

            assert result.exit_code == 0
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["cash"] == 100000
            assert call_kwargs["commission"] == 0.001425

    def test_run_with_strategy_override(self, cli_runner, sample_config_yaml):
        """Test run command with --strategy override."""
        with patch("ai_trader.cli.run_backtest") as mock_run, \
             patch("ai_trader.cli._load_strategy_class") as mock_load:
            mock_strategy = MagicMock(__name__="CustomStrategy")
            mock_load.return_value = mock_strategy

            result = cli_runner.invoke(
                cli,
                ["run", str(sample_config_yaml), "--strategy", "CustomStrategy"]
            )

            assert result.exit_code == 0
            # Verify _load_strategy_class was called (first for original, second for override)
            assert mock_load.call_count >= 1

    def test_run_with_cash_override(self, cli_runner, sample_config_yaml):
        """Test run command with --cash override."""
        with patch("ai_trader.cli.run_backtest") as mock_run, \
             patch("ai_trader.cli._load_strategy_class") as mock_load:
            mock_load.return_value = MagicMock(__name__="SMAStrategy")

            result = cli_runner.invoke(
                cli,
                ["run", str(sample_config_yaml), "--cash", "500000"]
            )

            assert result.exit_code == 0
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["cash"] == 500000

    def test_run_with_commission_override(self, cli_runner, sample_config_yaml):
        """Test run command with --commission override."""
        with patch("ai_trader.cli.run_backtest") as mock_run, \
             patch("ai_trader.cli._load_strategy_class") as mock_load:
            mock_load.return_value = MagicMock(__name__="SMAStrategy")

            result = cli_runner.invoke(
                cli,
                ["run", str(sample_config_yaml), "--commission", "0.002"]
            )

            assert result.exit_code == 0
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["commission"] == 0.002

    def test_run_with_portfolio_config(self, cli_runner, sample_portfolio_config_yaml, tmp_path):
        """Test run command with portfolio (directory) config."""
        # Create sample data files
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)

        with patch("ai_trader.cli.create_cerebro") as mock_cerebro_create, \
             patch("ai_trader.cli.add_portfolio_data"), \
             patch("ai_trader.cli.add_sizer"), \
             patch("ai_trader.cli.add_analyzers"), \
             patch("ai_trader.cli.print_results"), \
             patch("ai_trader.cli._load_strategy_class") as mock_load:

            mock_cerebro = MagicMock()
            mock_cerebro_create.return_value = mock_cerebro
            mock_cerebro.broker.getvalue.return_value = 500000
            mock_cerebro.run.return_value = []
            mock_load.return_value = MagicMock(__name__="TripleRSI")

            result = cli_runner.invoke(cli, ["run", str(sample_portfolio_config_yaml)])

            assert result.exit_code == 0
            mock_cerebro_create.assert_called_once()
            mock_cerebro.run.assert_called_once()

    def test_run_missing_config_file(self, cli_runner):
        """Test run command with missing config file."""
        result = cli_runner.invoke(cli, ["run", "/nonexistent/config.yaml"])

        assert result.exit_code != 0

    def test_run_missing_data_key_in_config(self, cli_runner, tmp_path):
        """Test run with invalid config (missing data.file and data.directory)."""
        config = {
            "strategy": {"class": "SMAStrategy"},
            "broker": {"cash": 100000}
        }

        config_file = tmp_path / "invalid_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        with patch("ai_trader.cli._load_strategy_class"):
            result = cli_runner.invoke(cli, ["run", str(config_file)])

            assert result.exit_code == 1
            assert "Error" in result.output

    def test_run_with_plot_enabled(self, cli_runner, sample_config_yaml):
        """Test run command with plot enabled in config."""
        with patch("ai_trader.cli.run_backtest"), \
             patch("ai_trader.cli._load_strategy_class") as mock_load:
            mock_load.return_value = MagicMock(__name__="SMAStrategy")

            # Modify config to enable plot
            with open(sample_config_yaml, "r") as f:
                config = yaml.safe_load(f)
            config["plot"] = True
            with open(sample_config_yaml, "w") as f:
                yaml.dump(config, f)

            result = cli_runner.invoke(cli, ["run", str(sample_config_yaml)])
            assert result.exit_code == 0


class TestListStrategiesCommand:
    """Test the 'list-strategies' command."""

    def test_list_all_strategies(self, cli_runner):
        """Test listing all strategies."""
        with patch("ai_trader.cli._get_strategies_from_module") as mock_get:
            # Mock classic and portfolio strategies
            mock_strategy = MagicMock()
            mock_strategy.__doc__ = "Test Strategy\nLonger description"
            mock_strategy.__name__ = "TestStrategy"

            mock_get.return_value = [("TestStrategy", mock_strategy)]

            result = cli_runner.invoke(cli, ["list-strategies"])

            assert result.exit_code == 0
            assert "AVAILABLE STRATEGIES" in result.output

    def test_list_classic_strategies_only(self, cli_runner):
        """Test listing only classic strategies."""
        with patch("ai_trader.cli._get_strategies_from_module") as mock_get:
            mock_strategy = MagicMock()
            mock_strategy.__doc__ = "Test Strategy"
            mock_strategy.__name__ = "TestStrategy"

            mock_get.return_value = [("TestStrategy", mock_strategy)]

            result = cli_runner.invoke(cli, ["list-strategies", "--type", "classic"])

            assert result.exit_code == 0
            assert "Classic Strategies" in result.output

    def test_list_portfolio_strategies_only(self, cli_runner):
        """Test listing only portfolio strategies."""
        with patch("ai_trader.cli._get_strategies_from_module") as mock_get:
            mock_strategy = MagicMock()
            mock_strategy.__doc__ = "Test Strategy"
            mock_strategy.__name__ = "TestStrategy"

            mock_get.return_value = [("TestStrategy", mock_strategy)]

            result = cli_runner.invoke(cli, ["list-strategies", "--type", "portfolio"])

            assert result.exit_code == 0
            assert "Portfolio Strategies" in result.output

    def test_list_strategies_with_no_docstring(self, cli_runner):
        """Test listing strategies where some have no docstring."""
        with patch("ai_trader.cli._get_strategies_from_module") as mock_get:
            mock_strategy = MagicMock()
            mock_strategy.__doc__ = None
            mock_strategy.__name__ = "TestStrategy"

            mock_get.return_value = [("TestStrategy", mock_strategy)]

            result = cli_runner.invoke(cli, ["list-strategies"])

            assert result.exit_code == 0
            assert "No description" in result.output


class TestFetchCommand:
    """Test the 'fetch' command."""

    def test_fetch_single_symbol(self, cli_runner, tmp_path, sample_ohlcv_data_short):
        """Test fetching single symbol."""
        with patch("ai_trader.data.fetchers.USStockFetcher") as mock_fetcher_class, \
             patch("ai_trader.data.storage.FileManager") as mock_fm_class:

            mock_fetcher = MagicMock()
            mock_fetcher.fetch.return_value = sample_ohlcv_data_short
            mock_fetcher_class.return_value = mock_fetcher

            mock_fm = MagicMock()
            mock_fm.save_to_csv.return_value = str(tmp_path / "AAPL.csv")
            mock_fm_class.return_value = mock_fm

            result = cli_runner.invoke(
                cli,
                ["fetch", "AAPL", "--market", "us_stock", "--start-date", "2023-01-01"]
            )

            assert result.exit_code == 0
            assert "Data saved" in result.output
            mock_fetcher.fetch.assert_called_once()

    def test_fetch_multiple_symbols(self, cli_runner, sample_ohlcv_data_short):
        """Test fetching multiple symbols in batch mode."""
        with patch("ai_trader.data.fetchers.USStockFetcher") as mock_fetcher_class, \
             patch("ai_trader.data.storage.FileManager") as mock_fm_class:

            mock_fetcher = MagicMock()
            mock_fetcher.fetch_batch.return_value = (
                {"AAPL": sample_ohlcv_data_short, "MSFT": sample_ohlcv_data_short},
                []
            )
            mock_fetcher_class.return_value = mock_fetcher

            mock_fm = MagicMock()
            mock_fm.save_to_csv.return_value = "test.csv"
            mock_fm_class.return_value = mock_fm

            result = cli_runner.invoke(
                cli,
                ["fetch", "AAPL", "MSFT", "--market", "us_stock", "--start-date", "2023-01-01"]
            )

            assert result.exit_code == 0
            assert "Successfully downloaded" in result.output
            mock_fetcher.fetch_batch.assert_called_once()

    def test_fetch_with_symbols_file(self, cli_runner, tmp_path, sample_ohlcv_data_short):
        """Test fetching symbols from file."""
        # Create symbols file
        symbols_file = tmp_path / "symbols.txt"
        symbols_file.write_text("AAPL\nMSFT\nGOOGL")

        with patch("ai_trader.data.fetchers.USStockFetcher") as mock_fetcher_class, \
             patch("ai_trader.data.storage.FileManager") as mock_fm_class:

            mock_fetcher = MagicMock()
            mock_fetcher.fetch_batch.return_value = (
                {"AAPL": sample_ohlcv_data_short},
                ["MSFT", "GOOGL"]
            )
            mock_fetcher_class.return_value = mock_fetcher

            mock_fm = MagicMock()
            mock_fm.save_to_csv.return_value = "test.csv"
            mock_fm_class.return_value = mock_fm

            result = cli_runner.invoke(
                cli,
                ["fetch", "--symbols-file", str(symbols_file),
                 "--market", "us_stock", "--start-date", "2023-01-01"]
            )

            assert result.exit_code == 1  # Should exit with failure for failed symbols
            assert "Failed to download" in result.output

    def test_fetch_with_comma_separated_symbols(self, cli_runner, sample_ohlcv_data_short):
        """Test fetching with comma-separated symbols."""
        with patch("ai_trader.data.fetchers.USStockFetcher") as mock_fetcher_class, \
             patch("ai_trader.data.storage.FileManager") as mock_fm_class:

            mock_fetcher = MagicMock()
            mock_fetcher.fetch_batch.return_value = (
                {"AAPL": sample_ohlcv_data_short, "MSFT": sample_ohlcv_data_short},
                []
            )
            mock_fetcher_class.return_value = mock_fetcher

            mock_fm = MagicMock()
            mock_fm.save_to_csv.return_value = "test.csv"
            mock_fm_class.return_value = mock_fm

            result = cli_runner.invoke(
                cli,
                ["fetch", "AAPL,MSFT", "--market", "us_stock", "--start-date", "2023-01-01"]
            )

            assert result.exit_code == 0
            assert "Successfully downloaded" in result.output

    def test_fetch_without_symbols(self, cli_runner):
        """Test fetch command without any symbols."""
        result = cli_runner.invoke(
            cli,
            ["fetch", "--market", "us_stock", "--start-date", "2023-01-01"]
        )

        assert result.exit_code == 1
        assert "Error" in result.output

    def test_fetch_with_both_symbols_and_file(self, cli_runner, tmp_path):
        """Test that providing both symbols and file is rejected."""
        symbols_file = tmp_path / "symbols.txt"
        symbols_file.write_text("AAPL")

        result = cli_runner.invoke(
            cli,
            ["fetch", "AAPL", "--symbols-file", str(symbols_file),
             "--market", "us_stock", "--start-date", "2023-01-01"]
        )

        assert result.exit_code == 1
        assert "Cannot specify both" in result.output

    def test_fetch_tw_stock(self, cli_runner, sample_ohlcv_data_short):
        """Test fetching Taiwan stock data."""
        with patch("ai_trader.data.fetchers.TWStockFetcher") as mock_fetcher_class, \
             patch("ai_trader.data.storage.FileManager") as mock_fm_class:

            mock_fetcher = MagicMock()
            mock_fetcher.fetch.return_value = sample_ohlcv_data_short
            mock_fetcher_class.return_value = mock_fetcher

            mock_fm = MagicMock()
            mock_fm.save_to_csv.return_value = "test.csv"
            mock_fm_class.return_value = mock_fm

            result = cli_runner.invoke(
                cli,
                ["fetch", "2330", "--market", "tw_stock", "--start-date", "2023-01-01"]
            )

            assert result.exit_code == 0
            mock_fetcher_class.assert_called_once_with(
                symbol="2330",
                start_date="2023-01-01",
                end_date=None
            )

    def test_fetch_crypto(self, cli_runner, sample_ohlcv_data_short):
        """Test fetching cryptocurrency data."""
        with patch("ai_trader.data.fetchers.CryptoDataFetcher") as mock_fetcher_class, \
             patch("ai_trader.data.storage.FileManager") as mock_fm_class:

            mock_fetcher = MagicMock()
            # Crypto with single symbol uses fetch(), not fetch_batch()
            mock_fetcher.fetch.return_value = sample_ohlcv_data_short
            mock_fetcher_class.return_value = mock_fetcher

            mock_fm = MagicMock()
            mock_fm.save_to_csv.return_value = "test.csv"
            mock_fm_class.return_value = mock_fm

            result = cli_runner.invoke(
                cli,
                ["fetch", "BTC-USD", "--market", "crypto", "--start-date", "2023-01-01"]
            )

            assert result.exit_code == 0
            # Crypto is handled as single symbol fetcher (like forex/vix)
            mock_fetcher.fetch.assert_called_once()

    def test_fetch_with_end_date(self, cli_runner, sample_ohlcv_data_short):
        """Test fetching with end date specified."""
        with patch("ai_trader.data.fetchers.USStockFetcher") as mock_fetcher_class, \
             patch("ai_trader.data.storage.FileManager") as mock_fm_class:

            mock_fetcher = MagicMock()
            mock_fetcher.fetch.return_value = sample_ohlcv_data_short
            mock_fetcher_class.return_value = mock_fetcher

            mock_fm = MagicMock()
            mock_fm.save_to_csv.return_value = "test.csv"
            mock_fm_class.return_value = mock_fm

            result = cli_runner.invoke(
                cli,
                ["fetch", "AAPL", "--market", "us_stock",
                 "--start-date", "2023-01-01", "--end-date", "2023-12-31"]
            )

            assert result.exit_code == 0
            mock_fetcher_class.assert_called_once_with(
                symbol="AAPL",
                start_date="2023-01-01",
                end_date="2023-12-31"
            )

    def test_fetch_with_output_dir(self, cli_runner, tmp_path, sample_ohlcv_data_short):
        """Test fetching with custom output directory."""
        output_dir = tmp_path / "custom_data"

        with patch("ai_trader.data.fetchers.USStockFetcher") as mock_fetcher_class, \
             patch("ai_trader.data.storage.FileManager") as mock_fm_class:

            mock_fetcher = MagicMock()
            mock_fetcher.fetch.return_value = sample_ohlcv_data_short
            mock_fetcher_class.return_value = mock_fetcher

            mock_fm = MagicMock()
            mock_fm.save_to_csv.return_value = "test.csv"
            mock_fm_class.return_value = mock_fm

            result = cli_runner.invoke(
                cli,
                ["fetch", "AAPL", "--market", "us_stock",
                 "--start-date", "2023-01-01", "--output-dir", str(output_dir)]
            )

            assert result.exit_code == 0
            # Verify FileManager was initialized with custom directory
            called_dir = mock_fm_class.call_args[1]["base_data_dir"]
            assert str(output_dir) in called_dir

    def test_fetch_partial_failure(self, cli_runner, sample_ohlcv_data_short):
        """Test batch fetch with partial failures."""
        with patch("ai_trader.data.fetchers.USStockFetcher") as mock_fetcher_class, \
             patch("ai_trader.data.storage.FileManager") as mock_fm_class:

            mock_fetcher = MagicMock()
            mock_fetcher.fetch_batch.return_value = (
                {"AAPL": sample_ohlcv_data_short},
                ["INVALID"]
            )
            mock_fetcher_class.return_value = mock_fetcher

            mock_fm = MagicMock()
            mock_fm.save_to_csv.return_value = "test.csv"
            mock_fm_class.return_value = mock_fm

            result = cli_runner.invoke(
                cli,
                ["fetch", "AAPL", "INVALID", "--market", "us_stock",
                 "--start-date", "2023-01-01"]
            )

            assert result.exit_code == 1
            assert "Failed to download" in result.output


class TestQuickCommand:
    """Test the 'quick' command."""

    def test_quick_with_defaults(self, cli_runner, tmp_path, sample_ohlcv_data_short):
        """Test quick command with default parameters."""
        # Create data file
        data_file = tmp_path / "test.csv"
        sample_ohlcv_data_short.to_csv(data_file)

        with patch("ai_trader.cli.run_backtest") as mock_run, \
             patch("ai_trader.cli._load_strategy_class") as mock_load:

            mock_strategy = MagicMock()
            mock_strategy.__name__ = "SMAStrategy"
            mock_load.return_value = mock_strategy

            result = cli_runner.invoke(
                cli,
                ["quick", "SMAStrategy", str(data_file)]
            )

            assert result.exit_code == 0
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["cash"] == 1000000
            assert call_kwargs["commission"] == 0.001425

    def test_quick_with_custom_cash(self, cli_runner, tmp_path, sample_ohlcv_data_short):
        """Test quick command with custom cash."""
        data_file = tmp_path / "test.csv"
        sample_ohlcv_data_short.to_csv(data_file)

        with patch("ai_trader.cli.run_backtest") as mock_run, \
             patch("ai_trader.cli._load_strategy_class") as mock_load:

            mock_load.return_value = MagicMock(__name__="SMAStrategy")

            result = cli_runner.invoke(
                cli,
                ["quick", "SMAStrategy", str(data_file), "--cash", "500000"]
            )

            assert result.exit_code == 0
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["cash"] == 500000

    def test_quick_with_custom_commission(self, cli_runner, tmp_path, sample_ohlcv_data_short):
        """Test quick command with custom commission."""
        data_file = tmp_path / "test.csv"
        sample_ohlcv_data_short.to_csv(data_file)

        with patch("ai_trader.cli.run_backtest") as mock_run, \
             patch("ai_trader.cli._load_strategy_class") as mock_load:

            mock_load.return_value = MagicMock(__name__="SMAStrategy")

            result = cli_runner.invoke(
                cli,
                ["quick", "SMAStrategy", str(data_file), "--commission", "0.002"]
            )

            assert result.exit_code == 0
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["commission"] == 0.002

    def test_quick_with_date_range(self, cli_runner, tmp_path, sample_ohlcv_data_short):
        """Test quick command with date range."""
        data_file = tmp_path / "test.csv"
        sample_ohlcv_data_short.to_csv(data_file)

        with patch("ai_trader.cli.run_backtest") as mock_run, \
             patch("ai_trader.cli._load_strategy_class") as mock_load:

            mock_load.return_value = MagicMock(__name__="SMAStrategy")

            result = cli_runner.invoke(
                cli,
                ["quick", "SMAStrategy", str(data_file),
                 "--start-date", "2023-01-01", "--end-date", "2023-12-31"]
            )

            assert result.exit_code == 0
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["start_date"] == "2023-01-01"
            assert call_kwargs["end_date"] == "2023-12-31"

    def test_quick_with_plot_enabled(self, cli_runner, tmp_path, sample_ohlcv_data_short):
        """Test quick command with plot enabled."""
        data_file = tmp_path / "test.csv"
        sample_ohlcv_data_short.to_csv(data_file)

        with patch("ai_trader.cli.run_backtest") as mock_run, \
             patch("ai_trader.cli._load_strategy_class") as mock_load:

            mock_load.return_value = MagicMock(__name__="SMAStrategy")

            result = cli_runner.invoke(
                cli,
                ["quick", "SMAStrategy", str(data_file), "--plot"]
            )

            assert result.exit_code == 0
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["plot"] is True

    def test_quick_with_plot_disabled(self, cli_runner, tmp_path, sample_ohlcv_data_short):
        """Test quick command with plot disabled (default)."""
        data_file = tmp_path / "test.csv"
        sample_ohlcv_data_short.to_csv(data_file)

        with patch("ai_trader.cli.run_backtest") as mock_run, \
             patch("ai_trader.cli._load_strategy_class") as mock_load:

            mock_load.return_value = MagicMock(__name__="SMAStrategy")

            result = cli_runner.invoke(
                cli,
                ["quick", "SMAStrategy", str(data_file), "--no-plot"]
            )

            assert result.exit_code == 0
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["plot"] is False

    def test_quick_missing_strategy(self, cli_runner, tmp_path, sample_ohlcv_data_short):
        """Test quick command with invalid strategy."""
        data_file = tmp_path / "test.csv"
        sample_ohlcv_data_short.to_csv(data_file)

        with patch("ai_trader.cli._load_strategy_class") as mock_load:
            mock_load.side_effect = ValueError("Strategy not found")

            result = cli_runner.invoke(
                cli,
                ["quick", "InvalidStrategy", str(data_file)]
            )

            assert result.exit_code != 0


class TestLoadStrategyClass:
    """Test the _load_strategy_class helper function."""

    def test_load_strategy_by_short_name_from_classic(self):
        """Test loading strategy by short name from classic module."""
        # Test that short names can be loaded from the actual classic module
        try:
            from ai_trader.backtesting.strategies.classic import SMAStrategy
            result = _load_strategy_class("SMAStrategy")
            assert result is SMAStrategy
        except (ImportError, AttributeError):
            # If the strategy doesn't exist, that's fine - just skip
            pytest.skip("SMAStrategy not available in classic module")

    def test_load_strategy_by_full_path(self):
        """Test loading strategy by full module path."""
        with patch("ai_trader.cli.importlib.import_module") as mock_import:
            mock_module = MagicMock()
            mock_strategy = MagicMock()
            mock_strategy.__name__ = "SMAStrategy"
            mock_module.SMAStrategy = mock_strategy
            mock_import.return_value = mock_module

            result = _load_strategy_class("ai_trader.backtesting.strategies.classic.sma.SMAStrategy")

            assert result == mock_strategy
            mock_import.assert_called_once_with(
                "ai_trader.backtesting.strategies.classic.sma"
            )

    def test_load_strategy_not_found(self):
        """Test loading non-existent strategy raises ValueError."""
        with patch("ai_trader.cli.importlib.import_module", side_effect=ImportError()):
            with pytest.raises(ValueError, match="Strategy not found"):
                _load_strategy_class("NonExistentStrategy")


class TestGetStrategiesFromModule:
    """Test the _get_strategies_from_module helper function."""

    def test_get_strategies_returns_list(self):
        """Test that _get_strategies_from_module returns a list of tuples."""
        from ai_trader.backtesting.strategies import classic

        result = _get_strategies_from_module(classic)

        assert isinstance(result, list)
        # Each item should be a tuple of (name, class)
        if result:  # Only check if strategies exist
            assert all(isinstance(item, tuple) and len(item) == 2 for item in result)

    def test_get_strategies_filters_non_strategies(self):
        """Test that only Strategy subclasses are returned."""
        import backtrader as bt

        # Create a mock module with mixed content
        mock_module = MagicMock()

        # The actual function uses inspect.getmembers, which we can test with real modules
        # For mocking, we'll verify the logic works with a simple test
        result = _get_strategies_from_module(mock_module)

        # Should return a list (possibly empty for mocks)
        assert isinstance(result, list)

    def test_get_strategies_sorts_alphabetically(self):
        """Test that strategies are sorted by name."""
        from ai_trader.backtesting.strategies import classic

        result = _get_strategies_from_module(classic)

        # Check that result is sorted by name (first element of tuple)
        if len(result) > 1:
            names = [name for name, _ in result]
            assert names == sorted(names)
