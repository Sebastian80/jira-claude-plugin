"""
Tests for error handling utilities in response.py.
"""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Setup paths
PLUGIN_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

from requests import HTTPError
from requests.models import Response

from jira.response import get_status_code, is_status


def _make_http_error(status_code: int) -> HTTPError:
    """Create an HTTPError with a real Response object."""
    response = Response()
    response.status_code = status_code
    response._content = b"error"
    return HTTPError(response=response)


class TestGetStatusCode:
    """Tests for get_status_code()."""

    def test_returns_status_from_http_error(self):
        """Should extract status code from HTTPError."""
        err = _make_http_error(404)
        assert get_status_code(err) == 404

    def test_returns_various_status_codes(self):
        """Should work for different HTTP status codes."""
        for code in (400, 403, 404, 409, 500, 502):
            err = _make_http_error(code)
            assert get_status_code(err) == code

    def test_returns_none_for_plain_exception(self):
        """Should return None for non-HTTPError exceptions."""
        assert get_status_code(Exception("something broke")) is None

    def test_returns_none_for_value_error(self):
        """Should return None for other exception types."""
        assert get_status_code(ValueError("bad value")) is None

    def test_returns_none_for_http_error_without_response(self):
        """Should return None when HTTPError has no response attached."""
        err = HTTPError("no response")
        assert get_status_code(err) is None


class TestIsStatus:
    """Tests for is_status()."""

    def test_matches_correct_status(self):
        """Should return True when status codes match."""
        err = _make_http_error(404)
        assert is_status(err, 404) is True

    def test_rejects_wrong_status(self):
        """Should return False when status codes differ."""
        err = _make_http_error(500)
        assert is_status(err, 404) is False

    def test_returns_false_for_plain_exception(self):
        """Should return False for non-HTTPError exceptions."""
        assert is_status(Exception("fail"), 404) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
