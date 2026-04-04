# validators.py
# Why pure functions? Side-effect-free validators are trivially unit-testable
# and can be audited without spinning up any infrastructure.
import re
from urllib.parse import urlparse

# Allowlist of schemes. We explicitly reject javascript://, data://, etc.
_ALLOWED_SCHEMES = {"http", "https"}
_MAX_URL_LENGTH = 2048  # browsers cap at ~2000; we enforce server-side too


def validate_url(raw: str) -> tuple[bool, str]:
    """
    Validates a URL for shortening.

    Returns (True, cleaned_url) on success, (False, error_message) on failure.

    Security rationale:
    - Scheme allowlist prevents javascript:// and data:// injection
    - Length cap prevents DoS via oversized payloads
    - netloc check prevents shortening of bare paths with no host
    """
    if not isinstance(raw, str):
        return False, "URL must be a string"

    url = raw.strip()

    if not url:
        return False, "URL must not be empty"

    if len(url) > _MAX_URL_LENGTH:
        return False, f"URL exceeds maximum length of {_MAX_URL_LENGTH} characters"

    try:
        parsed = urlparse(url)
    except Exception:
        return False, "URL could not be parsed"

    if parsed.scheme not in _ALLOWED_SCHEMES:
        return False, f"URL scheme '{parsed.scheme}' is not allowed. Use http or https"

    if not parsed.netloc:
        return False, "URL must include a host (e.g. https://example.com)"

    return True, url


def validate_short_code(code: str) -> tuple[bool, str]:
    """
    Validates a short code from the URL path.
    Allowlist: alphanumeric + hyphen, 4-12 chars.
    Rejects path traversal attempts, null bytes, etc.
    """
    if not isinstance(code, str):
        return False, "Code must be a string"

    if not re.fullmatch(r"[A-Za-z0-9\-_]{4,12}", code):
        return False, "Invalid short code format"

    return True, code