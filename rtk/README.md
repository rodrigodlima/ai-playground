# RTK — Rust Token Killer

[github.com/rtk-ai/rtk](https://github.com/rtk-ai/rtk)

## What it is

CLI proxy written in Rust. Sits between your shell (or Claude Code) and common dev tools (`git`, `gh`, `ls`, `tree`, `find`, `grep`, `jest`, `tsc`, `kubectl`, `docker`, `aws`, ...). Filters and compacts their output **before** it reaches the LLM context, cutting token usage 60–90% on most dev operations without losing technical signal.

Used transparently via a Claude Code hook: `git status` → rewritten to `rtk git status`, 0 tokens of overhead.

## Why

LLM context is the bottleneck. Native tools dump ASCII art, progress bars, repeated paths, blank padding, full file lists, etc. RTK strips noise, groups duplicates, truncates long lists, and produces a denser equivalent. Same information, fewer tokens, lower cost, longer session before compaction.

## Install check

```bash
rtk --version          # rtk X.Y.Z
which rtk              # /opt/homebrew/bin/rtk (or similar)
rtk gain               # must not say "command not found"
```

Name collision warning: `reachingforthejack/rtk` (Rust Type Kit) is a different binary. If `rtk gain` errors, you have the wrong one.

## Validating token savings

Three independent ways to compare RTK vs native output.

### 1. Built-in: `rtk gain`

RTK records every invocation. After running some commands, inspect the running tally:

```bash
rtk gain               # totals + per-command breakdown
rtk gain --history     # recent invocations with bytes saved
rtk gain --graph       # ASCII daily savings graph
rtk gain --project     # restrict to current cwd
rtk gain --format json # machine-readable
```

Reported numbers come from RTK's own input/output byte counters → token estimate (≈4 chars/token).

### 2. Manual A/B with byte counts

Run the same command twice, once raw, once through RTK, pipe both to `wc -c`. Difference in bytes ≈ difference in tokens × 4.

```bash
# Example: git status in a busy repo
git status               | wc -c       # raw bytes
rtk git status           | wc -c       # filtered bytes

# Example: directory listing
ls -la                   | wc -c
rtk ls -la               | wc -c

# Example: tree of a node_modules-heavy repo
tree -L 3                | wc -c
rtk tree -L 3            | wc -c

# Example: grep across repo
grep -rn "TODO" .        | wc -c
rtk grep -rn "TODO" .    | wc -c
```

For a closer token estimate use [tiktoken](https://github.com/openai/tiktoken) or Anthropic's tokenizer:

```bash
# rough estimate (chars/4)
echo "scale=0; $(git status | wc -c)/4"      | bc
echo "scale=0; $(rtk git status | wc -c)/4"  | bc
```

### 3. Retrospective: `rtk discover`

Scans your Claude Code session history and reports commands you ran natively that RTK could have filtered, with estimated savings:

```bash
rtk discover                 # current project, last 30 days
rtk discover --all           # all projects
rtk discover --since 7       # last 7 days
rtk discover --format json
```

Useful to find missed wins and to justify wiring the RTK hook.

### Bonus: economics view

```bash
rtk cc-economics             # ccusage spend vs rtk savings
rtk cc-economics --monthly
```

Combines Claude Code spending (`ccusage`) with RTK savings → net cost/benefit.

## Quick demo (one-liner)

```bash
for cmd in "git status" "ls -la" "tree -L 2"; do
  raw=$(eval "$cmd" 2>/dev/null | wc -c)
  rtk=$(eval "rtk $cmd" 2>/dev/null | wc -c)
  printf "%-15s raw=%6d  rtk=%6d  saved=%5.1f%%\n" \
    "$cmd" "$raw" "$rtk" "$(echo "scale=1; ($raw-$rtk)*100/$raw" | bc)"
done
```

Prints per-command byte counts + savings percentage. Sanity-check before trusting `rtk gain` totals.
