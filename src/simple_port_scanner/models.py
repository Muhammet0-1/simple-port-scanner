"""Immutable models used by the resolver, scanner, and reporters."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from socket import AddressFamily
from typing import Any


class PortState(str, Enum):
    """A conservative interpretation of one TCP connect attempt."""

    OPEN = "open"
    CLOSED = "closed"
    FILTERED = "filtered"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ResolvedAddress:
    """A DNS result pinned before scanning starts."""

    family: AddressFamily
    address: str
    scope_id: int = 0

    @property
    def ip_version(self) -> int:
        return 6 if self.family is AddressFamily.AF_INET6 else 4

    @property
    def display(self) -> str:
        if self.ip_version == 6 and self.scope_id:
            return f"{self.address}%{self.scope_id}"
        return self.address

    def socket_address(self, port: int) -> tuple[str, int] | tuple[str, int, int, int]:
        if self.family is AddressFamily.AF_INET6:
            return (self.address, port, 0, self.scope_id)
        return (self.address, port)

    def to_dict(self) -> dict[str, Any]:
        return {
            "address": self.address,
            "ip_version": self.ip_version,
            "scope_id": self.scope_id,
        }


@dataclass(frozen=True, slots=True)
class ScanResult:
    """Outcome of probing one address and TCP port."""

    address: ResolvedAddress
    port: int
    state: PortState
    latency_ms: float
    service: str | None = None
    banner: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "address": self.address.address,
            "ip_version": self.address.ip_version,
            "port": self.port,
            "state": self.state.value,
            "latency_ms": round(self.latency_ms, 3),
        }
        if self.address.scope_id:
            data["scope_id"] = self.address.scope_id
        if self.service is not None:
            data["service"] = self.service
        if self.banner is not None:
            data["banner"] = self.banner
        if self.error is not None:
            data["error"] = self.error
        return data


@dataclass(frozen=True, slots=True)
class ScanSummary:
    """Complete deterministic scan report."""

    target: str
    started_at: str
    duration_seconds: float
    addresses: tuple[ResolvedAddress, ...]
    ports: tuple[int, ...]
    results: tuple[ScanResult, ...]

    @property
    def counts(self) -> dict[str, int]:
        return {
            state.value: sum(result.state is state for result in self.results)
            for state in PortState
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "target": self.target,
            "started_at": self.started_at,
            "duration_seconds": round(self.duration_seconds, 3),
            "addresses": [address.to_dict() for address in self.addresses],
            "ports": list(self.ports),
            "counts": self.counts,
            "results": [result.to_dict() for result in self.results],
        }
