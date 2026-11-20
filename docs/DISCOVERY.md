# Agent discovery notes

Verified 2026-11-21 against the [Agent Skills specification](https://agentskills.io/specification), [Claude Code skills documentation](https://code.claude.com/docs/en/skills), and [OpenAI skill installation table](https://developers.openai.com/api/reference/cli).

The portable spec requires `SKILL.md` with `name` and `description` frontmatter. It allows supporting files. This CLI validates those required fields and preserves every other file and frontmatter field unchanged.

Current documented project directories are `.agents/skills/` for Codex and `.claude/skills/` for Claude Code. Claude's personal directory is `~/.claude/skills/`. The OpenAI installation table gives `~/.agents/skills/` for Codex, while Codex installations also commonly use `~/.codex/skills/`. This prerelease bootstrap uses `~/.codex/skills/`, matching the handoff and this Codex desktop environment; users should confirm discovery in their installed Codex version. Project paths are adapter constants and can be changed in code. A real agent invocation smoke test remains a release gate.
