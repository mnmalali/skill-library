# Skill Library

**A shared folder for Agent Skills, organized and fetched by your AI agent.**

Skill Library keeps one collection of skill folders on your computer. Each skill is a normal `SKILL.md` file with any references, assets, or scripts that belong to it. Two small management skills tell Codex or Claude Code how to organize the collection and copy only relevant skills into a project. There is no Python package, database, server, account, or background process.

```text
~/Skill-Library/
├── INDEX.md                         # Browse top-level categories
├── CATALOG.md                       # Provenance and review status
├── Development/
│   ├── INDEX.md
│   └── accessibility-audit/
│       └── SKILL.md
└── .management/                     # Source copies of the two management skills
    ├── setup-skill-library/SKILL.md
    └── fetch-skill-library/SKILL.md
```

This repository is an **empty library starter**. The `Development` category above illustrates what it can become; no collected third-party skills ship with the starter.

## How it works

1. Keep this repository at `~/Skill-Library`, or choose another location and tell your agent where it is.
2. Install the two folders in `.management/` into your agent's personal skill directory. These are the only skills installed globally.
3. Ask the agent to add skills to the library or fetch selected skills for a project.

The collection stays in one place. A fetched skill is a **copy** inside that project, so the project keeps working if the central library changes. Codex project copies go to `.agents/skills/`; Claude Code project copies go to `.claude/skills/`. The collection itself is outside those project discovery paths. See [agent setup](docs/AGENT_SETUP.md) for installation paths and examples.

## Quick start

Clone the starter into your home directory:

```sh
git clone https://github.com/mnmalali/skill-library.git ~/Skill-Library
```

Then copy the management skills to the personal skill directory used by your agent. For example, on this Codex desktop setup in PowerShell:

```powershell
New-Item -ItemType Directory -Force "$HOME/.codex/skills" | Out-Null
Copy-Item -Recurse "$HOME/Skill-Library/.management/setup-skill-library" "$HOME/.codex/skills/"
Copy-Item -Recurse "$HOME/Skill-Library/.management/fetch-skill-library" "$HOME/.codex/skills/"
```

For Claude Code, use `$HOME/.claude/skills/` as the destination. [Agent setup](docs/AGENT_SETUP.md) also covers Codex installations that use `~/.agents/skills/`, custom library paths, and existing skill folders. Start a new agent session after installation.

Try these requests:

> Set up my Skill Library at `~/Skill-Library`.
>
> Add this local skill folder to my library and file it under Accessibility.
>
> Recommend skills from my library for this React project.
>
> Fetch `accessibility-audit` into this project for Codex.

## Library format

- Every collected skill remains a complete folder with its original `SKILL.md` and supporting files.
- `INDEX.md` at the root and in each category lists **direct children only**, with short descriptions and relative links.
- `CATALOG.md` records an ID, location, source, license, and review status for each collected skill. The skill files remain the source of truth.
- Categories are created as needed. The agent can suggest a category; your preferred organization wins.
- Same-name skills with different contents stay separate. An exact duplicate can be skipped after the agent verifies the complete bundle.

The format follows the [Agent Skills specification](https://agentskills.io/specification). See [library conventions](docs/CONVENTIONS.md) for the folder and catalog rules.

## Safety and limits

An imported skill can contain instructions or scripts from someone else. The management skills direct the agent to inspect sources as **untrusted data**, avoid executing imported content during import or search, and request review before an untrusted skill is installed into a project. Agent instructions are guidance, not a security sandbox or an atomic transaction system. Keep this library under version control and review changes before sharing third-party skills. See [security guidance](SECURITY.md).

## Repository status

Version **0.2.0** replaces the earlier Python CLI prerelease with the Markdown-first design. The earlier `0.1.0` release is retained for history and should not be used for this workflow. See the [changelog](CHANGELOG.md).

Contributions are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md). This repository's original content is MIT licensed. Imported third-party skills keep their own licenses.
