from __future__ import annotations

import json
import socket

from simple_port_scanner.models import PortState, ResolvedAddress, ScanResult, ScanSummary
from simple_port_scanner.reporting import render_report

ADDRESS = ResolvedAddress(socket.AddressFamily.AF_INET, "127.0.0.1")


def summary() -> ScanSummary:
    return ScanSummary(
        target="localhost",
        started_at="2026-08-20T12:00:00+00:00",
        duration_seconds=0.1256,
        addresses=(ADDRESS,),
        ports=(22, 23),
        results=(
            ScanResult(ADDRESS, 22, PortState.OPEN, 1.2345, service="ssh", banner="hello"),
            ScanResult(ADDRESS, 23, PortState.CLOSED, 2.0),
        ),
    )


def test_summary_to_dict_is_schema_versioned() -> None:
    data = summary().to_dict()
    assert data["schema_version"] == 1
    assert data["duration_seconds"] == 0.126
    assert data["counts"] == {"open": 1, "closed": 1, "filtered": 0, "error": 0}
    assert data["results"][0]["latency_ms"] == 1.234


def test_text_report_hides_closed_ports_by_default() -> None:
    report = render_report(summary(), "text")
    assert "127.0.0.1:22 open" in report
    assert "127.0.0.1:23 closed" not in report
    assert "open=1 closed=1" in report


def test_text_report_can_show_all_states() -> None:
    assert "127.0.0.1:23 closed" in render_report(summary(), "text", show_all=True)


def test_json_report_round_trips() -> None:
    data = json.loads(render_report(summary(), "json"))
    assert data["target"] == "localhost"
    assert [item["state"] for item in data["results"]] == ["open", "closed"]


def test_jsonl_report_has_header_results_and_footer() -> None:
    records = [json.loads(line) for line in render_report(summary(), "jsonl").splitlines()]
    assert [record["type"] for record in records] == ["scan", "result", "result", "summary"]
    assert records[-1]["counts"]["open"] == 1


def test_unknown_output_format_is_rejected() -> None:
    try:
        render_report(summary(), "xml")
    except ValueError as exc:
        assert "unsupported output format" in str(exc)
    else:
        raise AssertionError("expected ValueError")
