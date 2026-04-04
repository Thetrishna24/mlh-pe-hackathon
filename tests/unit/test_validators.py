# Pure unit tests — no DB, no Flask, no fixtures needed.
import pytest
from app.validators import validate_url, validate_short_code


class TestValidateUrl:
    def test_valid_https_url(self):
        ok, result = validate_url("https://example.com")
        assert ok is True
        assert result == "https://example.com"

    def test_valid_http_url(self):
        ok, _ = validate_url("http://example.com/path?q=1")
        assert ok is True

    def test_strips_whitespace(self):
        ok, result = validate_url("  https://example.com  ")
        assert ok is True
        assert result == "https://example.com"

    # --- Negative / security cases ---

    def test_rejects_javascript_scheme(self):
        ok, msg = validate_url("javascript://alert(1)")
        assert ok is False
        assert "not allowed" in msg

    def test_rejects_data_uri(self):
        ok, msg = validate_url("data:text/html,<h1>hi</h1>")
        assert ok is False

    def test_rejects_empty_string(self):
        ok, msg = validate_url("")
        assert ok is False
        assert "empty" in msg

    def test_rejects_non_string(self):
        ok, msg = validate_url(None)
        assert ok is False

    def test_rejects_oversized_url(self):
        ok, msg = validate_url("https://x.com/" + "a" * 2048)
        assert ok is False
        assert "maximum length" in msg

    def test_rejects_url_without_host(self):
        ok, msg = validate_url("https:///no-host")
        assert ok is False

    def test_rejects_ftp_scheme(self):
        ok, msg = validate_url("ftp://example.com")
        assert ok is False


class TestValidateShortCode:
    def test_valid_alphanumeric(self):
        ok, _ = validate_short_code("abc123")
        assert ok is True

    def test_valid_with_hyphen(self):
        ok, _ = validate_short_code("abc-123")
        assert ok is True
    def test_valid_with_underscore(self):
        ok, _ = validate_short_code("abc_123")
        assert ok is True
    def test_rejects_too_short(self):
        ok, msg = validate_short_code("ab")
        assert ok is False

    def test_rejects_path_traversal(self):
        ok, msg = validate_short_code("../../etc")
        assert ok is False

    def test_rejects_null_byte(self):
        ok, msg = validate_short_code("abc\x00def")
        assert ok is False

    def test_rejects_special_chars(self):
        ok, msg = validate_short_code("abc<script>")
        assert ok is False