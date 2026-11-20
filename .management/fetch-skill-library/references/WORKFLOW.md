# Project fetch workflow

## Discover and recommend

Resolve the user's intended project root. In a monorepo, an explicitly named package or subproject takes precedence over the repository root. Read root and category `INDEX.md` pages, then inspect candidate `SKILL.md` descriptions. If index navigation yields nothing, search all catalog entries and skill descriptions so a misplaced category does not hide a skill. Recommend only skills that materially help the request; include catalog ID, reason, compatibility, source, and review status.

## Copy safely

For each approved candidate, verify the catalog path stays inside the shared library and the destination stays inside the intended project. Use `.agents/skills/<skill-name>/` for Codex and `.claude/skills/<skill-name>/` for Claude Code, subject to the installed agent's configuration. Preserve every file under the skill folder. Do not follow symlinks out of either root. A same-name destination with identical content is already installed; with different content, stop and ask how to resolve it. Do not silently overwrite or delete it.

Record installs in `.skill-library/INSTALLED.md` with a table of skill name, catalog ID, source, and date or revision. Keep this manifest out of native skill discovery directories. On a second fetch, add only missing selections. A project copy is independent of future central library changes.

## Trust

`Unreviewed` means the skill has not been approved for project installation. Inspect its instructions and supporting files for risky actions, secrets, license restrictions, and tool requirements. If the user approves it after review, update `CATALOG.md` to `Reviewed` and record who reviewed it and when in a note below the table. Never infer trust from a GitHub URL, popularity, or a plausible description.
