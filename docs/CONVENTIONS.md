# Library conventions

The root is one shared folder, normally `~/Skill-Library`. It is a regular filesystem directory, not a Codex or Claude skill discovery directory. The two management skills in `.management/` are distribution files; they are copied separately to an agent's personal skill directory.

## Collected skill folders

Place each collected skill under a purpose-based category:

```text
Category/Subcategory/skill-name/SKILL.md
Category/Subcategory/skill-name/references/...
Category/Subcategory/skill-name/assets/...
Category/Subcategory/skill-name/scripts/...
```

The folder immediately containing `SKILL.md` matches the skill's frontmatter `name`. Preserve the whole bundle and its frontmatter. Categories may be renamed as the collection evolves. Keep distinct same-name bundles in separate intermediate folders, such as `Category/variant-2/skill-name/`, rather than renaming a skill folder or overwriting another bundle.

## Indexes

The root and each category have an `INDEX.md` with a short purpose and links to **immediate** subcategories and skills only. A skill entry links to its `SKILL.md`; a subcategory entry links to its `INDEX.md`. Use relative paths. Avoid reproducing full skill instructions in indexes.

## Catalog

`CATALOG.md` holds one row per collected skill: stable ID, name, current library path, source and revision, license, and review status. Assign IDs once and keep them across category moves. Mark new imports `Unreviewed`; change to `Reviewed` only after a person approves the inspected bundle. Add a dated review note below the table. Unknown provenance or license should remain explicit.

The catalog is a navigation and provenance aid. The actual bundle files are the content source of truth. If a row or index disagrees with the filesystem, inspect and repair it before fetching.

## Project copies

Fetch only selected, reviewed bundles. Copy the whole folder into the target project's `.agents/skills/` for Codex or `.claude/skills/` for Claude Code, subject to the installed agent's configuration. Record selected IDs and source revisions in the project's `.skill-library/INSTALLED.md`. Keep unrelated project skills. A central update does not automatically replace a project copy.
