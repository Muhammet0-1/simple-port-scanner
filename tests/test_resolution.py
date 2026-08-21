from __future__ import annotations

import socket
from typing import Any

import pytest

from simple_port_scanner.config import ScanConfig
from simple_port_scanner.errors import ResolutionError
from simple_port_scanner.resolution import TargetResolver


def record(family: int, address: str, scope_id: int = 0) -> tuple[Any, ...]:
    sockaddr: tuple[Any, ...] = (
        (address, 0, 0, scope_id) if family == socket.AF_INET6 else (address, 0)
    )
    return (family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr)


def resolver_with(*records: tuple[Any, ...]) -> TargetResolver:
    return TargetResolver(getaddrinfo=lambda *_args, **_kwargs: records)


def test_resolver_deduplicates_and_sorts_pinned_addresses() -> None:
    resolver = resolver_with(
        record(socket.AF_INET6, "::1"),
        record(socket.AF_INET, "127.0.0.2"),
        record(socket.AF_INET, "127.0.0.1"),
        record(socket.AF_INET, "127.0.0.1"),
    )
    addresses = resolver.resolve(ScanConfig(target="localhost", ports=(80,)))
    assert [(item.ip_version, item.address) for item in addresses] == [
        (4, "127.0.0.1"),
        (4, "127.0.0.2"),
        (6, "::1"),
    ]


def test_public_address_requires_extra_opt_in() -> None:
    resolver = resolver_with(record(socket.AF_INET, "8.8.8.8"))
    with pytest.raises(ResolutionError, match="allow-public-target"):
        resolver.resolve(ScanConfig(target="dns.google", ports=(53,)))
    addresses = resolver.resolve(
        ScanConfig(target="dns.google", ports=(53,), allow_public_target=True)
    )
    assert addresses[0].address == "8.8.8.8"


@pytest.mark.parametrize("address", ["0.0.0.0", "224.0.0.1", "::", "ff02::1"])
def test_resolver_rejects_unspecified_and_multicast(address: str) -> None:
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    with pytest.raises(ResolutionError, match="prohibited"):
        resolver_with(record(family, address)).resolve(
            ScanConfig(target=address, ports=(80,), allow_public_target=True)
        )


def test_resolver_preserves_ipv6_scope_id() -> None:
    address = resolver_with(record(socket.AF_INET6, "fe80::1", 7)).resolve(
        ScanConfig(target="fe80::1%7", ports=(80,))
    )[0]
    assert address.scope_id == 7
    assert address.socket_address(443) == ("fe80::1", 443, 0, 7)


def test_resolver_enforces_address_limit_after_deduplication() -> None:
    resolver = resolver_with(
        record(socket.AF_INET, "127.0.0.1"),
        record(socket.AF_INET, "127.0.0.2"),
    )
    with pytest.raises(ResolutionError, match="exceeding"):
        resolver.resolve(ScanConfig(target="localhost", ports=(80,), max_resolved_addresses=1))


def test_resolver_wraps_name_resolution_failure() -> None:
    def fail(*_args: object, **_kwargs: object) -> list[tuple[Any, ...]]:
        raise socket.gaierror(socket.EAI_NONAME, "not found")

    with pytest.raises(ResolutionError, match="could not be resolved"):
        TargetResolver(getaddrinfo=fail).resolve(ScanConfig(target="missing.invalid", ports=(80,)))
