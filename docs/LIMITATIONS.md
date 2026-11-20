# Prerelease limitations

- Independent security review and native Codex/Claude invocation tests have not been completed. This is not a production readiness claim.
- A trust mark records a human review of one exact content hash. The CLI cannot determine whether instructions or scripts are safe.
- GitHub imports support public repositories and simple branch/subdirectory URLs. Private repositories, tags with ambiguous paths, Git submodules, and Git sync conflict resolution are not supported.
- Indexes are deterministic navigation over managed records. Editing category indexes by hand will be replaced on rebuild.
- Import rollback is best effort across a sudden power loss. A move journal remains for manual recovery if interrupted.
- `--auto` uses keyword matching, not semantic or agent-assisted ranking.
- Manual agent skill discovery and context footprint still require real integration benchmarking.
