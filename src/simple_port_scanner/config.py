"""Validated configuration and CLI value parsing."""

from __future__ import annotations

import ipaddress
import math
import re
from dataclasses import dataclass

from .errors import ConfigurationError

MIN_PORT = 1
MAX_PORT = 65_535
DEFAULT_PORT_LIMIT = 1_024
ABSOLUTE_PORT_LIMIT = MAX_PORT
MAX_CONCURRENCY = 256
MAX_RESOLVED_ADDRESSES = 8

_HOST_LABEL = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


def validate_target(value: str) -> str:
    """Accept a single IP literal or DNS hostname, never a URL or network range."""

    target = value.strip()
    if not target:
        raise ConfigurationError("target must not be empty")
    if target != value or any(character.isspace() for character in target):
        raise ConfigurationError("target must not contain surrounding or embedded whitespace")
    if "://" in target or any(character in target for character in "/?#@"):
        raise ConfigurationError("target must be a hostname or IP address, not a URL or CIDR")
    if len(target) > 253:
        raise ConfigurationError("target is too long")

    if ":" in target:
        try:
            parsed = ipaddress.ip_address(target)
        except ValueError as exc:
            raise ConfigurationError("target is not a valid IPv6 address") from exc
        if parsed.version != 6:
            raise ConfigurationError("target is not a valid IPv6 address")
    else:
        hostname = target[:-1] if target.endswith(".") else target
        if not hostname or any(not _HOST_LABEL.fullmatch(label) for label in hostname.split(".")):
            raise ConfigurationError("target is not a valid hostname or IP address")
    return target


def parse_ports(value: str) -> tuple[int, ...]:
    """Parse comma-separated ports and inclusive ranges into sorted unique ports."""

    if not value or value.strip() != value:
        raise ConfigurationError("ports must not be empty or surrounded by whitespace")

    ports: set[int] = set()
    for item in value.split(","):
        if not item or item.strip() != item:
            raise ConfigurationError("ports must use comma-separated numbers or ranges")
        if "-" in item:
            if item.count("-") != 1:
                raise ConfigurationError(f"invalid port range: {item}")
            start_text, end_text = item.split("-", 1)
            start = _parse_port(start_text)
            end = _parse_port(end_text)
            if start > end:
                raise ConfigurationError(f"port range starts after it ends: {item}")
            ports.update(range(start, end + 1))
        else:
            ports.add(_parse_port(item))
    return tuple(sorted(ports))


def _parse_port(value: str) -> int:
    if not value.isascii() or not value.isdecimal():
        raise ConfigurationError(f"invalid port: {value or '<empty>'}")
    port = int(value)
    if not MIN_PORT <= port <= MAX_PORT:
        raise ConfigurationError(f"port must be between {MIN_PORT} and {MAX_PORT}: {port}")
    return port


@dataclass(frozen=True, slots=True)
class ScanConfig:
    """Fail-fast configuration for a bounded TCP connect scan."""

    target: str
    ports: tuple[int, ...]
    concurrency: int = 32
    connect_timeout: float = 0.75
    banner: bool = False
    banner_timeout: float = 0.5
    banner_bytes: int = 256
    allow_public_target: bool = False
    allow_large_scan: bool = False
    max_resolved_addresses: int = MAX_RESOLVED_ADDRESSES

    def __post_init__(self) -> None:
        object.__setattr__(self, "target", validate_target(self.target))
        if not self.ports:
            raise ConfigurationError("at least one port is required")
        if any(isinstance(port, bool) or not isinstance(port, int) for port in self.ports):
            raise ConfigurationError("every port must be an integer")
        normalized_ports = tuple(sorted(set(self.ports)))
        if any(not MIN_PORT <= port <= MAX_PORT for port in normalized_ports):
            raise ConfigurationError("every port must be between 1 and 65535")
        object.__setattr__(self, "ports", normalized_ports)

        if (
            isinstance(self.concurrency, bool)
            or not isinstance(self.concurrency, int)
            or not 1 <= self.concurrency <= MAX_CONCURRENCY
        ):
            raise ConfigurationError(f"concurrency must be between 1 and {MAX_CONCURRENCY}")
        if not _valid_float(self.connect_timeout, minimum=0.05, maximum=10.0):
            raise ConfigurationError("connect timeout must be between 0.05 and 10 seconds")
        if not _valid_float(self.banner_timeout, minimum=0.05, maximum=2.0):
            raise ConfigurationError("banner timeout must be between 0.05 and 2 seconds")
        if (
            isinstance(self.banner_bytes, bool)
            or not isinstance(self.banner_bytes, int)
            or not 1 <= self.banner_bytes <= 4_096
        ):
            raise ConfigurationError("banner byte limit must be between 1 and 4096")
        if (
            isinstance(self.max_resolved_addresses, bool)
            or not isinstance(self.max_resolved_addresses, int)
            or not 1 <= self.max_resolved_addresses <= MAX_RESOLVED_ADDRESSES
        ):
            raise ConfigurationError(
                f"resolved address limit must be between 1 and {MAX_RESOLVED_ADDRESSES}"
            )
        if len(normalized_ports) > DEFAULT_PORT_LIMIT and not self.allow_large_scan:
            raise ConfigurationError(
                f"{len(normalized_ports)} ports exceed the safe default limit of "
                f"{DEFAULT_PORT_LIMIT}; pass --allow-large-scan only with authorization"
            )
        if len(normalized_ports) > ABSOLUTE_PORT_LIMIT:
            raise ConfigurationError("too many ports requested")


def _valid_float(value: object, minimum: float, maximum: float) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    numeric = float(value)
    return math.isfinite(numeric) and minimum <= numeric <= maximum
