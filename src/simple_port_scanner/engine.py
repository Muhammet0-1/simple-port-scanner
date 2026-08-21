"""Bounded concurrent scan orchestration."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from datetime import datetime, timezone
from typing import Protocol

from .config import ScanConfig
from .errors import ScanError
from .models import ResolvedAddress, ScanResult, ScanSummary
from .probe import TCPConnectProbe
from .resolution import TargetResolver


class Resolver(Protocol):
    def resolve(self, config: ScanConfig) -> tuple[ResolvedAddress, ...]: ...


class Probe(Protocol):
    def scan(self, address: ResolvedAddress, port: int, config: ScanConfig) -> ScanResult: ...


Task = tuple[ResolvedAddress, int]
MAX_TOTAL_PROBES = 65_535


class ScanEngine:
    """Resolve once, then keep only a small bounded set of probes in flight."""

    def __init__(
        self,
        resolver: Resolver | None = None,
        probe: Probe | None = None,
        wall_clock: Callable[[], datetime] | None = None,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._resolver = resolver or TargetResolver()
        self._probe = probe or TCPConnectProbe()
        self._wall_clock = wall_clock or (lambda: datetime.now(timezone.utc))
        self._monotonic = monotonic

    def run(self, config: ScanConfig) -> ScanSummary:
        addresses = self._resolver.resolve(config)
        probe_count = len(addresses) * len(config.ports)
        if probe_count > MAX_TOTAL_PROBES:
            raise ScanError(
                f"scan would create {probe_count} probes, exceeding the absolute limit of "
                f"{MAX_TOTAL_PROBES}"
            )
        started_at = self._wall_clock().astimezone(timezone.utc).isoformat()
        started = self._monotonic()
        tasks = ((address, port) for address in addresses for port in config.ports)
        results = self._run_bounded(tasks, config)
        results.sort(
            key=lambda item: (
                item.address.ip_version,
                item.address.address,
                item.address.scope_id,
                item.port,
            )
        )
        return ScanSummary(
            target=config.target,
            started_at=started_at,
            duration_seconds=max(0.0, self._monotonic() - started),
            addresses=addresses,
            ports=config.ports,
            results=tuple(results),
        )

    def _run_bounded(self, tasks: Iterator[Task], config: ScanConfig) -> list[ScanResult]:
        results: list[ScanResult] = []
        pending: dict[Future[ScanResult], Task] = {}
        capacity = config.concurrency * 2
        executor = ThreadPoolExecutor(
            max_workers=config.concurrency,
            thread_name_prefix="port-scan",
        )
        try:
            exhausted = self._fill(executor, pending, tasks, capacity, config)
            while pending:
                completed, _ = wait(pending, return_when=FIRST_COMPLETED)
                for future in completed:
                    task = pending.pop(future)
                    try:
                        results.append(future.result())
                    except Exception as exc:
                        for remaining in pending:
                            remaining.cancel()
                        address, port = task
                        raise ScanError(
                            f"unexpected probe failure for {address.display}:{port}"
                        ) from exc
                if not exhausted:
                    exhausted = self._fill(executor, pending, tasks, capacity, config)
        finally:
            executor.shutdown(wait=True, cancel_futures=True)
        return results

    def _fill(
        self,
        executor: ThreadPoolExecutor,
        pending: dict[Future[ScanResult], Task],
        tasks: Iterator[Task],
        capacity: int,
        config: ScanConfig,
    ) -> bool:
        while len(pending) < capacity:
            try:
                address, port = next(tasks)
            except StopIteration:
                return True
            future = executor.submit(self._probe.scan, address, port, config)
            pending[future] = (address, port)
        return False
