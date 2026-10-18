#!/bin/sh
# Claude Code PreToolUse hook: refuse real mouse, keyboard and window-focus input unless JStar has
# created ~/.supcom-input-ok (AGENTS.md). Covers shell commands and the computer-use tools.
[ -e "$HOME/.supcom-input-ok" ] && exit 0
input=$(cat)
tool=$(printf '%s' "$input" | jq -r '.tool_name // ""')
case "$tool" in
    mcp__computer-use__*) ;;
    Bash) printf '%s' "$input" | jq -r '.tool_input.command // ""' \
        | grep -Eq 'osascript|cliclick|game-window[^|;&]* (click|drag|scroll|key|type|wait)|game-window/input' || exit 0 ;;
    *) exit 0 ;;
esac
printf '%s\n' 'Blocked: real mouse/keyboard input is off (JStar enables it with: touch ~/.supcom-input-ok). Use scripted, hidden validation.' >&2
exit 2
