# Agent setup

## One library, two management skills

Clone or copy this repository to `~/Skill-Library`, or choose another shared folder. Do not clone a second library under each agent's home. Install only `.management/setup-skill-library` and `.management/fetch-skill-library` in each agent's personal skill directory. The full collection remains outside agent discovery directories.

For this Codex desktop setup, the personal directory is `~/.codex/skills/`. The [OpenAI installation reference](https://developers.openai.com/api/reference/cli) also documents `~/.agents/skills/` as a user-level directory for Codex; use the path recognized by your installed version. [Claude Code's skill documentation](https://code.claude.com/docs/en/skills) describes `~/.claude/skills/` for personal skills and `.claude/skills/` for project skills. Start a new agent session after copying management skills.

For a custom library location, tell the agent the path in your request. The management skill defaults to `~/Skill-Library` and does not read a hidden configuration file.

If a management skill with the same name is already installed, inspect it before replacing it. If you copied an earlier version of this repository's management skills, replace those two copies with the folders from the current repository.

On macOS or Linux, a fresh Claude Code installation can use:

```sh
mkdir -p "$HOME/.claude/skills"
cp -R "$HOME/Skill-Library/.management/setup-skill-library" "$HOME/.claude/skills/"
cp -R "$HOME/Skill-Library/.management/fetch-skill-library" "$HOME/.claude/skills/"
```

For Codex, substitute the personal skill directory recognized by your installation. These commands assume the destination skill folders do not already exist; inspect and update existing copies deliberately.

## Example requests

- “Set up my Skill Library at `~/Skill-Library`.”
- “Add this skill folder to my library under Research.”
- “Organize my video skills under Media; show the moves first.”
- “Find useful skills in my library for this project.”
- “Fetch `accessibility-audit` into this Codex project.”

The management skills use the agent's normal file and Git tools. They do not require a special CLI, plugin, or daemon. Their instructions guide the agent's work; they do not bypass the agent's permissions or guarantee safe handling of hostile files.
