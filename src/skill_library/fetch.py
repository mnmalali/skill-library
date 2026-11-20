"""Project-scoped copies and management skill bootstrap."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from .core import (LibraryError, atomic_json, inspect_tree, read_records,
                   skill_location)
from .operations import search

AGENT_DIR = {"codex": ".agents/skills", "claude": ".claude/skills"}


def project_root(path: str | None) -> Path:
    start = Path(path or ".").expanduser().resolve()
    if not start.is_dir():
        raise LibraryError("project path must be a directory")
    if path:
        return start
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start


def _install_dir(project: Path, agent: str) -> Path:
    if agent not in AGENT_DIR:
        raise LibraryError("agent must be codex or claude")
    dest = project / AGENT_DIR[agent]
    if dest.is_symlink() or not dest.resolve().is_relative_to(project.resolve()):
        raise LibraryError("project skill directory escapes project")
    return dest


def fetch(root: Path, project: Path, agent: str, skills: list[str],
          description: str | None, auto: bool, dry_run: bool = False) -> dict:
    records = read_records(root)
    if not skills and not description:
        raise LibraryError("provide --skills or --description")
    selected = []
    if skills:
        for selector in skills:
            matches = [r for r in records if r["id"] == selector or r["name"] == selector]
            if len(matches) != 1:
                raise LibraryError(f"skill {selector!r} is missing or ambiguous; use its exact ID")
            if matches[0] not in selected:
                selected.append(matches[0])
    else:
        candidates = search(root, description or "")[:5]
        if not auto:
            return {"recommendations": [{"id": r["id"], "name": r["name"],
                                         "description": r["description"], "trusted": r["trusted"],
                                         "compatibility": r["compatibility"]} for r in candidates],
                    "installed": [], "approval_required": True}
        selected = [r for r in candidates if r["trusted"]][:3]
    dest_root = _install_dir(project, agent)
    names = [r["name"] for r in selected]
    if len(names) != len(set(names)):
        raise LibraryError("selected skills share a name; install one by exact ID")
    manifest = project / ".skill-library" / f"{agent}-manifest.json"
    prior = json.loads(manifest.read_text(encoding="utf-8")) if manifest.is_file() else {}
    installed = []
    for rec in selected:
        if not rec["trusted"]:
            raise LibraryError(f"skill {rec['id']} is untrusted; review and run trust first")
        source = skill_location(root, rec)
        if inspect_tree(source)[0] != rec["hash"]:
            raise LibraryError(f"skill {rec['id']} changed since import")
        dest = dest_root / rec["name"]
        if dest.exists():
            if dest.is_symlink() or not dest.is_dir():
                raise LibraryError(f"project destination is unsafe: {dest}")
            if inspect_tree(dest)[0] == rec["hash"]:
                installed.append({"name": rec["name"], "status": "already-installed", "path": str(dest)})
                continue
            raise LibraryError(f"project skill already exists with different content: {dest}")
        installed.append({"name": rec["name"], "status": "would-install" if dry_run else "installed", "path": str(dest)})
    if dry_run:
        return {"installed": installed, "project": str(project), "agent": agent}
    created = []
    try:
        dest_root.mkdir(parents=True, exist_ok=True)
        for item in installed:
            if item["status"] != "installed":
                continue
            rec = next(r for r in selected if r["name"] == item["name"])
            dest = Path(item["path"])
            shutil.copytree(skill_location(root, rec), dest)
            created.append(dest)
            if inspect_tree(dest)[0] != rec["hash"]:
                raise LibraryError("project copy verification failed")
            prior[rec["name"]] = {"id": rec["id"], "hash": rec["hash"], "source": str(root)}
        atomic_json(manifest, prior)
    except Exception:
        for path in reversed(created):
            shutil.rmtree(path)
        raise
    return {"installed": installed, "project": str(project), "agent": agent}


def bootstrap(root: Path, package_root: Path, agents: list[str], dry_run: bool = False) -> dict:
    result = []
    for agent in agents:
        if agent not in AGENT_DIR:
            raise LibraryError("agent must be codex or claude")
        home = Path.home() / (".codex" if agent == "codex" else ".claude")
        skills_home = home / "skills"
        for name in ("setup-skill-library", "fetch-skill-library"):
            source = package_root / "management_skills" / name
            dest = skills_home / name
            if dest.exists() and inspect_tree(dest)[0] != inspect_tree(source)[0]:
                raise LibraryError(f"existing management skill differs: {dest}")
            result.append({"agent": agent, "skill": name, "path": str(dest),
                           "status": "exists" if dest.exists() else "would-install" if dry_run else "installed"})
            if not dry_run and not dest.exists():
                skills_home.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source, dest)
        pointer = home / "skill-library.json"
        if pointer.is_file():
            previous = json.loads(pointer.read_text(encoding="utf-8"))
            if previous.get("root") != str(root):
                raise LibraryError(f"existing pointer uses another library: {pointer}")
        elif not dry_run:
            atomic_json(pointer, {"root": str(root)})
    return {"root": str(root), "results": result}
