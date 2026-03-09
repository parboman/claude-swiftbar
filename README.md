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

## Context Window Monitoring (Optional)

Monitor Claude Code's context window usage in real-time — see which sessions are active, how full they are, and get a warning when you're about to run out of space.

### What You'll See

**In the menu bar:** Context warnings light up when sessions get large
```
☕50% 👌32%           ← No warnings (all sessions <70%)
☕50% 👌32% 🟡72%    ← One session at 72% (idle, 2h old)
☕50% 👌32% 🟡72% 🟠85%  ← Two sessions need attention
```

**In the dropdown:** Full session list with activity status
```
Context Windows
  🟢 42% (85k/200k) Opus [active]
     ~/ai/tools/utilities
  🟡 75% (150k/200k) Sonnet [idle] • 3h ago
     ~/ai/projects/parpod
  🟠 88% (176k/200k) Haiku [idle] ⚠️ SAVE! • 12h ago
     ~/ai/tools/live
```

### Setup (Claude Code)

The setup is two steps: create the status line hook + enable it in Claude Code settings.

**1. Create the status line script**

Open Claude Code and run this from your terminal (or paste into any Claude Code chat):

```bash
cat > ~/.claude/statusline.sh << 'EOF'
#!/bin/bash
INPUT=$(cat)
PCT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('context_window',{}).get('used_percentage','?'))" 2>/dev/null)
USED=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('context_window',{}).get('used_tokens',0))" 2>/dev/null)
LIMIT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('context_window',{}).get('limit_tokens',0))" 2>/dev/null)
SESSION=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id','unknown'))" 2>/dev/null)
MODEL=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('model','?'))" 2>/dev/null)
CWD=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('cwd','?'))" 2>/dev/null)
USED_K=$((USED / 1000))
LIMIT_K=$((LIMIT / 1000))
PCT_INT=$(printf "%.0f" "$PCT" 2>/dev/null || echo "?")
if [ "$PCT_INT" != "?" ]; then
    if [ "$PCT_INT" -ge 90 ]; then ICON="🔴"
    elif [ "$PCT_INT" -ge 80 ]; then ICON="🟠"
    elif [ "$PCT_INT" -ge 70 ]; then ICON="🟡"
    else ICON="🟢"; fi
else ICON="⚪"; fi
TMPDIR="/tmp/claude-context"
mkdir -p "$TMPDIR"
python3 -c "
import json, time
data = {'session_id': '$SESSION', 'pct': $PCT, 'used_tokens': $USED, 'limit_tokens': $LIMIT, 'model': '$MODEL', 'cwd': '$CWD', 'ts': time.time()}
with open('$TMPDIR/$SESSION.json', 'w') as f: json.dump(data, f)
" 2>/dev/null
echo "$ICON ${PCT_INT}% (${USED_K}k/${LIMIT_K}k)"
EOF
chmod +x ~/.claude/statusline.sh
```

**2. Register the hook in Claude Code settings**

In Claude Code, open **Settings** → find or create `~/.claude/settings.json`, then add this block (if `statusLine` already exists, replace it):

```json
"statusLine": {
  "type": "command",
  "command": "~/.claude/statusline.sh"
}
```

**That's it!** New Claude Code sessions will show a colored dot + context % in the terminal status line. SwiftBar will automatically pick up the context data on its next refresh (every 5 minutes).

### How It Works

- **Status line** — Each session reports its context percentage to a small temp file (`/tmp/claude-context/`)
- **SwiftBar plugin** — Reads those files and displays the data in your menu bar + dropdown
- **Color coding:**
  - 🟢 0–69% — Safe, no warning
  - 🟡 70–79% — Getting full, visible in menu bar
  - 🟠 80–84% — Nearly full, visible in menu bar
  - 🔴 90%+ — Critical, **save your work**
  - ⚠️ 85%+ — **SAVE!** warning appears (you need ~10–15k tokens to save files)

- **Active vs idle:**
  - `[active]` — session updated in the last hour (colored text)
  - `[idle]` — session last seen 1–24 hours ago (grayed out, shows "3h ago")

### Monitoring Multiple Sessions

The setup works great if you run multiple Claude Code windows at once — each one reports its usage independently. The dropdown shows all sessions from the last 24 hours, so you can see the full picture of your long-running work.

## Troubleshooting

**Phantom `?` in the menu bar:** SwiftBar tries to execute every file in the plugin folder. If you see an extra `?` icon, check for a `__pycache__/` directory — Python creates it when the extension is loaded, and stale `.pyc` files inside can get picked up by SwiftBar. Delete it: `rm -rf __pycache__/` and restart SwiftBar.

## Requirements

- macOS (uses Keychain for credentials)
- Python 3 (stdlib only, no pip dependencies)
- [Claude Code](https://claude.ai/download) installed and signed in
- [SwiftBar](https://github.com/swiftbar/SwiftBar) or [xbar](https://xbarapp.com/)

## License

MIT
