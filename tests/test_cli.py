from __future__ import annotations

import json
import socket

import pytest

from simple_port_scanner import cli
from simple_port_scanner.models import PortState, ResolvedAddress, ScanResult, ScanSummary

ADDRESS = ResolvedAddress(socket.AddressFamily.AF_INET, "127.0.0.1")


def completed_summary() -> ScanSummary:
    return ScanSummary(
        target="127.0.0.1",
        started_at="2026-08-20T12:00:00+00:00",
        duration_seconds=0.01,
        addresses=(ADDRESS,),
        ports=(80,),
        results=(ScanResult(ADDRESS, 80, PortState.CLOSED, 1.0),),
    )


class FakeEngine:
    last_config = None

    def run(self, config):
        type(self).last_config = config
        return completed_summary()


def test_cli_requires_authorization_acknowledgement(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        cli.main(["--target", "127.0.0.1", "--ports", "80"])
    assert raised.value.code == 2
    assert "acknowledge-authorization" in capsys.readouterr().err


def test_cli_runs_engine_and_emits_json(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.setattr(cli, "ScanEngine", FakeEngine)
    exit_code = cli.main(
        [
            "--target",
            "127.0.0.1",
            "--ports",
            "80,443",
            "--acknowledge-authorization",
            "--format",
            "json",
            "--banner",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["target"] == "127.0.0.1"
    assert FakeEngine.last_config.ports == (80, 443)
    assert FakeEngine.last_config.banner is True


@pytest.mark.parametrize(
    "arguments",
    [
        ["--target", "127.0.0.1", "--ports", "80", "--concurrency", "0"],
        ["--target", "127.0.0.1", "--ports", "1-1025"],
        ["--target", "https://example.com", "--ports", "80"],
    ],
)
def test_cli_reports_invalid_configuration_without_traceback(arguments, capsys) -> None:
    with pytest.raises(SystemExit) as raised:
        cli.main([*arguments, "--acknowledge-authorization"])
    assert raised.value.code == 2
    captured = capsys.readouterr()
    assert "Traceback" not in captured.err


def test_cli_help_does_not_start_a_scan(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        cli.main(["--help"])
    assert raised.value.code == 0
    assert "Bounded TCP connect scanner" in capsys.readouterr().out
