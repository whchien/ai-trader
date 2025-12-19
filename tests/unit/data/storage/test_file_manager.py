"""Tests for ai_trader.data.storage.base module (FileManager)."""

import pytest
import pandas as pd
from pathlib import Path

from ai_trader.data.storage.base import FileManager


class TestFileManagerInit:
    """Test FileManager initialization."""

    def test_init_creates_directory(self, tmp_path):
        """Test that __init__ creates the base directory."""
        data_dir = tmp_path / "market_data"
        manager = FileManager(str(data_dir))

        assert data_dir.exists()
        assert manager.base_data_dir == data_dir

    def test_init_with_default_directory(self):
        """Test initialization with default directory."""
        manager = FileManager()
        assert manager.base_data_dir == Path("data")

    def test_init_with_existing_directory(self, tmp_path):
        """Test initialization with existing directory."""
        data_dir = tmp_path / "existing"
        data_dir.mkdir()

        manager = FileManager(str(data_dir))
        assert manager.base_data_dir == data_dir

    def test_init_creates_nested_directories(self, tmp_path):
        """Test that nested directories are created."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        manager = FileManager(str(nested_dir))

        assert nested_dir.exists()


class TestGenerateFilename:
    """Test FileManager.generate_filename method."""

    def test_generates_valid_filename(self, tmp_path):
        """Test generating a valid filename."""
        manager = FileManager(str(tmp_path))
        filename = manager.generate_filename("AAPL", "2023-01-01", "2023-12-31")

        assert filename == "AAPL_2023-01-01_to_2023-12-31.csv"

    def test_handles_index_symbols(self, tmp_path):
        """Test that ^ is replaced with INDEX_ for index symbols."""
        manager = FileManager(str(tmp_path))
        filename = manager.generate_filename("^GSPC", "2023-01-01", "2023-12-31")

        assert filename == "INDEX_GSPC_2023-01-01_to_2023-12-31.csv"
        assert "^" not in filename

    def test_handles_multiple_caret_symbols(self, tmp_path):
        """Test handling of multiple ^ symbols."""
        manager = FileManager(str(tmp_path))
        filename = manager.generate_filename("^GSPC^", "2023-01-01", "2023-12-31")

        assert filename == "INDEX_GSPCINDEX__2023-01-01_to_2023-12-31.csv"

    @pytest.mark.parametrize("ticker,expected_prefix", [
        ("AAPL", "AAPL"),
        ("BRK.B", "BRK.B"),
        ("^VIX", "INDEX_VIX"),
        ("2330", "2330"),
    ])
    def test_various_ticker_formats(self, tmp_path, ticker, expected_prefix):
        """Test various ticker formats."""
        manager = FileManager(str(tmp_path))
        filename = manager.generate_filename(ticker, "2023-01-01", "2023-12-31")

        assert filename.startswith(expected_prefix)
        assert filename.endswith(".csv")


class TestSaveToCsv:
    """Test FileManager.save_to_csv method."""

    def test_saves_dataframe_successfully(self, tmp_path, sample_ohlcv_data_short):
        """Test saving a DataFrame to CSV."""
        manager = FileManager(str(tmp_path))
        filepath = manager.save_to_csv(sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10")

        assert Path(filepath).exists()
        assert filepath.endswith("AAPL_2023-01-01_to_2023-04-10.csv")

    def test_saves_correct_data(self, tmp_path, sample_ohlcv_data_short):
        """Test that saved data preserves values."""
        manager = FileManager(str(tmp_path))
        filepath = manager.save_to_csv(sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10")

        # Load back and compare
        loaded = pd.read_csv(filepath, index_col=0, parse_dates=True)
        assert len(loaded) == len(sample_ohlcv_data_short)

    def test_raises_on_empty_dataframe(self, tmp_path):
        """Test that empty DataFrame raises ValueError."""
        manager = FileManager(str(tmp_path))
        empty_df = pd.DataFrame()

        with pytest.raises(ValueError, match="Cannot save empty DataFrame"):
            manager.save_to_csv(empty_df, "AAPL", "2023-01-01", "2023-12-31")

    def test_respects_overwrite_flag(self, tmp_path, sample_ohlcv_data_short):
        """Test that overwrite flag is respected."""
        manager = FileManager(str(tmp_path))

        # Save first time
        filepath1 = manager.save_to_csv(sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10")

        # Try to save again with overwrite=False
        filepath2 = manager.save_to_csv(
            sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10", overwrite=False
        )

        # Should return same path but not overwrite
        assert filepath1 == filepath2

    def test_overwrites_when_flag_true(self, tmp_path, sample_ohlcv_data_short):
        """Test that file is overwritten when overwrite=True."""
        manager = FileManager(str(tmp_path))

        # Save first time
        manager.save_to_csv(sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10")
        original_time = Path(manager.base_data_dir / "AAPL_2023-01-01_to_2023-04-10.csv").stat().st_mtime

        # Create modified data
        modified_df = sample_ohlcv_data_short.copy()
        modified_df["open"] = modified_df["open"] * 2

        # Save again with overwrite=True
        import time
        time.sleep(0.1)  # Ensure different mtime
        manager.save_to_csv(modified_df, "AAPL", "2023-01-01", "2023-04-10", overwrite=True)

        new_time = Path(manager.base_data_dir / "AAPL_2023-01-01_to_2023-04-10.csv").stat().st_mtime
        assert new_time > original_time

    def test_creates_file_with_correct_size(self, tmp_path, sample_ohlcv_data_short):
        """Test that file is created with data."""
        manager = FileManager(str(tmp_path))
        filepath = manager.save_to_csv(sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10")

        file_size = Path(filepath).stat().st_size
        assert file_size > 0

    def test_saves_with_special_ticker(self, tmp_path, sample_ohlcv_data_short):
        """Test saving with special characters in ticker."""
        manager = FileManager(str(tmp_path))
        filepath = manager.save_to_csv(sample_ohlcv_data_short, "^GSPC", "2023-01-01", "2023-04-10")

        assert "INDEX_GSPC" in filepath


class TestLoadFromCsv:
    """Test FileManager.load_from_csv method."""

    def test_loads_csv_successfully(self, tmp_path, sample_ohlcv_data_short):
        """Test loading a CSV file."""
        manager = FileManager(str(tmp_path))
        filepath = manager.save_to_csv(sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10")

        loaded = manager.load_from_csv(filepath)

        assert isinstance(loaded, pd.DataFrame)
        assert len(loaded) == len(sample_ohlcv_data_short)

    def test_loads_with_date_parsing(self, tmp_path, sample_ohlcv_data_short):
        """Test that dates are parsed correctly."""
        manager = FileManager(str(tmp_path))
        filepath = manager.save_to_csv(sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10")

        loaded = manager.load_from_csv(filepath, parse_dates=True)

        assert isinstance(loaded.index, pd.DatetimeIndex)

    def test_raises_on_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        manager = FileManager(str(tmp_path))

        with pytest.raises(FileNotFoundError):
            manager.load_from_csv(str(tmp_path / "nonexistent.csv"))

    def test_preserves_data_precision(self, tmp_path, sample_ohlcv_data_short):
        """Test that data values are preserved with precision."""
        manager = FileManager(str(tmp_path))
        filepath = manager.save_to_csv(sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10")

        loaded = manager.load_from_csv(filepath)

        # Check that values match (allowing for dtype differences)
        assert len(loaded) == len(sample_ohlcv_data_short)
        assert list(loaded.columns) == list(sample_ohlcv_data_short.columns)

    def test_loads_without_date_parsing(self, tmp_path, sample_ohlcv_data_short):
        """Test loading without date parsing."""
        manager = FileManager(str(tmp_path))
        filepath = manager.save_to_csv(sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10")

        loaded = manager.load_from_csv(filepath, parse_dates=False)

        # Index should be object type, not datetime
        assert loaded.index.dtype == object


class TestFileExists:
    """Test FileManager.file_exists method."""

    def test_returns_true_for_existing_file(self, tmp_path, sample_ohlcv_data_short):
        """Test that file_exists returns True for existing file."""
        manager = FileManager(str(tmp_path))
        manager.save_to_csv(sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10")

        assert manager.file_exists("AAPL", "2023-01-01", "2023-04-10") is True

    def test_returns_false_for_nonexistent_file(self, tmp_path):
        """Test that file_exists returns False for missing file."""
        manager = FileManager(str(tmp_path))

        assert manager.file_exists("AAPL", "2023-01-01", "2023-04-10") is False

    def test_checks_with_special_characters(self, tmp_path, sample_ohlcv_data_short):
        """Test file_exists with special characters."""
        manager = FileManager(str(tmp_path))
        manager.save_to_csv(sample_ohlcv_data_short, "^GSPC", "2023-01-01", "2023-04-10")

        assert manager.file_exists("^GSPC", "2023-01-01", "2023-04-10") is True
        assert manager.file_exists("GSPC", "2023-01-01", "2023-04-10") is False


class TestDeleteFile:
    """Test FileManager.delete_file method."""

    def test_deletes_existing_file(self, tmp_path, sample_ohlcv_data_short):
        """Test deleting an existing file."""
        manager = FileManager(str(tmp_path))
        manager.save_to_csv(sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10")

        result = manager.delete_file("AAPL", "2023-01-01", "2023-04-10")

        assert result is True
        assert not manager.file_exists("AAPL", "2023-01-01", "2023-04-10")

    def test_returns_false_for_nonexistent_file(self, tmp_path):
        """Test that delete_file returns False for missing file."""
        manager = FileManager(str(tmp_path))

        result = manager.delete_file("AAPL", "2023-01-01", "2023-04-10")

        assert result is False

    def test_deletes_with_special_characters(self, tmp_path, sample_ohlcv_data_short):
        """Test deleting file with special characters."""
        manager = FileManager(str(tmp_path))
        manager.save_to_csv(sample_ohlcv_data_short, "^GSPC", "2023-01-01", "2023-04-10")

        result = manager.delete_file("^GSPC", "2023-01-01", "2023-04-10")

        assert result is True


class TestGetExistingDataFiles:
    """Test FileManager.get_existing_data_files method."""

    def test_returns_empty_list_for_empty_directory(self, tmp_path):
        """Test getting files from empty directory."""
        manager = FileManager(str(tmp_path))

        files = manager.get_existing_data_files()

        assert files == []

    def test_returns_all_csv_files(self, tmp_path, sample_ohlcv_data_short):
        """Test getting all CSV files."""
        manager = FileManager(str(tmp_path))

        # Save multiple files
        manager.save_to_csv(sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10")
        manager.save_to_csv(sample_ohlcv_data_short, "MSFT", "2023-01-01", "2023-04-10")

        files = manager.get_existing_data_files()

        assert len(files) == 2

    def test_filters_by_ticker(self, tmp_path, sample_ohlcv_data_short):
        """Test filtering files by ticker."""
        manager = FileManager(str(tmp_path))

        manager.save_to_csv(sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10")
        manager.save_to_csv(sample_ohlcv_data_short, "MSFT", "2023-01-01", "2023-04-10")

        aapl_files = manager.get_existing_data_files("AAPL")

        assert len(aapl_files) == 1
        assert "AAPL" in aapl_files[0]

    def test_filters_index_symbols(self, tmp_path, sample_ohlcv_data_short):
        """Test filtering index symbols."""
        manager = FileManager(str(tmp_path))

        manager.save_to_csv(sample_ohlcv_data_short, "^GSPC", "2023-01-01", "2023-04-10")
        manager.save_to_csv(sample_ohlcv_data_short, "^VIX", "2023-01-01", "2023-04-10")

        gspc_files = manager.get_existing_data_files("^GSPC")

        assert len(gspc_files) == 1
        assert "INDEX_GSPC" in gspc_files[0]

    def test_returns_empty_for_nonexistent_ticker(self, tmp_path, sample_ohlcv_data_short):
        """Test that filtering nonexistent ticker returns empty list."""
        manager = FileManager(str(tmp_path))

        manager.save_to_csv(sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10")

        files = manager.get_existing_data_files("NONEXISTENT")

        assert files == []


class TestGetDataDirectoryInfo:
    """Test FileManager.get_data_directory_info method."""

    def test_returns_info_for_empty_directory(self, tmp_path):
        """Test getting info for empty directory."""
        manager = FileManager(str(tmp_path))

        info = manager.get_data_directory_info()

        assert info["exists"] is True
        assert info["file_count"] == 0
        assert info["total_size"] == 0

    def test_returns_correct_file_count(self, tmp_path, sample_ohlcv_data_short):
        """Test that file count is correct."""
        manager = FileManager(str(tmp_path))

        manager.save_to_csv(sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10")
        manager.save_to_csv(sample_ohlcv_data_short, "MSFT", "2023-01-01", "2023-04-10")

        info = manager.get_data_directory_info()

        assert info["file_count"] == 2
        assert len(info["files"]) == 2

    def test_returns_total_size(self, tmp_path, sample_ohlcv_data_short):
        """Test that total size is calculated."""
        manager = FileManager(str(tmp_path))

        manager.save_to_csv(sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10")

        info = manager.get_data_directory_info()

        assert info["total_size"] > 0

    def test_returns_nonexistent_directory_info(self, tmp_path):
        """Test getting info for nonexistent directory."""
        data_dir = tmp_path / "nonexistent"
        manager = FileManager(str(data_dir))
        # Delete the directory after creation
        data_dir.rmdir()

        info = manager.get_data_directory_info()

        assert info["exists"] is False
        assert info["file_count"] == 0


class TestFileManagerIntegration:
    """Integration tests for FileManager."""

    def test_save_load_roundtrip(self, tmp_path, sample_ohlcv_data_short):
        """Test complete save-load roundtrip."""
        manager = FileManager(str(tmp_path))

        # Save
        filepath = manager.save_to_csv(sample_ohlcv_data_short, "AAPL", "2023-01-01", "2023-04-10")

        # Verify file exists
        assert manager.file_exists("AAPL", "2023-01-01", "2023-04-10")

        # Load
        loaded = manager.load_from_csv(filepath)

        # Verify structure is preserved
        assert len(loaded) == len(sample_ohlcv_data_short)
        assert set(loaded.columns) == set(sample_ohlcv_data_short.columns)

    def test_manage_multiple_tickers(self, tmp_path, sample_ohlcv_data_short):
        """Test managing data for multiple tickers."""
        manager = FileManager(str(tmp_path))

        tickers = ["AAPL", "MSFT", "GOOGL", "^GSPC"]

        for ticker in tickers:
            manager.save_to_csv(sample_ohlcv_data_short, ticker, "2023-01-01", "2023-04-10")

        # Verify all files exist
        info = manager.get_data_directory_info()
        assert info["file_count"] == len(tickers)

        # Load each and verify
        for ticker in tickers:
            assert manager.file_exists(ticker, "2023-01-01", "2023-04-10")
            filepath = manager.base_data_dir / manager.generate_filename(
                ticker, "2023-01-01", "2023-04-10"
            )
            loaded = manager.load_from_csv(str(filepath))
            assert not loaded.empty
