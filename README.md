# Skill Library

Skill Library is a local, shared collection of Agent Skills. It imports full skill folders into one library, maintains category indexes, and copies selected, reviewed skills into one project at a time. It does not run imported scripts.

This is a **0.1 prerelease**. See [limitations](docs/LIMITATIONS.md) before using it with third-party skills.

## Install

Requires Python 3.11 or newer.

```sh
python -m pip install .
skill-library init
skill-library bootstrap --agents codex claude
```

`bootstrap` installs only the two management skills into each agent's user skill directory and writes a pointer to the same library root. It does not install collected skills globally. Omit an agent if you do not use it. Use `--root PATH` before the command to choose another library.

## Import and review

```sh
skill-library add ./my-skill --category Development --dry-run
skill-library add ./my-skill --category Development
skill-library list
skill-library trust RECORD_ID
skill-library index --check
```

`add` accepts a skill directory, a folder containing several skills, a ZIP or TAR archive, or a public `https://github.com/OWNER/REPO` URL. A GitHub URL can include `/tree/BRANCH/SUBDIRECTORY` for branches without slashes. Imports preserve all files in each bundle byte for byte. They are marked untrusted until a human reviews and trusts a specific content hash. Exact duplicate bundles are skipped. Distinct bundles sharing a name are kept separately.

## Fetch to a project

```sh
skill-library fetch --agent codex --project ./my-project --description "React storefront"
skill-library fetch --agent codex --project ./my-project --skills react-patterns
skill-library fetch --agent claude --project ./my-project --skills RECORD_ID
```

A description returns recommendations for approval; it does not install them. An exact, unique, trusted name or ID installs directly. `--auto` selects up to three trusted recommendations. Codex project copies go under `.agents/skills/`; Claude copies go under `.claude/skills/`. Each project receives only its selected bundles. Existing different content is never overwritten.

## Maintenance

```sh
skill-library search accessibility
skill-library doctor
skill-library reorganize RECORD_ID --category Quality/Accessibility --dry-run
skill-library reorganize RECORD_ID --category Quality/Accessibility
skill-library sync-status
skill-library --json list
```

The root defaults to `~/Skill-Library`. `SKILL_LIBRARY_ROOT` or `--root` overrides it. The CLI returns exit code 2 for validation or integrity failures. `--json` is a global option before the command.

## Development

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python -m build
```

The project has no server or account dependency. Git sync is manual so local edits cannot be reset automatically. Read [security](SECURITY.md), [contributing](CONTRIBUTING.md), and [discovery notes](docs/DISCOVERY.md).
