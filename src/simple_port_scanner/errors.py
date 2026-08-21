"""Project-specific exceptions."""


class PortScannerError(Exception):
    """Base error for expected scanner failures."""


class ConfigurationError(PortScannerError):
    """Raised when user-controlled configuration is invalid."""


class ResolutionError(PortScannerError):
    """Raised when a target cannot be resolved safely."""


class ScanError(PortScannerError):
    """Raised when the scan engine cannot complete."""
