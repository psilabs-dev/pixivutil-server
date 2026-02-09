import pytest

from PixivServer.utils import get_version, clear_folder, is_valid_date


def test_get_version():
    """Test that get_version returns a valid version string."""
    version = get_version()
    assert isinstance(version, str)
    assert len(version) > 0
    # Version should be in semantic versioning format (x.y.z)
    parts = version.split(".")
    assert len(parts) >= 2, f"Version {version} should have at least major.minor format"


class TestClearFolder:
    """Tests for the clear_folder function."""

    def test_clear_folder_with_files(self, temp_folder_with_files):
        """Test clearing a folder with files and subdirectories."""
        folder_path = str(temp_folder_with_files)

        # Verify folder has content before clearing
        assert len(list(temp_folder_with_files.iterdir())) > 0

        # Clear the folder
        result = clear_folder(folder_path)

        # Verify result is True
        assert result is True

        # Verify folder is empty
        assert len(list(temp_folder_with_files.iterdir())) == 0

        # Verify folder still exists
        assert temp_folder_with_files.exists()

    def test_clear_empty_folder(self, temp_dir):
        """Test clearing an already empty folder."""
        folder_path = str(temp_dir)

        # Verify folder is empty
        assert len(list(temp_dir.iterdir())) == 0

        # Clear the folder
        result = clear_folder(folder_path)

        # Verify result is True
        assert result is True

        # Verify folder is still empty
        assert len(list(temp_dir.iterdir())) == 0


class TestIsValidDate:
    """Tests for the is_valid_date function."""

    @pytest.mark.parametrize("valid_date", [
        "2024-01-01",
        "2024-12-31",
        "2023-06-15",
        "2025-02-28",
        "2024-02-29",  # Leap year
        "1999-01-01",
        "2100-12-31",
    ])
    def test_valid_dates(self, valid_date):
        """Test that valid date strings return True."""
        assert is_valid_date(valid_date) is True

    @pytest.mark.parametrize("invalid_date", [
        "2024-13-01",     # Invalid month
        "2024-01-32",     # Invalid day
        "2023-02-29",     # Not a leap year
        "2024-00-01",     # Invalid month (0)
        "2024-01-00",     # Invalid day (0)
        "24-01-01",       # Wrong year format
        "2024/01/01",     # Wrong separator
        "01-01-2024",     # Wrong order
        "2024-01",        # Missing day
        "2024",           # Only year
        "not-a-date",     # Invalid string
        "",               # Empty string
        "2024-01-01T00:00:00",  # Datetime format
    ])
    def test_invalid_dates(self, invalid_date):
        """Test that invalid date strings return False."""
        assert is_valid_date(invalid_date) is False
