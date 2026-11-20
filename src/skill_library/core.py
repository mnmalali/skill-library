"""Filesystem and metadata primitives. Imported content is always treated as data."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

import yaml

MAX_FILES = 2000
MAX_BYTES = 100 * 1024 * 1024
MAX_FILE = 25 * 1024 * 1024
MAX_DEPTH = 20
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BAD_WINDOWS = re.compile(r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$", re.I)
META = ".skill-library"


class LibraryError(Exception):
    pass


def safe_part(part: str) -> None:
    if not part or part in (".", "..") or part[-1] in ". " or BAD_WINDOWS.match(part):
        raise LibraryError(f"unsafe path component: {part!r}")
    if any(c in part for c in '<>:"\\|?*\x00') or any(ord(c) < 32 for c in part):
        raise LibraryError(f"unsafe path component: {part!r}")


def safe_relative(value: str) -> Path:
    if not value or value.startswith(("/", "\\")) or "\\" in value or ":" in value:
        raise LibraryError(f"unsafe relative path: {value!r}")
    parts = PurePosixPath(value).parts
    if not parts or len(parts) > MAX_DEPTH:
        raise LibraryError("path nesting limit exceeded")
    for part in parts:
        safe_part(part)
    return Path(*parts)


def root_path(value: str | None = None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    if os.environ.get("SKILL_LIBRARY_ROOT"):
        return Path(os.environ["SKILL_LIBRARY_ROOT"]).expanduser().resolve()
    for agent in (".codex", ".claude"):
        pointer = Path.home() / agent / "skill-library.json"
        if pointer.is_file():
            try:
                return Path(json.loads(pointer.read_text(encoding="utf-8"))["root"]).expanduser().resolve()
            except (ValueError, KeyError, OSError):
                pass
    return (Path.home() / "Skill-Library").resolve()


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as out:
            out.write(value)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def atomic_json(path: Path, value: object) -> None:
    atomic_text(path, json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


@contextmanager
def lock(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    state = root / META
    state.mkdir(exist_ok=True)
    path = state / "lock"
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise LibraryError("library is locked; inspect .skill-library/lock before retrying") from exc
    try:
        os.write(fd, f"pid={os.getpid()} time={time.time()}".encode())
        os.close(fd)
        yield
    finally:
        path.unlink(missing_ok=True)


def read_records(root: Path) -> list[dict]:
    path = root / META / "records.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise LibraryError("invalid records.json")
    return data


def write_records(root: Path, records: list[dict]) -> None:
    atomic_json(root / META / "records.json", sorted(records, key=lambda r: r["id"]))


def inspect_tree(folder: Path) -> tuple[str, int, int]:
    """Reject links and unsafe names; hash every file and its relative path."""
    if folder.is_symlink() or not folder.is_dir():
        raise LibraryError("skill source must be a real directory")
    digest = hashlib.sha256()
    count = total = 0
    seen: set[str] = set()
    for base, dirs, files in os.walk(folder, followlinks=False):
        base_path = Path(base)
        for name in dirs + files:
            rel = (base_path / name).relative_to(folder)
            if len(rel.parts) > MAX_DEPTH:
                raise LibraryError("path nesting limit exceeded")
            safe_part(name)
            folded = rel.as_posix().casefold()
            if folded in seen:
                raise LibraryError("case-insensitive path collision")
            seen.add(folded)
            p = base_path / name
            mode = p.lstat().st_mode
            if stat.S_ISLNK(mode) or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise LibraryError("links and special files are not allowed")
        dirs.sort()
        for name in sorted(files):
            p = base_path / name
            rel = p.relative_to(folder).as_posix()
            size = p.stat().st_size
            count += 1
            total += size
            if count > MAX_FILES or total > MAX_BYTES or size > MAX_FILE:
                raise LibraryError("skill size or file count limit exceeded")
            digest.update(rel.encode("utf-8"))
            digest.update(b"\0")
            with p.open("rb") as stream:
                while block := stream.read(1024 * 1024):
                    digest.update(block)
            digest.update(b"\0")
    return digest.hexdigest(), count, total


def skill_meta(folder: Path) -> dict:
    path = folder / "SKILL.md"
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 1024 * 1024:
        raise LibraryError(f"missing or oversized SKILL.md: {folder}")
    content = path.read_text(encoding="utf-8-sig")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", content, re.S)
    if not match:
        raise LibraryError(f"malformed SKILL.md frontmatter: {folder}")
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise LibraryError(f"invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise LibraryError("SKILL.md frontmatter must be a mapping")
    name, desc = data.get("name"), data.get("description")
    if not isinstance(name, str) or len(name) > 64 or not NAME.fullmatch(name):
        raise LibraryError("invalid skill name")
    if folder.name != name:
        raise LibraryError(f"skill folder must match name {name!r}")
    if not isinstance(desc, str) or not (1 <= len(desc) <= 1024):
        raise LibraryError("invalid skill description")
    return {"name": name, "description": desc.strip(), "license": data.get("license"),
            "compatibility": data.get("compatibility")}


def discover(source: Path) -> list[Path]:
    inspect_tree(source)
    found = []
    for base, dirs, files in os.walk(source, followlinks=False):
        dirs[:] = [d for d in dirs if d not in (META, ".git")]
        if "SKILL.md" in files:
            found.append(Path(base))
            dirs.clear()
    return sorted(found)


def category_path(value: str | None) -> Path:
    if not value:
        return Path("Uncategorized")
    return safe_relative(value.replace("\\", "/"))


def skill_location(root: Path, rec: dict) -> Path:
    rel = safe_relative(rec["path"])
    path = root / rel
    if not path.resolve().is_relative_to(root.resolve()):
        raise LibraryError("record escapes library root")
    return path


def existing_paths(root: Path, records: list[dict]) -> None:
    seen = set()
    for rec in records:
        key = rec["path"].casefold()
        if key in seen:
            raise LibraryError("duplicate record paths")
        seen.add(key)
        if not skill_location(root, rec).is_dir():
            raise LibraryError(f"missing skill bundle: {rec['path']}")
