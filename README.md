# Claude Usage — SwiftBar Plugin

A macOS menu bar plugin that shows your Claude Code session and weekly usage at a glance.

Works with [SwiftBar](https://github.com/swiftbar/SwiftBar) and [xbar](https://xbarapp.com/).

## What You Get

**Menu bar:** Dynamic icons showing session + weekly usage with pacing

```
☕50% 👌32%        ← Normal usage
🔥78% 🐇65%       ← Session getting hot, weekly ahead of pace
💀97% 🏎️88%      ← Session almost gone, weekly way ahead
⏳ ◽42% ◽30%     ← Showing cached data (API unreachable)
```

**Dropdown:** Detailed breakdown with progress bars, time until reset, and pacing vs target

```
Claude Usage
---
Session (5h): 42%
  ██████████░░░░░░░░░░
  Resets in 3h 12m
---
Weekly — All Models: 31%
  ██████░░░░░░░░░░░░░░
  Resets in 4d 8h
  🟢 -2% vs pace (target 33% now)
Weekly — Opus: 45%
  █████████░░░░░░░░░░░
  Resets in 4d 8h
Weekly — Sonnet: 12%
  ██░░░░░░░░░░░░░░░░░░
  Resets in 4d 8h
---
Extra Credits: €2.50 / €10 (25%)
  █████░░░░░░░░░░░░░░░
```

## Install

1. Install [SwiftBar](https://github.com/swiftbar/SwiftBar) (or xbar)
2. Download `claude-usage.5m.py` to your SwiftBar plugin folder
3. Make it executable: `chmod +x claude-usage.5m.py`
4. Make sure Claude Code is installed and signed in (the plugin reads credentials from macOS Keychain)

That's it. The plugin refreshes every 5 minutes.

## Configuration

**Currency:** Edit the `CURRENCY` constant at the top of the script (default: `€`).

**Refresh interval:** Rename the file — the number before `.py` controls it. `claude-usage.1m.py` for every minute, `claude-usage.15m.py` for every 15 minutes.

## Pacing

The weekly pacing feature helps you use your full allocation without burning through it too fast. It targets 95% usage at 13 hours before your weekly reset (leaving a small buffer).

The pacing icons tell you at a glance:
- 🧘 Way under pace — lots of headroom
- 🐢 Slightly under — comfortable
- 👌 On track
- 🐇 Slightly ahead — ease up a bit
- 🏎️ Way ahead of pace — slow down or you'll hit the limit early

## Local Extensions

You can add custom items to the dropdown without modifying the plugin. Create a `.claude_usage_local.py` file next to the plugin (dot-prefixed so SwiftBar won't try to execute it as a separate plugin):

```python
def extend(data, stale):
    """Called after all standard items, before the footer links."""
    print("---")
    print("My Custom Item | color=purple")
```

The function receives the raw API data and a staleness flag. See `.claude-usage-local.example.py` for a full example.

The file is gitignored in this repo — perfect for private additions.

## Troubleshooting

**Phantom `?` in the menu bar:** SwiftBar tries to execute every file in the plugin folder. If you see an extra `?` icon, check for a `__pycache__/` directory — Python creates it when the extension is loaded, and stale `.pyc` files inside can get picked up by SwiftBar. Delete it: `rm -rf __pycache__/` and restart SwiftBar.

## Requirements

- macOS (uses Keychain for credentials)
- Python 3 (stdlib only, no pip dependencies)
- [Claude Code](https://claude.ai/download) installed and signed in
- [SwiftBar](https://github.com/swiftbar/SwiftBar) or [xbar](https://xbarapp.com/)

## License

MIT
