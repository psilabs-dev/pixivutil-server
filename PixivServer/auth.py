import hmac
import re

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from PixivServer.config.server import config

authorization_header = APIKeyHeader(name="Authorization", auto_error=False)


def extract_api_key(header_value: str | None) -> str:
    """
    Extract API key from Authorization header.

    Expected format: Bearer <api-key>
    """
    if not header_value:
        return ""
    pattern = re.compile(r"Bearer\s+(.+)")
    result = pattern.findall(header_value)
    return result[0] if result else ""


async def is_valid_api_key_header(
    header_value: str | None = Security(authorization_header),
) -> bool:
    """
    Validate API key from Authorization header.

    Auth is disabled when PIXIVUTIL_SERVER_API_KEY is not configured.
    """
    if not config.api_key:
        return True

    api_key = extract_api_key(header_value)
    if hmac.compare_digest(api_key, config.api_key):
        return True
    raise HTTPException(status_code=401, detail="Invalid API key.")
