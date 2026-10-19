# mac/agents: guards, hooks and Claude plugins

These files decide what agents may run, so a silent mistake here disables a guard for every session.
- `mac/scripts/setup` installs the hooks into `.git/mac-hooks/`; rerun it after an edit (`check` fails until then).
  Running sessions keep the hooks they started with.
- Every deny or ask pattern gets a refused case and an allowed lookalike in `mac/scripts/check`.
- A hook fails closed: a payload it cannot read is refused.
- After editing a plugin, bump its `plugin.json` version and run `claude plugin update NAME@supcom --scope local`;
  `check` compares the installed copy with the source.
- A command or skill holds judgement and names the script to run; a fixed sequence belongs in a script.
