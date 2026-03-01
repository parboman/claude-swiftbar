# claude-swiftbar

SwiftBar/xbar plugin that shows Claude Code usage in the macOS menu bar.

## Files

- `claude-usage.5m.py` — the plugin (refreshes every 5 minutes)
- `claude_usage_local.py` — local extensions (gitignored, optional)
- `.claude-usage-local.example.py` — extension template

## How It Works

1. Reads OAuth token from macOS Keychain (`Claude Code-credentials`)
2. Calls the Anthropic usage API
3. Displays session (5h) and weekly usage with color-coded icons
4. Falls back to cached data (greyed out) when API is unreachable

## Key Design Decisions

- **stdlib only** — no pip dependencies, just Python 3
- **Extension hook** — `claude_usage_local.py` is imported at the end if present, letting users add private menu items without forking
- **Cache** — stored at `~/.cache/claude-usage.json`, used as fallback when API fails
- **CURRENCY constant** — defaults to `€`, change for your locale

## Conventions

- SwiftBar output format: first line = menu bar, `---` = separator, then dropdown
- Colors: green < 50%, yellow 50-69%, orange 70-89%, red 90%+
- Icons change at session thresholds: 🧊 < 10%, 🌱 10%, ⚡ 25%, ☕ 50%, 🔥 75%, 🧨 90%, 💀 95%
- Weekly pacing icons: 🧘 (way under) → 🐢 → 👌 → 🐇 → 🏎️ (way over)

## Pacing

The pacing calculation targets 95% usage at 13 hours before weekly reset. The reset time comes from the API's `resets_at` field — it varies per account. The plugin calculates expected usage for the current point in the cycle and shows how far ahead or behind you are.
