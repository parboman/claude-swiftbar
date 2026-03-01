"""
Example local extension for claude-usage.5m.py

This file shows how to add custom items to the Claude Usage dropdown menu.
To use it:
  1. Copy this file to `claude_usage_local.py` (same directory as the plugin)
  2. Edit the extend() function to add your own items
  3. SwiftBar will pick it up on next refresh

The extend() function receives:
  - data: dict — raw API response from the usage endpoint
  - stale: bool — True if showing cached data (API was unreachable)

Print SwiftBar-formatted lines to add items to the dropdown.
Items appear after the usage buckets and before the "Open Usage Page" link.
"""


def extend(data, stale):
    """Add custom items to the Claude Usage dropdown."""
    # Example: show a separator and custom link
    print("---")
    print("My Custom Section | size=14")
    print("--Custom item 1 | color=purple")
    print("--Custom item 2 | href=https://example.com")

    # Example: conditional items based on usage
    weekly = data.get("seven_day", {})
    util = int(weekly.get("utilization", 0))
    if util > 80:
        print("--⚠️ Weekly usage high! | color=orange")
