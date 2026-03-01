#!/usr/bin/env python3
# <xbar.title>Claude Usage Monitor</xbar.title>
# <xbar.version>v2.0</xbar.version>
# <xbar.author>Pär Boman</xbar.author>
# <xbar.desc>Shows Claude AI session and weekly usage in the menu bar</xbar.desc>
# <swiftbar.refreshOnOpen>true</swiftbar.refreshOnOpen>

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

CACHE_PATH = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "claude-usage.json"
CURRENCY = "€"  # Change to "$", "£", etc. for your locale

# --- Helpers ---


def fail(title, message):
    print(title)
    print("---")
    print(f"❌ {message} | color=red")
    sys.exit(0)


def get_token():
    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-s",
                "Claude Code-credentials",
                "-w",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None
        creds = json.loads(result.stdout.strip())
        return creds["claudeAiOauth"]["accessToken"]
    except Exception:
        return None


def save_cache(data):
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps({"data": data, "ts": datetime.now(timezone.utc).isoformat()}))
    except Exception:
        pass


def load_cache():
    try:
        cache = json.loads(CACHE_PATH.read_text())
        return cache["data"], cache["ts"]
    except Exception:
        return None, None


def fetch_usage(token):
    req = Request(
        "https://api.anthropic.com/api/oauth/usage",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "anthropic-beta": "oauth-2025-04-20",
            "User-Agent": "claude-code/2.0.32",
        },
    )
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            save_cache(data)
            return data, False, None
    except Exception:
        data, ts = load_cache()
        if data:
            return data, True, ts  # stale
        return None, False, None


def pct(bucket):
    if bucket is None:
        return None
    return int(bucket.get("utilization", 0))


def time_left(bucket):
    if bucket is None or bucket.get("resets_at") is None:
        return None
    try:
        reset = datetime.fromisoformat(bucket["resets_at"].replace("Z", "+00:00"))
        diff = reset - datetime.now(timezone.utc)
        total_sec = int(diff.total_seconds())
        if total_sec <= 0:
            ago = -total_sec
            h, remainder = divmod(ago, 3600)
            m = remainder // 60
            if h > 24:
                return f"reset {h // 24}d {h % 24}h ago"
            elif h > 0:
                return f"reset {h}h {m}m ago"
            elif m > 0:
                return f"reset {m}m ago"
            return "just reset"
        h, remainder = divmod(total_sec, 3600)
        m = remainder // 60
        if h > 24:
            return f"{h // 24}d {h % 24}h"
        elif h > 0:
            return f"{h}h {m}m"
        else:
            return f"{m}m"
    except Exception:
        return "?"


def bar(percent, width=20):
    filled = int(width * percent / 100)
    return "\u2588" * filled + "\u2591" * (width - filled)


def color_for(percent):
    if percent >= 90:
        return "red"
    elif percent >= 70:
        return "orange"
    elif percent >= 50:
        return "yellow"
    return "green"


def pacing(bucket):
    """Calculate pacing vs goal of 95% at 13h before weekly reset."""
    p = pct(bucket)
    if p is None or bucket is None or bucket.get("resets_at") is None:
        return None
    try:
        reset = datetime.fromisoformat(bucket["resets_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        secs_left = (reset - now).total_seconds()
        if secs_left <= 0:
            return None
        total_secs = 7 * 24 * 3600  # 168h
        elapsed_secs = total_secs - secs_left
        # Goal: 95% at 155h mark (13h before reset)
        target_secs = total_secs - 13 * 3600  # 155h
        if elapsed_secs >= target_secs:
            target_pct = 95.0
        else:
            target_pct = 95.0 * elapsed_secs / target_secs
        diff = p - target_pct
        return diff, target_pct
    except Exception:
        return None


def section(label, bucket, show_pacing=False):
    p = pct(bucket)
    if p is None:
        print(f"{label}: No data | color=gray")
        return
    c = color_for(p)
    t = time_left(bucket)
    print(f"{label}: {p}% | color={c}")
    print(f"  {bar(p)} | font=Menlo size=11")
    if t:
        if t.startswith("reset ") or t == "just reset":
            print(f"  ♻️ {t.capitalize()} | color=gray size=11")
        else:
            print(f"  Resets in {t} | color=gray size=11")
    if show_pacing:
        pace = pacing(bucket)
        if pace:
            diff, target = pace
            if diff >= 0:
                emoji = "🔴" if diff > 15 else "🟡" if diff > 5 else "🟢"
                print(f"  {emoji} {diff:+.0f}% vs pace (target {target:.0f}% now) | size=11")
            else:
                emoji = "🟢" if diff > -10 else "🔵"
                print(f"  {emoji} {diff:+.0f}% vs pace (target {target:.0f}% now) | size=11")


# --- Main ---

token = get_token()
if not token:
    fail("\u26a1 ?", "No Claude Code credentials in Keychain")

data, stale, cache_ts = fetch_usage(token)
if not data:
    fail("\u26a1 ?", "API request failed")

session = pct(data.get("five_hour"))
weekly = pct(data.get("seven_day"))

# Menu bar title
parts = []
if stale:
    parts.append("⏳")
if session is not None:
    if stale:
        icon = "◽"
    elif session >= 95:
        icon = "💀"
    elif session >= 90:
        icon = "🧨"
    elif session >= 75:
        icon = "🔥"
    elif session >= 50:
        icon = "☕"
    elif session >= 25:
        icon = "⚡"
    elif session >= 10:
        icon = "🌱"
    else:
        icon = "🧊"
    parts.append(f"{icon}{session}%")
if weekly is not None:
    if stale:
        pace_icon = "◽"
    else:
        pace_icon = "📊"
        pace = pacing(data.get("seven_day"))
        if pace:
            diff, _ = pace
            if diff > 15:
                pace_icon = "🏎️"
            elif diff > 5:
                pace_icon = "🐇"
            elif diff >= 0:
                pace_icon = "👌"
            elif diff > -10:
                pace_icon = "🐢"
            else:
                pace_icon = "🧘"
    parts.append(f"{pace_icon}{weekly}%")

title = " ".join(parts) if parts else "\U0001f525 ok"
if stale:
    print(f"{title} | color=#888888")
else:
    print(title)

# Dropdown
print("---")
if stale:
    cache_age = ""
    if cache_ts:
        try:
            cached = datetime.fromisoformat(cache_ts)
            ago_s = int((datetime.now(timezone.utc) - cached).total_seconds())
            if ago_s > 86400:
                cache_age = f" ({ago_s // 86400}d {(ago_s % 86400) // 3600}h old)"
            elif ago_s > 3600:
                cache_age = f" ({ago_s // 3600}h {(ago_s % 3600) // 60}m old)"
            elif ago_s > 60:
                cache_age = f" ({ago_s // 60}m old)"
            else:
                cache_age = " (just cached)"
        except Exception:
            pass
    print(f"⏳ Cached data{cache_age} — API unreachable | color=orange size=11")
    print("---")
print("Claude Usage | size=14")
print("---")
section("Session (5h)", data.get("five_hour"))
print("---")
section("Weekly \u2014 All Models", data.get("seven_day"), show_pacing=True)
section("Weekly \u2014 Opus", data.get("seven_day_opus"))
section("Weekly \u2014 Sonnet", data.get("seven_day_sonnet"))

# Optional buckets
if data.get("seven_day_oauth_apps"):
    section("Weekly \u2014 OAuth Apps", data.get("seven_day_oauth_apps"))

# Extra usage (paid credits)
extra = data.get("extra_usage")
if extra and extra.get("is_enabled"):
    used = extra.get("used_credits", 0)
    limit = extra.get("monthly_limit", 0)
    ep = int(extra.get("utilization", 0))
    print("---")
    c = color_for(ep)
    print(f"Extra Credits: {CURRENCY}{used / 100:.2f} / {CURRENCY}{limit / 100:.0f} ({ep}%) | color={c}")
    print(f"  {bar(ep)} | font=Menlo size=11")

# Load local extensions — dot-prefixed to hide from SwiftBar
# Place .claude_usage_local.py next to this plugin (see .claude-usage-local.example.py)
try:
    import importlib.util
    _ext_path = Path(__file__).parent / ".claude_usage_local.py"
    if _ext_path.exists():
        _spec = importlib.util.spec_from_file_location("_claude_usage_local", _ext_path)
        _ext = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_ext)
        if hasattr(_ext, "extend"):
            _ext.extend(data=data, stale=stale)
except Exception:
    pass

print("---")
print("Open Usage Page | href=https://claude.ai/settings/usage")
print("Refresh | refresh=true")
