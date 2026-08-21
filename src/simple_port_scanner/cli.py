"""Command-line interface for explicitly authorized TCP connect scans."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from . import __version__
from .config import ScanConfig, parse_ports, validate_target
from .engine import ScanEngine
from .errors import ConfigurationError, ResolutionError, ScanError
from .reporting import render_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="simple-port-scanner",
        description=(
            "Bounded TCP connect scanner for systems you own or are explicitly authorized to test."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--target", required=True, type=_target_argument, help="one hostname or IP")
    parser.add_argument(
        "--ports",
        required=True,
        type=_ports_argument,
        metavar="SPEC",
        help="comma-separated ports/ranges, for example 22,80,443,8000-8010",
    )
    parser.add_argument(
        "--acknowledge-authorization",
        action="store_true",
        help="confirm that you own the target or have explicit permission to scan it",
    )
    parser.add_argument(
        "--allow-public-target",
        action="store_true",
        help="permit globally routable resolved addresses after authorization is confirmed",
    )
    parser.add_argument(
        "--allow-large-scan",
        action="store_true",
        help="permit more than 1024 ports after authorization is confirmed",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=32,
        metavar="N",
        help="simultaneous connect attempts, 1-256 (default: 32)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=0.75,
        metavar="SECONDS",
        help="connect timeout, 0.05-10 (default: 0.75)",
    )
    parser.add_argument(
        "--banner",
        action="store_true",
        help="passively receive up to --banner-bytes after a successful connection",
    )
    parser.add_argument(
        "--banner-timeout",
        type=float,
        default=0.5,
        metavar="SECONDS",
        help="passive banner receive timeout, 0.05-2 (default: 0.5)",
    )
    parser.add_argument(
        "--banner-bytes",
        type=int,
        default=256,
        metavar="N",
        help="maximum passive banner bytes, 1-4096 (default: 256)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "jsonl"),
        default="text",
        dest="output_format",
        help="stdout report format (default: text)",
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="include closed and filtered results in text output",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.acknowledge_authorization:
        parser.error("--acknowledge-authorization is required")

    try:
        config = ScanConfig(
            target=args.target,
            ports=args.ports,
            concurrency=args.concurrency,
            connect_timeout=args.timeout,
            banner=args.banner,
            banner_timeout=args.banner_timeout,
            banner_bytes=args.banner_bytes,
            allow_public_target=args.allow_public_target,
            allow_large_scan=args.allow_large_scan,
        )
        summary = ScanEngine().run(config)
        report = render_report(summary, args.output_format, show_all=args.show_all)
        sys.stdout.write(report)
        sys.stdout.write("\n")
        sys.stdout.flush()
    except (ConfigurationError, ResolutionError) as exc:
        parser.error(str(exc))
    except ScanError as exc:
        print(f"scan failed: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("scan interrupted", file=sys.stderr)
        return 130
    except BrokenPipeError:
        return 0
    return 0


def _target_argument(value: str) -> str:
    try:
        return validate_target(value)
    except ConfigurationError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _ports_argument(value: str) -> tuple[int, ...]:
    try:
        return parse_ports(value)
    except ConfigurationError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
