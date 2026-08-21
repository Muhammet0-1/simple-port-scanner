from __future__ import annotations

import pytest

from simple_port_scanner.config import ScanConfig, parse_ports, validate_target
from simple_port_scanner.errors import ConfigurationError


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("22", (22,)),
        ("22,80,443", (22, 80, 443)),
        ("80,78-80", (78, 79, 80)),
        ("1-3,65535", (1, 2, 3, 65_535)),
    ],
)
def test_parse_ports_normalizes_ranges(value: str, expected: tuple[int, ...]) -> None:
    assert parse_ports(value) == expected


@pytest.mark.parametrize(
    "value",
    ["", " 22", "22 ", "0", "65536", "a", "22,,80", "80-22", "1-2-3", "1, 2"],
)
def test_parse_ports_rejects_invalid_specs(value: str) -> None:
    with pytest.raises(ConfigurationError):
        parse_ports(value)


@pytest.mark.parametrize("value", ["localhost", "example.com", "example.com.", "127.0.0.1", "::1"])
def test_validate_target_accepts_hostnames_and_ip_literals(value: str) -> None:
    assert validate_target(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        " example.com",
        "example.com/path",
        "https://example.com",
        "10.0.0.0/24",
        "bad host",
        "not:ipv6",
    ],
)
def test_validate_target_rejects_urls_networks_and_whitespace(value: str) -> None:
    with pytest.raises(ConfigurationError):
        validate_target(value)


def test_config_sorts_and_deduplicates_ports() -> None:
    config = ScanConfig(target="localhost", ports=(443, 22, 443))
    assert config.ports == (22, 443)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"concurrency": 0},
        {"concurrency": 257},
        {"connect_timeout": 0.01},
        {"connect_timeout": 11.0},
        {"connect_timeout": float("nan")},
        {"connect_timeout": float("inf")},
        {"banner_timeout": 0.01},
        {"banner_timeout": 3.0},
        {"banner_timeout": float("nan")},
        {"banner_bytes": 0},
        {"banner_bytes": 4_097},
        {"max_resolved_addresses": 0},
        {"max_resolved_addresses": 9},
    ],
)
def test_config_rejects_unsafe_bounds(kwargs: dict[str, int | float]) -> None:
    with pytest.raises(ConfigurationError):
        ScanConfig(target="localhost", ports=(80,), **kwargs)


def test_large_scan_requires_explicit_opt_in() -> None:
    ports = tuple(range(1, 1_026))
    with pytest.raises(ConfigurationError, match="allow-large-scan"):
        ScanConfig(target="localhost", ports=ports)
    assert ScanConfig(target="localhost", ports=ports, allow_large_scan=True).ports == ports


def test_programmatic_boolean_port_is_rejected() -> None:
    with pytest.raises(ConfigurationError):
        ScanConfig(target="localhost", ports=(True,))
