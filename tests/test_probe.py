from __future__ import annotations

import errno
import socket
from collections.abc import Iterator

import pytest

from simple_port_scanner.config import ScanConfig
from simple_port_scanner.models import PortState, ResolvedAddress
from simple_port_scanner.probe import TCPConnectProbe


class FakeSocket:
    def __init__(
        self,
        status: int = 0,
        payload: bytes = b"",
        connect_error: OSError | None = None,
        recv_error: OSError | None = None,
    ) -> None:
        self.status = status
        self.payload = payload
        self.connect_error = connect_error
        self.recv_error = recv_error
        self.timeouts: list[float | None] = []
        self.connected_to: tuple[object, ...] | None = None
        self.closed = False

    def settimeout(self, value: float | None) -> None:
        self.timeouts.append(value)

    def connect_ex(self, address: tuple[object, ...]) -> int:
        self.connected_to = address
        if self.connect_error:
            raise self.connect_error
        return self.status

    def recv(self, size: int) -> bytes:
        if self.recv_error:
            raise self.recv_error
        return self.payload[:size]

    def close(self) -> None:
        self.closed = True


def clock(*values: float) -> callable:
    iterator: Iterator[float] = iter(values)
    return lambda: next(iterator)


def address() -> ResolvedAddress:
    return ResolvedAddress(socket.AddressFamily.AF_INET, "127.0.0.1")


@pytest.mark.parametrize(
    ("status", "state"),
    [
        (0, PortState.OPEN),
        (errno.ECONNREFUSED, PortState.CLOSED),
        (errno.ETIMEDOUT, PortState.FILTERED),
        (errno.EHOSTUNREACH, PortState.FILTERED),
        (999, PortState.ERROR),
    ],
)
def test_probe_maps_connect_status_and_closes_socket(status: int, state: PortState) -> None:
    client = FakeSocket(status=status)
    probe = TCPConnectProbe(
        socket_factory=lambda *_args: client,
        monotonic=clock(1.0, 1.025),
        service_lookup=lambda *_args: "http",
    )
    result = probe.scan(address(), 80, ScanConfig(target="127.0.0.1", ports=(80,)))
    assert result.state is state
    assert result.latency_ms == pytest.approx(25.0)
    assert client.connected_to == ("127.0.0.1", 80)
    assert client.closed


def test_banner_is_opt_in_and_sanitized() -> None:
    client = FakeSocket(payload=b"SSH-2.0-Test\r\n\x1b[31m")
    probe = TCPConnectProbe(
        socket_factory=lambda *_args: client,
        monotonic=clock(2.0, 2.01),
        service_lookup=lambda *_args: "ssh",
    )
    config = ScanConfig(target="127.0.0.1", ports=(22,), banner=True, banner_bytes=64)
    result = probe.scan(address(), 22, config)
    assert result.banner == "SSH-2.0-Test [31m"
    assert result.service == "ssh"
    assert client.timeouts == [0.75, 0.5]


def test_banner_is_not_read_by_default() -> None:
    client = FakeSocket(payload=b"secret")
    probe = TCPConnectProbe(
        socket_factory=lambda *_args: client,
        monotonic=clock(1.0, 1.1),
    )
    result = probe.scan(address(), 80, ScanConfig(target="127.0.0.1", ports=(80,)))
    assert result.banner is None
    assert client.timeouts == [0.75]


def test_banner_timeout_does_not_change_open_state() -> None:
    client = FakeSocket(recv_error=TimeoutError())
    probe = TCPConnectProbe(
        socket_factory=lambda *_args: client,
        monotonic=clock(1.0, 1.1),
    )
    result = probe.scan(
        address(),
        80,
        ScanConfig(target="127.0.0.1", ports=(80,), banner=True),
    )
    assert result.state is PortState.OPEN
    assert result.banner is None


def test_os_error_is_reduced_to_a_non_sensitive_error_code() -> None:
    client = FakeSocket(connect_error=OSError(errno.EMFILE, "/sensitive/path"))
    probe = TCPConnectProbe(
        socket_factory=lambda *_args: client,
        monotonic=clock(1.0, 1.1),
    )
    result = probe.scan(address(), 80, ScanConfig(target="127.0.0.1", ports=(80,)))
    assert result.state is PortState.ERROR
    assert result.error == "EMFILE"
    assert "/sensitive" not in str(result.to_dict())
