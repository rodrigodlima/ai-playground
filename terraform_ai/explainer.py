#!/usr/bin/env python3
"""
Terraform Plan Explainer
Analyzes terraform plan output and explains changes in plain language.

Usage:
    terraform plan | python explainer.py
    python explainer.py --file plan.txt
    python explainer.py --file plan.txt --lang en
"""

import argparse
import os
import sys
import anthropic
from dotenv import load_dotenv

SYSTEM_PROMPT = """You are a senior DevOps engineer reviewing a Terraform plan.
Your job is to explain the plan clearly and highlight any risks.

Always respond in the same language as requested by the user.
Always structure your response EXACTLY in this format (use the same section headers):

## Summary
A 2-3 sentence plain-language summary of what this plan will do.

## Changes by Resource
List each affected resource with its operation:
- ✅ CREATE: <resource>
- 🔁 UPDATE: <resource> — <what changes>
- 🔴 DESTROY: <resource>
- ⚠️  REPLACE: <resource> — <reason for replacement>

## Risk Analysis
For each risk found (destruction, replacement, sensitive resources like IAM/network/database/secrets):
- **[HIGH/MEDIUM/LOW]** <resource>: <explanation of the risk>

If no risks found, write: "No significant risks identified."

## Recommendation
One of:
- **SAFE TO APPLY** — brief reason
- **REVIEW BEFORE APPLYING** — what to check
- **DO NOT APPLY** — critical issue found

Be concise. Focus on what matters. If the plan output is empty or has no changes, say so clearly."""

load_dotenv()


def read_plan(filepath: str | None) -> str:
    """Read terraform plan from file or stdin."""
    if filepath:
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        with open(filepath, "r") as f:
            return f.read()

    if sys.stdin.isatty():
        print("❌ No input provided. Use --file or pipe terraform plan output.", file=sys.stderr)
        print("   Example: terraform plan | python explainer.py", file=sys.stderr)
        sys.exit(1)

    return sys.stdin.read()


def explain_plan(plan_output: str, lang: str = "pt") -> None:
    """Send plan to Claude and stream the explanation."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    lang_instruction = "Respond in Portuguese (Brazilian)." if lang == "pt" else "Respond in English."

    user_message = f"""{lang_instruction}

Analyze this Terraform plan output:

```
{plan_output}
```"""

    print("\n🔍 Analyzing Terraform plan...\n")
    print("─" * 60)

    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)

    print("\n" + "─" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Explain a Terraform plan using Claude AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  terraform plan | python explainer.py
  terraform plan -out=plan.tfplan && terraform show -no-color plan.tfplan | python explainer.py
  python explainer.py --file plan.txt
  python explainer.py --file plan.txt --lang en
        """,
    )
    parser.add_argument(
        "--file", "-f",
        metavar="PATH",
        help="Path to a file containing terraform plan output",
    )
    parser.add_argument(
        "--lang", "-l",
        choices=["pt", "en"],
        default="pt",
        help="Output language: pt (Portuguese) or en (English). Default: pt",
    )

    args = parser.parse_args()

    plan_output = read_plan(args.file)

    if not plan_output.strip():
        print("❌ Plan output is empty.", file=sys.stderr)
        sys.exit(1)

    explain_plan(plan_output, lang=args.lang)


if __name__ == "__main__":
    main()