# Setup workflow

Run `skill-library init` once. Use `skill-library add SOURCE --dry-run` to inspect the planned imports, then `skill-library add SOURCE --category CATEGORY` to import. Imported bundles remain untrusted. Review `SKILL.md`, scripts, references, provenance, and license before `skill-library trust ID`. Use `skill-library doctor` to inspect integrity and `skill-library index --check` to verify navigation. For moves, run `skill-library reorganize ID --category CATEGORY --dry-run` first, then apply the same command without `--dry-run`.
