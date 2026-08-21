from __future__ import annotations

import socket
from datetime import datetime, timezone

import pytest

from simple_port_scanner.config import ScanConfig
from simple_port_scanner.engine import ScanEngine
from simple_port_scanner.errors import ScanError
from simple_port_scanner.models import PortState, ResolvedAddress, ScanResult

IPV4 = ResolvedAddress(socket.AddressFamily.AF_INET, "127.0.0.2")
IPV6 = ResolvedAddress(socket.AddressFamily.AF_INET6, "::1")


class FakeResolver:
    def resolve(self, _config: ScanConfig) -> tuple[ResolvedAddress, ...]:
        return (IPV6, IPV4)


class FakeProbe:
    def scan(self, address: ResolvedAddress, port: int, _config: ScanConfig) -> ScanResult:
        return ScanResult(address, port, PortState.OPEN, float(port), service="test")


def test_engine_returns_sorted_deterministic_summary() -> None:
    ticks = iter((10.0, 10.25))
    engine = ScanEngine(
        resolver=FakeResolver(),
        probe=FakeProbe(),
        wall_clock=lambda: datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc),
        monotonic=lambda: next(ticks),
    )
    summary = engine.run(ScanConfig(target="localhost", ports=(443, 22), concurrency=2))
    assert summary.started_at == "2026-08-20T12:00:00+00:00"
    assert summary.duration_seconds == pytest.approx(0.25)
    assert [(item.address.address, item.port) for item in summary.results] == [
        ("127.0.0.2", 22),
        ("127.0.0.2", 443),
        ("::1", 22),
        ("::1", 443),
    ]
    assert summary.counts == {"open": 4, "closed": 0, "filtered": 0, "error": 0}


class BrokenProbe:
    def scan(self, _address: ResolvedAddress, _port: int, _config: ScanConfig) -> ScanResult:
        raise RuntimeError("internal detail")


def test_engine_wraps_unexpected_worker_failures() -> None:
    engine = ScanEngine(resolver=FakeResolver(), probe=BrokenProbe())
    with pytest.raises(ScanError, match=r"127\.0\.0\.2|::1") as raised:
        engine.run(ScanConfig(target="localhost", ports=(80,), concurrency=1))
    assert "internal detail" not in str(raised.value)


class ManyAddressResolver:
    def resolve(self, _config: ScanConfig) -> tuple[ResolvedAddress, ...]:
        return (IPV4, IPV6)


def test_engine_rejects_excessive_total_probe_count_before_workers_start() -> None:
    config = ScanConfig(
        target="localhost",
        ports=tuple(range(1, 40_001)),
        allow_large_scan=True,
    )
    with pytest.raises(ScanError, match="absolute limit"):
        ScanEngine(resolver=ManyAddressResolver(), probe=FakeProbe()).run(config)
