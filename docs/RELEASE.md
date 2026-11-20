# 0.1.0 prerelease checklist

Completed: local unit and security regression tests, wheel and source distribution build, documented CLI usage, release notes, cross-platform CI configuration, basic integrity checks.

Pending before a stable release: independent security review, real Codex and Claude discovery smoke tests on each supported platform, interruption and crash recovery tests, reproducible build verification, and full bundle import benchmarks. Do not label this version production ready.

To build artifacts: `python -m build`. To run tests: `python -m unittest discover -s tests -v`. Release assets are the wheel and source tarball, with SHA-256 hashes in the GitHub release notes.
