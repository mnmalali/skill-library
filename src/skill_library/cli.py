"""Command line interface."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .core import LibraryError, lock, read_records, root_path
from .fetch import bootstrap, fetch, project_root
from .operations import add, doctor, init, rebuild_indexes, reorganize, search, trust


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="skill-library", description="Manage one shared local Agent Skills library")
    p.add_argument("--root", help="shared library path (default: ~/Skill-Library)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    commands = p.add_subparsers(dest="command", required=True)
    for name in ("init", "list", "doctor", "sync-status", "version"):
        sub = commands.add_parser(name)
        if name == "init": sub.add_argument("--dry-run", action="store_true")
    sub = commands.add_parser("add")
    sub.add_argument("source")
    sub.add_argument("--category")
    sub.add_argument("--dry-run", action="store_true")
    sub = commands.add_parser("index")
    sub.add_argument("--check", action="store_true")
    sub = commands.add_parser("search")
    sub.add_argument("query")
    sub = commands.add_parser("trust")
    sub.add_argument("id")
    sub.add_argument("--dry-run", action="store_true")
    sub = commands.add_parser("reorganize")
    sub.add_argument("id")
    sub.add_argument("--category", required=True)
    sub.add_argument("--dry-run", action="store_true")
    sub = commands.add_parser("fetch")
    sub.add_argument("--project")
    sub.add_argument("--agent", choices=["codex", "claude"], required=True)
    sub.add_argument("--skills", nargs="+")
    sub.add_argument("--description")
    sub.add_argument("--auto", action="store_true")
    sub.add_argument("--dry-run", action="store_true")
    sub = commands.add_parser("bootstrap")
    sub.add_argument("--agents", nargs="+", choices=["codex", "claude"], default=["codex", "claude"])
    sub.add_argument("--dry-run", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = root_path(args.root)
    try:
        if args.command == "version": result = {"version": __version__}
        elif args.command == "init": result = init(root, args.dry_run)
        elif args.command == "add": result = add(root, args.source, args.category, args.dry_run)
        elif args.command == "list": result = {"skills": read_records(root)}
        elif args.command == "search": result = {"matches": search(root, args.query)}
        elif args.command == "doctor": result = doctor(root)
        elif args.command == "sync-status":
            result = {"root": str(root), "git": (root / ".git").exists(),
                      "message": "Git sync is user-managed; no automatic pull or push"}
        elif args.command == "index":
            if args.check: result = rebuild_indexes(root, read_records(root), True)
            else:
                with lock(root): result = rebuild_indexes(root, read_records(root))
        elif args.command == "trust": result = trust(root, args.id, args.dry_run)
        elif args.command == "reorganize": result = reorganize(root, args.id, args.category, args.dry_run)
        elif args.command == "fetch":
            result = fetch(root, project_root(args.project), args.agent,
                           args.skills or [], args.description, args.auto, args.dry_run)
        elif args.command == "bootstrap":
            result = bootstrap(root, Path(__file__).resolve().parent, args.agents, args.dry_run)
        else: raise LibraryError("unknown command")
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else _human(result))
        if result.get("ok") is False:
            return 2
        return 0
    except (LibraryError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        if args.json: print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        else: print(f"error: {exc}", file=sys.stderr)
        return 2


def _human(result: dict) -> str:
    return json.dumps(result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())
