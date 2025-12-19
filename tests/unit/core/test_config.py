"""Tests for ai_trader.core.config module."""

import pytest
import yaml
from pathlib import Path
from pydantic import ValidationError
from ai_trader.core.config import Config, DataConfig, BrokerConfig, BacktestConfig


class TestDataConfig:
    """Test the DataConfig model."""

    def test_default_values(self):
        """Test default configuration values."""
        config = DataConfig()
        assert config.market == "tw"
        assert config.start_year == 2019
        assert config.start_month == 1
        assert config.data_dir == Path("./data/tw_stock/")

    def test_create_with_us_market(self):
        """Test creating DataConfig with US market."""
        config = DataConfig(market="us")
        assert config.market == "us"

    def test_data_dir_string_to_path_conversion(self):
        """Test that string data_dir is converted to Path."""
        config = DataConfig(data_dir="./data/us_stock/")
        assert isinstance(config.data_dir, Path)
        assert config.data_dir == Path("./data/us_stock/")

    def test_data_dir_path_remains_path(self):
        """Test that Path data_dir remains Path."""
        path = Path("./data/custom/")
        config = DataConfig(data_dir=path)
        assert config.data_dir == path

    @pytest.mark.parametrize("start_year", [2000, 2010, 2020, 2024])
    def test_valid_start_year_values(self, start_year):
        """Test valid start_year values."""
        config = DataConfig(start_year=start_year)
        assert config.start_year == start_year

    def test_start_year_too_small(self):
        """Test that start_year < 2000 is rejected."""
        with pytest.raises(ValidationError):
            DataConfig(start_year=1999)

    @pytest.mark.parametrize("start_month", [1, 6, 12])
    def test_valid_start_month_values(self, start_month):
        """Test valid start_month values."""
        config = DataConfig(start_month=start_month)
        assert config.start_month == start_month

    def test_start_month_zero_invalid(self):
        """Test that start_month=0 is rejected."""
        with pytest.raises(ValidationError):
            DataConfig(start_month=0)

    def test_start_month_greater_than_12_invalid(self):
        """Test that start_month > 12 is rejected."""
        with pytest.raises(ValidationError):
            DataConfig(start_month=13)


class TestBrokerConfig:
    """Test the BrokerConfig model."""

    def test_default_values(self):
        """Test default broker configuration."""
        config = BrokerConfig()
        assert config.cash == 1000000
        assert config.commission == 0.001425
        assert config.stake == 0.95

    def test_custom_cash(self):
        """Test setting custom cash value."""
        config = BrokerConfig(cash=500000)
        assert config.cash == 500000

    def test_cash_zero_invalid(self):
        """Test that cash <= 0 is rejected."""
        with pytest.raises(ValidationError):
            BrokerConfig(cash=0)

        with pytest.raises(ValidationError):
            BrokerConfig(cash=-1000)

    def test_cash_positive_valid(self):
        """Test that positive cash values are valid."""
        for cash in [1, 100, 1000, 1000000, 10000000]:
            config = BrokerConfig(cash=cash)
            assert config.cash == cash

    def test_commission_at_boundaries(self):
        """Test commission values at boundaries."""
        config_zero = BrokerConfig(commission=0.0)
        assert config_zero.commission == 0.0

        config_almost_one = BrokerConfig(commission=0.999999)
        assert config_almost_one.commission == 0.999999

    def test_commission_at_one_invalid(self):
        """Test that commission >= 1 is rejected."""
        with pytest.raises(ValidationError):
            BrokerConfig(commission=1.0)

        with pytest.raises(ValidationError):
            BrokerConfig(commission=1.5)

    def test_commission_negative_invalid(self):
        """Test that negative commission is rejected."""
        with pytest.raises(ValidationError):
            BrokerConfig(commission=-0.001)

    @pytest.mark.parametrize("commission", [0.0, 0.001, 0.001425, 0.01, 0.1])
    def test_valid_commission_values(self, commission):
        """Test various valid commission values."""
        config = BrokerConfig(commission=commission)
        assert config.commission == commission

    def test_stake_boundaries(self):
        """Test stake boundaries."""
        config_min = BrokerConfig(stake=0.01)
        assert config_min.stake == 0.01

        config_max = BrokerConfig(stake=1.0)
        assert config_max.stake == 1.0

    def test_stake_zero_invalid(self):
        """Test that stake <= 0 is rejected."""
        with pytest.raises(ValidationError):
            BrokerConfig(stake=0.0)

        with pytest.raises(ValidationError):
            BrokerConfig(stake=-0.5)

    def test_stake_greater_than_one_invalid(self):
        """Test that stake > 1 is rejected."""
        with pytest.raises(ValidationError):
            BrokerConfig(stake=1.1)

        with pytest.raises(ValidationError):
            BrokerConfig(stake=2.0)

    @pytest.mark.parametrize("stake", [0.1, 0.5, 0.9, 0.95, 1.0])
    def test_valid_stake_values(self, stake):
        """Test various valid stake values."""
        config = BrokerConfig(stake=stake)
        assert config.stake == stake


class TestBacktestConfig:
    """Test the BacktestConfig model."""

    def test_default_values(self):
        """Test default backtest configuration."""
        config = BacktestConfig()
        assert config.start_date is None
        assert config.end_date is None

    def test_start_and_end_dates(self):
        """Test setting start and end dates."""
        config = BacktestConfig(
            start_date="2020-01-01",
            end_date="2023-12-31"
        )
        assert config.start_date == "2020-01-01"
        assert config.end_date == "2023-12-31"

    def test_only_start_date(self):
        """Test setting only start date."""
        config = BacktestConfig(start_date="2020-01-01")
        assert config.start_date == "2020-01-01"
        assert config.end_date is None

    def test_only_end_date(self):
        """Test setting only end date."""
        config = BacktestConfig(end_date="2023-12-31")
        assert config.start_date is None
        assert config.end_date == "2023-12-31"


class TestConfig:
    """Test the main Config model."""

    def test_default_values(self):
        """Test Config with default values."""
        config = Config()
        assert config.data.market == "tw"
        assert config.broker.cash == 1000000
        assert config.broker.commission == 0.001425
        assert config.backtest.start_date is None

    def test_create_with_custom_values(self):
        """Test creating Config with custom values."""
        config = Config(
            data=DataConfig(market="us", start_year=2020),
            broker=BrokerConfig(cash=500000),
            backtest=BacktestConfig(start_date="2020-01-01")
        )
        assert config.data.market == "us"
        assert config.broker.cash == 500000
        assert config.backtest.start_date == "2020-01-01"

    def test_create_with_dict(self):
        """Test creating Config from dictionary."""
        config = Config(**{
            "data": {"market": "us", "start_year": 2020},
            "broker": {"cash": 100000},
            "backtest": {"start_date": "2021-01-01"}
        })
        assert config.data.market == "us"
        assert config.broker.cash == 100000
        assert config.backtest.start_date == "2021-01-01"


class TestConfigFromYaml:
    """Test Config.from_yaml method."""

    def test_from_yaml_with_valid_file(self, tmp_path, sample_config_dict):
        """Test loading config from valid YAML file."""
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config_dict, f)

        config = Config.from_yaml(config_file)
        assert config.data.market == sample_config_dict["data"]["market"]
        assert config.broker.cash == sample_config_dict["broker"]["cash"]

    def test_from_yaml_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        missing_file = tmp_path / "nonexistent.yaml"
        with pytest.raises(FileNotFoundError):
            Config.from_yaml(missing_file)

    def test_from_yaml_with_path_object(self, tmp_path, sample_config_dict):
        """Test from_yaml works with Path object."""
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config_dict, f)

        config = Config.from_yaml(config_file)
        assert config.data.market == "tw"

    def test_from_yaml_with_string_path(self, tmp_path, sample_config_dict):
        """Test from_yaml works with string path."""
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config_dict, f)

        config = Config.from_yaml(str(config_file))
        assert config.data.market == "tw"

    def test_from_yaml_us_config(self, tmp_path, sample_config_dict_us):
        """Test loading US market configuration from YAML."""
        config_file = tmp_path / "us_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config_dict_us, f)

        config = Config.from_yaml(config_file)
        assert config.data.market == "us"
        assert config.broker.cash == 100000

    def test_from_yaml_with_invalid_yaml(self, tmp_path):
        """Test that invalid YAML raises error."""
        invalid_file = tmp_path / "invalid.yaml"
        with open(invalid_file, "w") as f:
            f.write("{ invalid yaml content [")

        with pytest.raises(Exception):  # yaml parsing error
            Config.from_yaml(invalid_file)

    def test_from_yaml_with_missing_required_fields(self, tmp_path):
        """Test that missing required fields raise ValidationError."""
        incomplete_config = {"data": {}}  # Missing broker and backtest
        config_file = tmp_path / "incomplete.yaml"
        with open(config_file, "w") as f:
            yaml.dump(incomplete_config, f)

        # Should work with defaults for missing fields
        config = Config.from_yaml(config_file)
        assert config.broker.cash == 1000000  # default value


class TestConfigToYaml:
    """Test Config.to_yaml method."""

    def test_to_yaml_creates_file(self, tmp_path):
        """Test that to_yaml creates a YAML file."""
        config = Config()
        config_file = tmp_path / "config.yaml"

        config.to_yaml(config_file)

        assert config_file.exists()

    def test_to_yaml_creates_parent_directories(self, tmp_path):
        """Test that to_yaml creates parent directories."""
        config = Config()
        config_file = tmp_path / "subdir" / "nested" / "config.yaml"

        config.to_yaml(config_file)

        assert config_file.exists()
        assert config_file.parent.exists()

    def test_to_yaml_creates_readable_file(self, tmp_path):
        """Test that to_yaml creates a file that exists."""
        config = Config(
            data=DataConfig(market="us"),
            broker=BrokerConfig(cash=500000)
        )
        config_file = tmp_path / "config.yaml"

        config.to_yaml(config_file)

        # File should exist and have content
        assert config_file.exists()
        assert config_file.stat().st_size > 0

    def test_to_yaml_with_path_object(self, tmp_path):
        """Test to_yaml with Path object."""
        config = Config()
        config_file = tmp_path / "config.yaml"
        config.to_yaml(config_file)
        assert config_file.exists()

    def test_to_yaml_with_string_path(self, tmp_path):
        """Test to_yaml with string path."""
        config = Config()
        config_file = str(tmp_path / "config.yaml")
        config.to_yaml(config_file)
        assert Path(config_file).exists()


class TestConfigIntegration:
    """Integration tests for Config class."""

    def test_default_config_is_valid(self):
        """Test that default config is valid."""
        config = Config()
        assert config is not None
        assert all([
            hasattr(config, attr)
            for attr in ["data", "broker", "backtest"]
        ])

    def test_taiwan_market_config(self):
        """Test Taiwan market configuration."""
        config = Config(data=DataConfig(market="tw"))
        assert config.data.market == "tw"
        assert config.data.data_dir == Path("./data/tw_stock/")

    def test_us_market_config(self):
        """Test US market configuration."""
        config = Config(data=DataConfig(market="us"))
        assert config.data.market == "us"

    def test_full_config_workflow(self, sample_config_dict, tmp_path):
        """Test complete workflow: create -> load from YAML."""
        # Save sample config to file
        config_file = tmp_path / "workflow.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config_dict, f)

        # Load
        loaded = Config.from_yaml(config_file)

        # Verify
        assert loaded.data.market == sample_config_dict["data"]["market"]
        assert loaded.broker.cash == sample_config_dict["broker"]["cash"]
        assert loaded.backtest.start_date == sample_config_dict["backtest"]["start_date"]
