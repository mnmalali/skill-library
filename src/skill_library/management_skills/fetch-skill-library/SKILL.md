---
name: fetch-skill-library
description: Search a shared Skill Library and fetch relevant skills into the current project only. Use when the user describes a project and requests recommended skills, or names exact skills to install locally for Codex or Claude Code.
---

# Fetch Skill Library

Use the `skill-library` CLI. Resolve the shared library and the current project root. If the user describes a project, run `fetch --description`, explain the focused recommendations, and obtain selection before installing. If they give an explicit unique trusted name or ID, install directly with `fetch --skills`. `--auto` only selects trusted candidates. Use the appropriate `--agent` value. Fetch copies full bundles into this project's agent skill directory and preserves existing skills. Read `references/WORKFLOW.md` for command examples.
