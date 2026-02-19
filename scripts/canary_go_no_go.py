"""Evaluate canary report against rollout thresholds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate OmniSwarm canary go/no-go.")
    parser.add_argument("--report", type=str, default="canary_report.json")
    parser.add_argument("--min-success-rate", type=float, default=0.98)
    parser.add_argument("--max-verification-failure-rate", type=float, default=0.20)
    parser.add_argument("--max-latency-p95-sec", type=float, default=5.0)
    parser.add_argument("--max-failures", type=int, default=1)
    parser.add_argument("--output", type=str, default="canary_gate_report.json")
    args = parser.parse_args()

    report_path = Path(args.report)
    report = json.loads(report_path.read_text(encoding="utf-8"))

    reasons: list[str] = []
    if report.get("success_rate", 0.0) < args.min_success_rate:
        reasons.append(
            f"success_rate {report.get('success_rate')} < {args.min_success_rate}"
        )
    if report.get("verification_failure_rate", 1.0) > args.max_verification_failure_rate:
        reasons.append(
            "verification_failure_rate "
            f"{report.get('verification_failure_rate')} > {args.max_verification_failure_rate}"
        )
    if report.get("latency_p95_sec", 999.0) > args.max_latency_p95_sec:
        reasons.append(
            f"latency_p95_sec {report.get('latency_p95_sec')} > {args.max_latency_p95_sec}"
        )
    if report.get("total_failures", 999) > args.max_failures:
        reasons.append(
            f"total_failures {report.get('total_failures')} > {args.max_failures}"
        )

    status = "GO" if not reasons else "NO_GO"
    gate_report = {
        "status": status,
        "reasons": reasons,
        "input_report": str(report_path.resolve()),
        "thresholds": {
            "min_success_rate": args.min_success_rate,
            "max_verification_failure_rate": args.max_verification_failure_rate,
            "max_latency_p95_sec": args.max_latency_p95_sec,
            "max_failures": args.max_failures,
        },
        "metrics": {
            "success_rate": report.get("success_rate"),
            "verification_failure_rate": report.get("verification_failure_rate"),
            "latency_p95_sec": report.get("latency_p95_sec"),
            "total_failures": report.get("total_failures"),
        },
    }

    out_path = Path(args.output)
    out_path.write_text(json.dumps(gate_report, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"[CANARY_GATE] status={status}")
    print(f"[CANARY_GATE] report={out_path.resolve()}")
    return 0 if status == "GO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
