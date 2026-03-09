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

**Status line (bottom of each Claude Code window):**
```
🟢 35% | S:42% W:31% | Opus ? ✨
```
- **Context %** — How full this session's context window is (🟢🟡🟠🔴)
- **S:42%** — Current 5-hour quota (from API, colored: green safe → red critical)
- **W:31%** — Weekly quota (colored the same way)
- **Opus** — Which model you're using (in pink)
- **?** — Session age (shows as `42m` or `3h` once calculated)
- **✨** — Cosmic rays! Random sparkles appear 15% of the time (pure vibes)
- **📝** — Unsaved work indicator (appears if git detects changes)

**In the menu bar:** Context warnings light up when sessions get large
```
☕50% 👌32%           ← No warnings (all sessions <70%)
☕50% 👌32% 🟡72%    ← One session at 72% (idle, 2h old)
☕50% 👌32% 🟡72% 🟠85%  ← Two sessions need attention
```

**In the dropdown:** Full session list with activity status
```
Context Windows
  🟢 35% (70k/200k) Opus [active]
     ~/ai/tools/utilities
  🟡 75% (150k/200k) Sonnet [idle] • 3h ago
     ~/ai/projects/parpod
  🟠 88% (176k/200k) Haiku [idle] ⚠️ SAVE! • 12h ago
     ~/ai/tools/live
```

### Setup (Claude Code)

The setup is two steps: create the status line hook + enable it in Claude Code settings.

**1. Create the status line script**

Open Claude Code and run this from your terminal:

```bash
cat > ~/.claude/statusline.sh << 'STATUSLINE_EOF'
#!/bin/bash
# Claude Code enhanced status line with context, quotas, model, and cosmic rays
python3 -c '
import json, time, subprocess, random, sys
from pathlib import Path
try:
    input_data = json.load(sys.stdin)
except:
    input_data = {}
ctx_pct = float(input_data.get("context_window", {}).get("used_percentage", 0))
used = int(input_data.get("context_window", {}).get("used_tokens", 0))
limit = int(input_data.get("context_window", {}).get("limit_tokens", 0))
session = input_data.get("session_id", "unknown")
model_raw = input_data.get("model", "?")
cwd = input_data.get("cwd", "?")
if "opus" in model_raw.lower():
    model = "Opus"
elif "sonnet" in model_raw.lower():
    model = "Sonnet"
elif "haiku" in model_raw.lower():
    model = "Haiku"
else:
    model = model_raw.split("-")[0][:6]
session_pct, weekly_pct = "?", "?"
try:
    cache_path = Path.home() / ".cache" / "claude-usage.json"
    if cache_path.exists():
        cache_data = json.loads(cache_path.read_text())
        api_data = cache_data.get("data", {})
        session_pct = int(api_data.get("five_hour", {}).get("utilization", 0))
        weekly_pct = int(api_data.get("seven_day", {}).get("utilization", 0))
except:
    pass
session_age = "?"
try:
    project_dir = Path.home() / ".claude" / "projects"
    for proj_dir in project_dir.glob("*"):
        session_file = proj_dir / f"{session}.jsonl"
        if session_file.exists():
            age_secs = int(time.time() - session_file.stat().st_mtime)
            session_age = f"{age_secs // 60}m" if age_secs < 3600 else f"{age_secs // 3600}h"
            break
except:
    pass
unsaved = ""
try:
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, timeout=2, cwd=cwd)
    if result.returncode == 0 and result.stdout.strip():
        unsaved = " 📝"
except:
    pass
ctx_int = int(ctx_pct) if ctx_pct != "?" else 0
ctx_icon = "🔴" if ctx_int >= 90 else "🟠" if ctx_int >= 80 else "🟡" if ctx_int >= 70 else "🟢"
def quota_color(pct):
    p = pct if isinstance(pct, int) else 0
    if p >= 90: return "\033[91m"
    elif p >= 70: return "\033[35m"
    elif p >= 50: return "\033[33m"
    else: return "\033[92m"
s_color, w_color = quota_color(session_pct), quota_color(weekly_pct)
s_display = f"{session_pct}%" if session_pct != "?" else "?"
w_display = f"{weekly_pct}%" if weekly_pct != "?" else "?"
cosmic = " ✨" if random.random() < 0.15 else ""
status = f"{ctx_icon} {int(ctx_pct)}% | {s_color}S:{s_display}\033[0m {w_color}W:{w_display}\033[0m | \033[95m{model}\033[0m{unsaved} {session_age}{cosmic}"
print(status)
tmpdir = Path("/tmp/claude-context")
tmpdir.mkdir(exist_ok=True)
(tmpdir / f"{session}.json").write_text(json.dumps({"session_id": session, "pct": float(ctx_pct), "used_tokens": used, "limit_tokens": limit, "model": model_raw, "cwd": cwd, "ts": time.time()}))
'
STATUSLINE_EOF
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

**Status line** — Reports three things every update:
- **Context window %** — Local context usage (just this session)
- **Session/Weekly quotas** (S:X% / W:X%) — Your API usage quota from the claude-usage cache
- **Model, session age, unsaved work, cosmic rays** — Everything else

**SwiftBar integration** — Reads the cache + temp files to show:
- Current context in menu bar
- Full session breakdown in dropdown
- Context warnings (🟡🟠🔴) for sessions at 70%+

**Color coding (context window):**
- 🟢 0–69% — Safe
- 🟡 70–79% — Getting full, shows in menu bar
- 🟠 80–89% — Nearly full, shows in menu bar
- 🔴 90%+ — Critical

**Color coding (quotas S:% / W:%):**
- 🟢 Green — 0–49% (plenty left)
- 🟡 Yellow — 50–69% (comfortable)
- 🟠🔵 Magenta/Pink — 70–89% (getting full)
- 🔴 Red — 90%+ (nearly out)

**Session indicators:**
- `[active]` — updated in last hour (normal colors)
- `[idle]` — last seen 1–24h ago (grayed out with timestamp)
- 📝 — Git has uncommitted changes (you've got work to save)
- ✨ — Cosmic rays (random sparkles, 15% chance per update, purely decorative)

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
