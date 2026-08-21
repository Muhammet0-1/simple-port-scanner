"""Deterministic terminal and machine-readable reporting."""

from __future__ import annotations

import json

from .models import PortState, ScanResult, ScanSummary


def render_report(summary: ScanSummary, output_format: str, show_all: bool = False) -> str:
    if output_format == "json":
        return json.dumps(summary.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
    if output_format == "jsonl":
        return _render_jsonl(summary)
    if output_format != "text":
        raise ValueError(f"unsupported output format: {output_format}")
    return _render_text(summary, show_all=show_all)


def _render_text(summary: ScanSummary, show_all: bool) -> str:
    addresses = ", ".join(address.display for address in summary.addresses)
    lines = [
        f"Target: {summary.target}",
        f"Resolved: {addresses}",
        f"Ports: {len(summary.ports)} | Addresses: {len(summary.addresses)}",
        "",
    ]
    visible = (
        summary.results
        if show_all
        else tuple(
            result
            for result in summary.results
            if result.state in (PortState.OPEN, PortState.ERROR)
        )
    )
    if not visible:
        lines.append("No open ports were found.")
    else:
        for result in visible:
            lines.append(_format_result(result))
    counts = summary.counts
    lines.extend(
        [
            "",
            (
                "Summary: "
                f"open={counts['open']} closed={counts['closed']} "
                f"filtered={counts['filtered']} error={counts['error']} "
                f"duration={summary.duration_seconds:.3f}s"
            ),
        ]
    )
    return "\n".join(lines)


def _format_result(result: ScanResult) -> str:
    details: list[str] = []
    if result.service:
        details.append(f"service={result.service}")
    if result.banner:
        details.append(f"banner={result.banner!r}")
    if result.error:
        details.append(f"error={result.error}")
    suffix = f" ({', '.join(details)})" if details else ""
    host = (
        f"[{result.address.display}]" if result.address.ip_version == 6 else result.address.display
    )
    return f"{host}:{result.port} {result.state.value} {result.latency_ms:.3f}ms{suffix}"


def _render_jsonl(summary: ScanSummary) -> str:
    header = {
        "type": "scan",
        "schema_version": 1,
        "target": summary.target,
        "started_at": summary.started_at,
        "addresses": [address.to_dict() for address in summary.addresses],
        "ports": list(summary.ports),
    }
    lines = [json.dumps(header, ensure_ascii=False, sort_keys=True)]
    lines.extend(
        json.dumps({"type": "result", **result.to_dict()}, ensure_ascii=False, sort_keys=True)
        for result in summary.results
    )
    footer = {
        "type": "summary",
        "duration_seconds": round(summary.duration_seconds, 3),
        "counts": summary.counts,
    }
    lines.append(json.dumps(footer, ensure_ascii=False, sort_keys=True))
    return "\n".join(lines)
