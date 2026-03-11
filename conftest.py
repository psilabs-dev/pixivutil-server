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
