import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_dir():
    """
    Provide a temporary directory for test file operations.
    Automatically cleaned up after test completion.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_folder_with_files(temp_dir):
    """
    Provide a temporary directory with test files and subdirectories.
    """
    # Create test files
    (temp_dir / "test_file1.txt").write_text("test content 1")
    (temp_dir / "test_file2.txt").write_text("test content 2")

    # Create subdirectory with files
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested_file.txt").write_text("nested content")

    # Create a symlink
    link_path = temp_dir / "test_link.txt"
    link_path.symlink_to(temp_dir / "test_file1.txt")

    yield temp_dir
