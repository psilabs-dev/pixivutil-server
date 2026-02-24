import tempfile
from pathlib import Path

import pytest


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--pixiv-api",
        action="store_true",
        default=False,
        help="Run tests that make Pixiv API calls.",
    )


def pytest_configure(config: pytest.Config):
    config.addinivalue_line(
        "markers",
        "pixiv_api: test performs Pixiv API calls and is skipped unless --pixiv-api is provided.",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]):
    if config.getoption("--pixiv-api"):
        return
    skip_pixiv_api = pytest.mark.skip(reason="need --pixiv-api option enabled")
    for item in items:
        if "pixiv_api" in item.keywords:
            item.add_marker(skip_pixiv_api)


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
