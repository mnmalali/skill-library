# Fetch workflow

Run `skill-library search QUERY` or `skill-library fetch --agent codex --project PATH --description "PROJECT DESCRIPTION"` to get candidates. Ask the user which recommended IDs to install. For an explicit ID or unique name, run `skill-library fetch --agent codex --project PATH --skills NAME`. Use `--agent claude` for Claude Code. The CLI blocks untrusted bundles and changed copies. `--auto` only picks trusted candidates; it does not bypass the trust gate. The project manifest is stored in `.skill-library/` outside the installed bundles.
