#!/bin/sh
# Claude Code PreToolUse hook: enforce the repository git command rules.
exec python3 -I -c '
import json
import os
import re
import shlex
import subprocess
import sys

payload = json.load(sys.stdin)
command = payload.get("tool_input", {}).get("command", "")
pattern = r"git[^|;&]*(--no-verify|commit[^|;&]* -[a-zA-Z]*n[a-zA-Z]*( |$)|add[^|;&]* (-[a-zA-Z]*[fA][a-zA-Z]*|--force|--all|\.)([\s]|$)|pull[^|;&]* --rebase([=\s]|$)|-c core\.hooksPath)"
def refuse():
    print("Blocked: this git command violates mac/agents/hooks/block-git-bypass.sh.", file=sys.stderr)
    sys.exit(2)
if re.search(pattern, command):
    refuse()
if "rebase" not in command:
    sys.exit(0)
try:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    tokens = list(lexer)
except ValueError:
    refuse()
cwd = payload.get("cwd") or os.getcwd()
for index, token in enumerate(tokens):
    if token == "cd" and index + 1 < len(tokens):
        cwd = os.path.abspath(os.path.join(cwd, tokens[index + 1]))
    if token != "git":
        continue
    args = []
    for arg in tokens[index + 1:]:
        if arg and all(c in ";&|\n" for c in arg):
            break
        args.append(arg)
    repo = cwd
    while args and args[0].startswith("-"):
        option = args.pop(0)
        if option in ("-C", "-c") and args:
            value = args.pop(0)
            if option == "-C":
                repo = os.path.abspath(os.path.join(repo, value))
        elif option.startswith("-C"):
            repo = os.path.abspath(os.path.join(repo, option[2:]))
    if not args or args[0] != "rebase":
        continue
    branch = subprocess.run(["git", "-C", repo, "branch", "--show-current"],
                            capture_output=True, text=True).stdout.strip()
    if "main" in args[1:] or branch == "main":
        refuse()
'
