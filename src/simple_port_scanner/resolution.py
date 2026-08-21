"""Resolve and pin a single authorized target before any connection attempts."""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable, Iterable
from typing import Any

from .config import ScanConfig
from .errors import ResolutionError
from .models import ResolvedAddress

GetAddrInfo = Callable[..., Iterable[tuple[Any, Any, Any, Any, tuple[Any, ...]]]]


class TargetResolver:
    """Resolve a hostname once and validate every resulting address."""

    def __init__(self, getaddrinfo: GetAddrInfo = socket.getaddrinfo) -> None:
        self._getaddrinfo = getaddrinfo

    def resolve(self, config: ScanConfig) -> tuple[ResolvedAddress, ...]:
        try:
            records = self._getaddrinfo(
                config.target,
                None,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            )
        except (socket.gaierror, UnicodeError, ValueError) as exc:
            raise ResolutionError(f"target could not be resolved: {config.target}") from exc

        addresses: dict[tuple[int, str, int], ResolvedAddress] = {}
        for family_raw, _socktype, _protocol, _canonical, sockaddr in records:
            family = socket.AddressFamily(family_raw)
            if family not in (socket.AddressFamily.AF_INET, socket.AddressFamily.AF_INET6):
                continue
            address = str(sockaddr[0])
            scope_id = int(sockaddr[3]) if family is socket.AddressFamily.AF_INET6 else 0
            parsed = ipaddress.ip_address(address)
            if parsed.is_unspecified or parsed.is_multicast:
                raise ResolutionError(f"target resolved to a prohibited address: {address}")
            if parsed.is_global and not config.allow_public_target:
                raise ResolutionError(
                    f"target resolved to public address {address}; pass --allow-public-target "
                    "only when you have explicit authorization"
                )
            key = (int(family), address, scope_id)
            addresses[key] = ResolvedAddress(family=family, address=address, scope_id=scope_id)

        if not addresses:
            raise ResolutionError(f"target has no usable IPv4 or IPv6 addresses: {config.target}")
        if len(addresses) > config.max_resolved_addresses:
            raise ResolutionError(
                f"target resolved to {len(addresses)} addresses, exceeding the configured "
                f"limit of {config.max_resolved_addresses}"
            )
        return tuple(sorted(addresses.values(), key=_address_sort_key))


def _address_sort_key(item: ResolvedAddress) -> tuple[int, str, int]:
    return (item.ip_version, item.address, item.scope_id)
