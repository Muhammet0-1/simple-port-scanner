"""Safe, authorized TCP connect scanning primitives."""

from .config import ScanConfig, parse_ports
from .engine import ScanEngine
from .models import PortState, ResolvedAddress, ScanResult, ScanSummary

__all__ = [
    "PortState",
    "ResolvedAddress",
    "ScanConfig",
    "ScanEngine",
    "ScanResult",
    "ScanSummary",
    "parse_ports",
]

__version__ = "1.0.0"
