#!/usr/bin/env python3
"""
generate_variants.py

Reads the baseline CLAUDE.md (LF, no BOM) and generates 4 encoding variants:
  - claude_lf.md          : LF line endings, no BOM  (baseline)
  - claude_crlf.md        : CRLF line endings, no BOM
  - claude_lf_bom.md      : LF line endings, UTF-8 BOM
  - claude_crlf_bom.md    : CRLF line endings, UTF-8 BOM

Usage:
    python scripts/generate_variants.py
"""

from pathlib import Path

ROOT = Path(__file__).parent.parent
TEMPLATE = ROOT / "CLAUDE.md"
VARIANTS_DIR = ROOT / "variants"

UTF8_BOM = b"\xef\xbb\xbf"


def read_normalized(path: Path) -> bytes:
    """Read file and normalize to LF line endings (strip any existing CR)."""
    raw = path.read_bytes()
    # Remove BOM if present
    if raw.startswith(UTF8_BOM):
        raw = raw[len(UTF8_BOM):]
    # Normalize to LF
    normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return normalized


def write_variant(content: bytes, name: str) -> None:
    path = VARIANTS_DIR / name
    path.write_bytes(content)
    lines = content.count(b"\n")
    has_bom = content.startswith(UTF8_BOM)
    has_crlf = b"\r\n" in content
    print(
        f"  {name:<25}  {len(content):>6} bytes  "
        f"{lines:>3} lines  "
        f"BOM={'yes' if has_bom else 'no ':3}  "
        f"endings={'CRLF' if has_crlf else 'LF  '}"
    )


def main() -> None:
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"Template not found: {TEMPLATE}")

    VARIANTS_DIR.mkdir(exist_ok=True)

    lf = read_normalized(TEMPLATE)
    crlf = lf.replace(b"\n", b"\r\n")

    print(f"Source: {TEMPLATE}  ({len(lf)} bytes normalized)")
    print(f"Output: {VARIANTS_DIR}/\n")
    print(f"  {'Filename':<25}  {'Bytes':>6}  Lines  BOM    Endings")
    print(f"  {'-'*25}  {'-'*6}  {'-'*5}  {'-'*3}    {'-'*7}")

    write_variant(lf,               "claude_lf.md")
    write_variant(crlf,             "claude_crlf.md")
    write_variant(UTF8_BOM + lf,    "claude_lf_bom.md")
    write_variant(UTF8_BOM + crlf,  "claude_crlf_bom.md")

    print(f"\nDone. Run the test with:")
    print(f"  bash scripts/run_test.sh lf")
    print(f"  bash scripts/run_test.sh crlf")
    print(f"  bash scripts/run_test.sh lf_bom")
    print(f"  bash scripts/run_test.sh crlf_bom")


if __name__ == "__main__":
    main()
