#!/usr/bin/env python3
"""
analyze_results.py

Reads all result JSON files from the results/ directory and prints
a comparison table grouped by environment and variant.

Usage:
    python scripts/analyze_results.py
    python scripts/analyze_results.py --results-dir /path/to/results
    python scripts/analyze_results.py --export results_summary.csv
"""

import argparse
import csv
import json
import sys
from pathlib import Path


# ── ANSI colors (disabled on Windows if no ANSI support) ────────────────────
def supports_ansi() -> bool:
    import os
    return os.name != "nt" or "WT_SESSION" in os.environ or "TERM" in os.environ

RESET  = "\033[0m"   if supports_ansi() else ""
BOLD   = "\033[1m"   if supports_ansi() else ""
CYAN   = "\033[36m"  if supports_ansi() else ""
GREEN  = "\033[32m"  if supports_ansi() else ""
YELLOW = "\033[33m"  if supports_ansi() else ""
RED    = "\033[31m"  if supports_ansi() else ""
DIM    = "\033[2m"   if supports_ansi() else ""


def load_results(results_dir: Path) -> list[dict]:
    files = sorted(results_dir.glob("*.json"))
    if not files:
        print(f"No result files found in {results_dir}")
        print("Run the test first: bash scripts/run_test.sh lf")
        sys.exit(1)

    results = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["_file"] = f.name
            results.append(data)
        except Exception as e:
            print(f"WARNING: Could not parse {f.name}: {e}", file=sys.stderr)

    return results


def print_separator(width: int = 80, char: str = "─") -> None:
    print(char * width)


def fmt_tokens(n: int, baseline: int | None = None) -> str:
    """Format token count, optionally with delta from baseline."""
    if baseline is None or baseline == 0:
        return f"{n:>8,}"
    delta = n - baseline
    pct = (delta / baseline) * 100
    sign = "+" if delta >= 0 else ""
    color = RED if delta > 0 else (GREEN if delta < 0 else DIM)
    return f"{n:>8,} {color}({sign}{delta:+,} / {sign}{pct:.1f}%){RESET}"


def analyze(results: list[dict]) -> None:
    VARIANT_ORDER = ["lf", "crlf", "lf_bom", "crlf_bom"]
    ENV_ORDER     = ["macos", "linux", "wsl2", "windows_native"]

    # Group results: {env: {variant: result}}
    grouped: dict[str, dict[str, dict]] = {}
    for r in results:
        env     = r.get("environment", "unknown")
        variant = r.get("variant", "unknown")
        # Keep most recent if duplicate
        if env not in grouped:
            grouped[env] = {}
        if variant not in grouped[env] or r["timestamp"] > grouped[env][variant]["timestamp"]:
            grouped[env][variant] = r

    environments = sorted(grouped.keys(), key=lambda e: ENV_ORDER.index(e) if e in ENV_ORDER else 99)

    print()
    print(f"{BOLD}{'='*80}{RESET}")
    print(f"{BOLD}  Claude Code Token Benchmark — Results Analysis{RESET}")
    print(f"{BOLD}{'='*80}{RESET}")
    print()

    # ── Per-environment table ─────────────────────────────────────────────────
    for env in environments:
        env_data = grouped[env]
        print(f"{CYAN}{BOLD}  Environment: {env.upper()}{RESET}")
        print()

        # Baseline = lf variant
        baseline_tokens = None
        if "lf" in env_data:
            baseline_tokens = env_data["lf"]["tokens"]["input"]

        header = f"  {'Variant':<14}  {'File':>7}  {'Lines':>5}  {'BOM':>3}  {'CRLF':>4}  " \
                 f"{'Input':>8}  {'Output':>6}  {'Cache↑':>7}  {'Cache↓':>7}  {'Total':>8}  {'Time(s)':>7}"
        print(f"{DIM}{header}{RESET}")
        print(f"  {'-'*14}  {'-'*7}  {'-'*5}  {'-'*3}  {'-'*4}  " \
              f"{'-'*8}  {'-'*6}  {'-'*7}  {'-'*7}  {'-'*8}  {'-'*7}")

        for variant in VARIANT_ORDER:
            if variant not in env_data:
                print(f"  {variant:<14}  {'—':>7}  {'—':>5}  {'—':>3}  {'—':>4}  " \
                      f"{'—':>8}  {'—':>6}  {'—':>7}  {'—':>7}  {'—':>8}  {'—':>7}")
                continue

            r   = env_data[variant]
            t   = r["tokens"]
            fm  = r.get("file_metadata", {})

            bom_flag  = "yes" if fm.get("has_bom")  else "no"
            crlf_flag = "yes" if fm.get("has_crlf") else "no"

            delta_color = ""
            if baseline_tokens and variant != "lf":
                diff = t["input"] - baseline_tokens
                delta_color = RED if diff > 0 else (GREEN if diff < 0 else "")

            print(
                f"  {variant:<14}  "
                f"{fm.get('size_bytes', 0):>7,}  "
                f"{fm.get('line_count', 0):>5,}  "
                f"{bom_flag:>3}  "
                f"{crlf_flag:>4}  "
                f"{delta_color}{t['input']:>8,}{RESET}  "
                f"{t['output']:>6,}  "
                f"{t['cache_creation']:>7,}  "
                f"{t['cache_read']:>7,}  "
                f"{t['total']:>8,}  "
                f"{r.get('duration_seconds', 0):>7.3f}"
            )

        print()

    # ── Cross-environment comparison (input tokens for lf baseline) ───────────
    print(f"{CYAN}{BOLD}  Cross-Environment Comparison (input tokens per variant){RESET}")
    print()

    # Header: environments as columns
    col_w = 14
    header = f"  {'Variant':<14}  " + "  ".join(f"{e:<{col_w}}" for e in environments)
    print(f"{DIM}{header}{RESET}")
    print(f"  {'-'*14}  " + "  ".join("-" * col_w for _ in environments))

    for variant in VARIANT_ORDER:
        row = f"  {variant:<14}  "
        cells = []
        for env in environments:
            if variant in grouped.get(env, {}):
                v = grouped[env][variant]["tokens"]["input"]
                cells.append(f"{v:<{col_w},}")
            else:
                cells.append(f"{'—':<{col_w}}")
        row += "  ".join(cells)
        print(row)

    print()

    # ── Findings summary ──────────────────────────────────────────────────────
    print(f"{CYAN}{BOLD}  Key Observations{RESET}")
    print()

    for env in environments:
        if "lf" not in grouped.get(env, {}) or "crlf" not in grouped.get(env, {}):
            continue
        lf_in   = grouped[env]["lf"]["tokens"]["input"]
        crlf_in = grouped[env]["crlf"]["tokens"]["input"]
        diff = crlf_in - lf_in
        if diff != 0:
            pct = abs(diff / lf_in) * 100 if lf_in else 0
            direction = "MORE" if diff > 0 else "FEWER"
            print(f"  [{env}] CRLF vs LF: {abs(diff):,} {direction} input tokens ({pct:.1f}%)")
        else:
            print(f"  [{env}] CRLF vs LF: no difference in input tokens")

    for env in environments:
        if "lf" not in grouped.get(env, {}) or "lf_bom" not in grouped.get(env, {}):
            continue
        lf_in     = grouped[env]["lf"]["tokens"]["input"]
        lf_bom_in = grouped[env]["lf_bom"]["tokens"]["input"]
        diff = lf_bom_in - lf_in
        if diff != 0:
            pct = abs(diff / lf_in) * 100 if lf_in else 0
            direction = "MORE" if diff > 0 else "FEWER"
            print(f"  [{env}] BOM vs no-BOM (LF): {abs(diff):,} {direction} input tokens ({pct:.1f}%)")
        else:
            print(f"  [{env}] BOM vs no-BOM (LF): no difference in input tokens")

    print()
    print(f"{DIM}  Tip: Red input token counts = more than LF baseline.{RESET}")
    print(f"{DIM}       Green = fewer. Gray = baseline.{RESET}")
    print()


def export_csv(results: list[dict], path: Path) -> None:
    rows = []
    for r in results:
        t  = r.get("tokens", {})
        fm = r.get("file_metadata", {})
        rows.append({
            "environment":       r.get("environment"),
            "variant":           r.get("variant"),
            "timestamp":         r.get("timestamp"),
            "file_size_bytes":   fm.get("size_bytes"),
            "line_count":        fm.get("line_count"),
            "has_bom":           fm.get("has_bom"),
            "has_crlf":          fm.get("has_crlf"),
            "duration_seconds":  r.get("duration_seconds"),
            "input_tokens":      t.get("input"),
            "output_tokens":     t.get("output"),
            "cache_creation":    t.get("cache_creation"),
            "cache_read":        t.get("cache_read"),
            "total_tokens":      t.get("total"),
        })

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} rows to {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze Claude Code token benchmark results")
    parser.add_argument("--results-dir", default=None, help="Path to results directory")
    parser.add_argument("--export", default=None, help="Export results to CSV file")
    args = parser.parse_args()

    root = Path(__file__).parent.parent
    results_dir = Path(args.results_dir) if args.results_dir else root / "results"

    results = load_results(results_dir)
    analyze(results)

    if args.export:
        export_csv(results, Path(args.export))


if __name__ == "__main__":
    main()
