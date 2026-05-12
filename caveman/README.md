A Claude Code skill/plugin (also Codex, Gemini, Cursor, Windsurf, Cline, Copilot, 30+ more) that makes agent talk like caveman — cuts ~75% of output tokens, keeps full technical accuracy. Brain still big. Mouth small.

Reference: https://github.com/juliusbrussee/caveman

I created a simple prompt: " I need to integrate argocd and crossplane. How can I configure it?"

And the result using the Caveman is:

UserPromptSubmit operation blocked by hook:
  Caveman Stats
  ──────────────────────────────────
  Session:  ...nd/d806150a-2734-40b7-a87b-c478287ad71b.jsonl
  Turns:    11                
  ──────────────────────────────────
  Output tokens:         3.700
  Cache-read tokens:     323.578
  ──────────────────────────────────
  Est. without caveman:  10.571
  Est. tokens saved:     6.871 (~65%)
  Est. saved (USD):      ~$0.515
  Savings est. from benchmarks/ (mean per-task). Pricing for claude-opus-4-7. Actual varies by task.