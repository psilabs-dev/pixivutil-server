import asyncio

import pytest
from fastapi import HTTPException

from PixivServer.auth import extract_api_key, is_valid_api_key_header
from PixivServer.config.server import config


def test_extract_api_key():
    assert extract_api_key("Bearer abc123") == "abc123"
    assert extract_api_key("Bearer    abc123") == "abc123"
    assert extract_api_key("abc123") == ""
    assert extract_api_key(None) == ""


def test_auth_disabled_when_env_key_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(config, "api_key", None)
    assert asyncio.run(is_valid_api_key_header(None)) is True


def test_valid_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(config, "api_key", "expected-key")
    assert asyncio.run(is_valid_api_key_header("Bearer expected-key")) is True


def test_invalid_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(config, "api_key", "expected-key")
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(is_valid_api_key_header("Bearer wrong-key"))
    assert exc_info.value.status_code == 401
