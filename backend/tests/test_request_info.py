from unittest.mock import MagicMock

import pytest

from timegrip.adapters.controllers.request_info import client_ip


def _make_request(headers, client_host):
    request = MagicMock()
    request.headers = headers
    request.client = (
        MagicMock(host=client_host) if client_host is not None else None
    )
    return request


@pytest.mark.parametrize(
    ("forwarded_for", "expected"),
    [
        ("203.0.113.7, 10.0.0.1", "203.0.113.7"),
        (" 203.0.113.7 ,10.0.0.1", "203.0.113.7"),
    ],
)
def test_client_ip_prefers_first_forwarded_address(forwarded_for, expected):
    request = _make_request(
        headers={"x-forwarded-for": forwarded_for},
        client_host="10.0.0.1",
    )
    assert client_ip(request) == expected


def test_client_ip_falls_back_to_connection_address():
    request = _make_request(headers={}, client_host="192.168.1.1")
    assert client_ip(request) == "192.168.1.1"


def test_client_ip_ignores_empty_forwarded_header():
    request = _make_request(
        headers={"x-forwarded-for": ""},
        client_host="192.168.1.1",
    )
    assert client_ip(request) == "192.168.1.1"


def test_client_ip_unknown_without_client():
    request = _make_request(headers={}, client_host=None)
    assert client_ip(request) is None
