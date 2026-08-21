"""One bounded TCP connect probe with optional passive banner reception."""

from __future__ import annotations

import errno
import socket
import time
from collections.abc import Callable
from typing import Protocol

from .config import ScanConfig
from .models import PortState, ResolvedAddress, ScanResult


class SocketLike(Protocol):
    def settimeout(self, value: float | None) -> None: ...

    def connect_ex(self, address: tuple[object, ...]) -> int: ...

    def recv(self, size: int) -> bytes: ...

    def close(self) -> None: ...


SocketFactory = Callable[[int, int], SocketLike]
Clock = Callable[[], float]

_FILTERED_CODES = {
    errno.EACCES,
    errno.EHOSTDOWN,
    errno.EHOSTUNREACH,
    errno.ENETDOWN,
    errno.ENETUNREACH,
    errno.EPERM,
    errno.ETIMEDOUT,
}


class TCPConnectProbe:
    """Perform a normal userspace TCP connection without raw packets or evasion."""

    def __init__(
        self,
        socket_factory: SocketFactory = socket.socket,
        monotonic: Clock = time.monotonic,
        service_lookup: Callable[[int, str], str] = socket.getservbyport,
    ) -> None:
        self._socket_factory = socket_factory
        self._monotonic = monotonic
        self._service_lookup = service_lookup

    def scan(self, address: ResolvedAddress, port: int, config: ScanConfig) -> ScanResult:
        started = self._monotonic()
        client: SocketLike | None = None
        try:
            client = self._socket_factory(int(address.family), socket.SOCK_STREAM)
            client.settimeout(config.connect_timeout)
            status = client.connect_ex(address.socket_address(port))
            latency = _milliseconds(self._monotonic() - started)
            if status == 0:
                banner = self._read_banner(client, config) if config.banner else None
                return ScanResult(
                    address=address,
                    port=port,
                    state=PortState.OPEN,
                    latency_ms=latency,
                    service=self._service(port),
                    banner=banner,
                )
            if status == errno.ECONNREFUSED:
                state = PortState.CLOSED
            elif status in _FILTERED_CODES:
                state = PortState.FILTERED
            else:
                state = PortState.ERROR
            return ScanResult(
                address=address,
                port=port,
                state=state,
                latency_ms=latency,
                error=None if state is not PortState.ERROR else _errno_message(status),
            )
        except TimeoutError:
            return ScanResult(
                address=address,
                port=port,
                state=PortState.FILTERED,
                latency_ms=_milliseconds(self._monotonic() - started),
            )
        except OSError as exc:
            return ScanResult(
                address=address,
                port=port,
                state=PortState.ERROR,
                latency_ms=_milliseconds(self._monotonic() - started),
                error=_safe_os_error(exc),
            )
        finally:
            if client is not None:
                client.close()

    def _service(self, port: int) -> str | None:
        try:
            return self._service_lookup(port, "tcp")
        except OSError:
            return None

    @staticmethod
    def _read_banner(client: SocketLike, config: ScanConfig) -> str | None:
        client.settimeout(config.banner_timeout)
        try:
            payload = client.recv(config.banner_bytes)
        except (TimeoutError, OSError):
            return None
        if not payload:
            return None
        decoded = payload.decode("utf-8", errors="replace")
        printable = "".join(character if character.isprintable() else " " for character in decoded)
        normalized = " ".join(printable.split())
        return normalized or None


def _milliseconds(seconds: float) -> float:
    return max(0.0, seconds * 1_000.0)


def _errno_message(status: int) -> str:
    try:
        return errno.errorcode.get(status, "socket error")
    except (TypeError, ValueError):
        return "socket error"


def _safe_os_error(exc: OSError) -> str:
    if exc.errno is not None:
        return errno.errorcode.get(exc.errno, "socket error")
    return type(exc).__name__
