"""Library operations with fail-closed collision and trust handling."""
from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import tarfile
import tempfile
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from .core import (MAX_BYTES, MAX_FILES, MAX_FILE, META, LibraryError, atomic_json,
                   atomic_text, category_path, discover, existing_paths, inspect_tree,
                   lock, read_records, root_path, safe_relative, skill_location,
                   skill_meta, write_records)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init(root: Path, dry_run: bool = False) -> dict:
    if dry_run:
        return {"root": str(root), "would_create": not (root / "INDEX.md").exists()}
    with lock(root):
        if not (root / META / "records.json").exists():
            write_records(root, [])
        if not (root / "README.md").exists():
            atomic_text(root / "README.md", "# Skill Library\n\nShared local Agent Skills collection. Managed by `skill-library`.\n")
        rebuild_indexes(root, read_records(root))
    return {"root": str(root), "skills": len(read_records(root))}


def _download(url: str, limit: int = MAX_BYTES) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "skill-library/0.1", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        if urllib.parse.urlparse(response.url).hostname not in {"api.github.com", "codeload.github.com", "github.com"}:
            raise LibraryError("unexpected download origin")
        data = response.read(limit + 1)
        if len(data) > limit:
            raise LibraryError("download exceeds size limit")
        return data


def github_source(url: str) -> tuple[bytes, str, str]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "github.com":
        raise LibraryError("GitHub source must be an https://github.com URL")
    parts = [urllib.parse.unquote(x) for x in parsed.path.strip("/").split("/")]
    if len(parts) < 2 or any(not x or x in (".", "..") for x in parts[:2]):
        raise LibraryError("invalid GitHub repository URL")
    owner, repo = parts[:2]
    if repo.endswith(".git"):
        repo = repo[:-4]
    if not all(c.isalnum() or c in "-_" for c in owner + repo):
        raise LibraryError("invalid GitHub owner or repository")
    ref = "HEAD"
    subdir = ""
    if len(parts) > 2:
        if len(parts) < 4 or parts[2] != "tree":
            raise LibraryError("use a repository URL or /tree/REF/PATH URL")
        ref = parts[3]
        subdir = "/".join(parts[4:])
        if subdir:
            safe_relative(subdir)
    api = f"https://api.github.com/repos/{owner}/{repo}/commits/{urllib.parse.quote(ref, safe='')}"
    commit = json.loads(_download(api, 2 * 1024 * 1024))["sha"]
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise LibraryError("invalid GitHub commit")
    archive = _download(f"https://codeload.github.com/{owner}/{repo}/zip/{commit}")
    return archive, commit, subdir


def extract_archive(data: bytes | Path, dest: Path) -> None:
    """Validate every member before writing any member."""
    source = io.BytesIO(data) if isinstance(data, bytes) else data
    is_zip = zipfile.is_zipfile(source)
    if is_zip:
        with zipfile.ZipFile(source) as archive:
            members = []
            total = 0
            for item in archive.infolist():
                rel = safe_relative(item.filename.rstrip("/"))
                mode = (item.external_attr >> 16) & 0o170000
                if mode not in (0, 0o040000, 0o100000):
                    raise LibraryError("archive contains link or special file")
                if item.file_size > MAX_FILE or item.file_size > max(item.compress_size, 1) * 100:
                    raise LibraryError("archive member exceeds size or compression ratio limit")
                total += item.file_size
                members.append((item, rel))
            if len(members) > MAX_FILES or total > MAX_BYTES:
                raise LibraryError("archive exceeds limits")
            _extract_members(((rel, item.is_dir(), archive.open(item) if not item.is_dir() else None)
                              for item, rel in members), dest)
    else:
        try:
            with tarfile.open(fileobj=source if isinstance(source, io.BytesIO) else None,
                              name=str(source) if isinstance(source, Path) else None, mode="r:*") as archive:
                members = []
                total = 0
                for item in archive.getmembers():
                    rel = safe_relative(item.name.rstrip("/"))
                    if not (item.isfile() or item.isdir()):
                        raise LibraryError("archive contains link or special file")
                    total += item.size
                    if item.size > MAX_FILE:
                        raise LibraryError("archive member exceeds file size limit")
                    members.append((item, rel))
                if len(members) > MAX_FILES or total > MAX_BYTES:
                    raise LibraryError("archive exceeds limits")
                _extract_members(((rel, item.isdir(), archive.extractfile(item) if item.isfile() else None)
                                  for item, rel in members), dest)
        except tarfile.TarError as exc:
            raise LibraryError(f"invalid archive: {exc}") from exc


def _extract_members(members, dest: Path) -> None:
    seen = set()
    for rel, is_dir, stream in members:
        key = rel.as_posix().casefold()
        if key in seen:
            raise LibraryError("duplicate archive path")
        seen.add(key)
        target = dest / rel
        if is_dir:
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise LibraryError("archive path collision")
        with stream, target.open("xb") as output:
            shutil.copyfileobj(stream, output)


def _source_stage(source: str, stage: Path) -> tuple[Path, str, str | None]:
    if source.startswith("https://github.com/"):
        data, commit, subdir = github_source(source)
        extract_archive(data, stage)
        top = [p for p in stage.iterdir() if p.is_dir()]
        if len(top) != 1:
            raise LibraryError("unexpected GitHub archive layout")
        chosen = top[0] / safe_relative(subdir) if subdir else top[0]
        if not chosen.is_dir():
            raise LibraryError("GitHub subdirectory not found")
        return chosen, source, commit
    raw = Path(source).expanduser()
    if raw.is_symlink():
        raise LibraryError("source symlink not allowed")
    p = raw.resolve()
    if p.is_dir():
        if p.is_symlink():
            raise LibraryError("source symlink not allowed")
        return p, str(p), None
    if p.is_file():
        if p.stat().st_size > MAX_BYTES:
            raise LibraryError("archive exceeds download limit")
        extract_archive(p, stage)
        return stage, str(p), None
    raise LibraryError("source does not exist")


def add(root: Path, source: str, category: str | None = None, dry_run: bool = False) -> dict:
    if not (root / META / "records.json").exists():
        raise LibraryError("initialize library first")
    with tempfile.TemporaryDirectory(prefix="skill-library-stage-") as temp:
        chosen, origin, commit = _source_stage(source, Path(temp))
        bundles = discover(chosen)
        if not bundles:
            raise LibraryError("source contains no valid skill folders")
        prepared = []
        for bundle in bundles:
            meta = skill_meta(bundle)
            digest, files, size = inspect_tree(bundle)
            prepared.append((bundle, meta, digest, files, size))
        with lock(root):
            records = read_records(root)
            existing_paths(root, records)
            hashes = {r["hash"] for r in records}
            planned = []
            for bundle, meta, digest, files, size in prepared:
                if digest in hashes:
                    planned.append({"name": meta["name"], "status": "duplicate", "hash": digest})
                    continue
                hashes.add(digest)
                category_rel = category_path(category)
                if category_rel.parts[0].casefold() in {META.casefold(), ".git"}:
                    raise LibraryError("category uses a reserved directory")
                for prior in records:
                    prior_path = Path(prior["path"])
                    if category_rel == prior_path or prior_path in category_rel.parents:
                        raise LibraryError("category cannot be nested inside a skill bundle")
                candidate = category_rel / meta["name"]
                if (root / candidate).exists() or any(p.get("path") == candidate.as_posix() for p in planned):
                    candidate = category_rel / ("variant-" + digest[:12]) / meta["name"]
                while (root / candidate).exists():
                    candidate = category_rel / ("variant-" + digest[:20]) / meta["name"]
                    if (root / candidate).exists():
                        raise LibraryError("cannot find collision-free destination")
                relative_source = bundle.relative_to(chosen).as_posix()
                stable = hashlib.sha256((origin + "\0" + relative_source + "\0" + digest).encode()).hexdigest()[:20]
                rec = {"id": stable, "name": meta["name"], "description": meta["description"],
                       "hash": digest, "path": candidate.as_posix(), "source": origin,
                       "source_path": relative_source, "commit": commit, "license": meta["license"],
                       "compatibility": meta["compatibility"], "trusted": False,
                       "imported_at": now(), "files": files, "bytes": size}
                planned.append({"name": meta["name"], "status": "added", "path": rec["path"], "id": stable, "record": rec, "bundle": bundle})
            if dry_run:
                return {"results": [{k: v for k, v in p.items() if k not in ("record", "bundle")} for p in planned]}
            installed = []
            previous = list(records)
            try:
                for item in planned:
                    if item["status"] != "added":
                        continue
                    dest = root / item["path"]
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    installed.append(dest)
                    shutil.copytree(item["bundle"], dest, symlinks=False)
                    if inspect_tree(dest)[0] != item["record"]["hash"]:
                        raise LibraryError("copy verification failed")
                    records.append(item["record"])
                write_records(root, records)
                rebuild_indexes(root, records)
            except Exception:
                write_records(root, previous)
                for path in reversed(installed):
                    if path.exists():
                        shutil.rmtree(path)
                rebuild_indexes(root, previous)
                raise
            return {"results": [{k: v for k, v in p.items() if k not in ("record", "bundle")} for p in planned]}


def _index_content(root: Path, category: Path, records: list[dict]) -> str:
    title = "Skill Library" if category == Path(".") else category.name
    lines = [f"# {title}", "", "Direct folders and skills in this category.", ""]
    prefix = () if category == Path(".") else category.parts
    children = {}
    for rec in records:
        parts = Path(rec["path"]).parts
        if parts[:len(prefix)] != prefix or len(parts) <= len(prefix):
            continue
        child = parts[len(prefix)]
        if len(parts) == len(prefix) + 1:
            children[child] = ("skill", rec["description"])
        else:
            children.setdefault(child, ("folder", "Skill category"))
    for name, (kind, desc) in sorted(children.items(), key=lambda pair: pair[0].casefold()):
        target = f"{name}/SKILL.md" if kind == "skill" else f"{name}/INDEX.md"
        lines.append(f"- [{name}]({target}) — {desc.replace(chr(10), ' ')}")
    return "\n".join(lines) + "\n"


def index_map(root: Path, records: list[dict]) -> dict[Path, str]:
    categories = {Path(".")}
    for rec in records:
        parent = Path(rec["path"]).parent
        while parent != Path("."):
            categories.add(parent)
            parent = parent.parent
    return {root / cat / "INDEX.md": _index_content(root, cat, records) for cat in categories}


def rebuild_indexes(root: Path, records: list[dict], check: bool = False) -> dict:
    expected = index_map(root, records)
    inventory = root / META / "index-paths.json"
    previous = json.loads(inventory.read_text(encoding="utf-8")) if inventory.is_file() else []
    obsolete = [root / safe_relative(value) for value in previous if root / safe_relative(value) not in expected]
    stale = [str(path.relative_to(root)) for path, value in expected.items()
             if not path.exists() or path.read_text(encoding="utf-8") != value]
    stale.extend(str(path.relative_to(root)) for path in obsolete if path.exists())
    if check:
        return {"ok": not stale, "stale": sorted(stale)}
    for path, value in expected.items():
        atomic_text(path, value)
    for path in obsolete:
        if path.name == "INDEX.md":
            path.unlink(missing_ok=True)
    atomic_json(inventory, sorted(str(path.relative_to(root)).replace("\\", "/") for path in expected))
    return {"updated": len(expected), "stale": sorted(stale)}


def search(root: Path, query: str) -> list[dict]:
    terms = query.casefold().split()
    ranked = []
    for rec in read_records(root):
        hay = (rec["name"] + " " + rec["description"] + " " + rec["path"]).casefold()
        score = sum(3 if term in rec["name"].casefold() else 1 for term in terms if term in hay)
        if score:
            ranked.append((score, rec))
    return [r for _, r in sorted(ranked, key=lambda x: (-x[0], x[1]["name"], x[1]["id"]))]


def trust(root: Path, selector: str, dry_run: bool = False) -> dict:
    with lock(root):
        records = read_records(root)
        matches = [r for r in records if r["id"] == selector]
        if len(matches) != 1:
            raise LibraryError("trust requires an exact record ID")
        rec = matches[0]
        if inspect_tree(skill_location(root, rec))[0] != rec["hash"]:
            raise LibraryError("bundle changed since import; reimport before trusting")
        if not dry_run:
            rec["trusted"] = True
            rec["trusted_at"] = now()
            write_records(root, records)
        return {"id": rec["id"], "trusted": not dry_run, "dry_run": dry_run}


def doctor(root: Path) -> dict:
    issues = []
    records = read_records(root)
    for rec in records:
        try:
            folder = skill_location(root, rec)
            if inspect_tree(folder)[0] != rec["hash"]:
                issues.append(f"changed bundle: {rec['id']}")
            skill_meta(folder)
        except (LibraryError, OSError) as exc:
            issues.append(f"{rec['id']}: {exc}")
    issues.extend("stale index: " + x for x in rebuild_indexes(root, records, check=True)["stale"])
    return {"ok": not issues, "skills": len(records), "issues": issues}


def reorganize(root: Path, selector: str, category: str, dry_run: bool = False) -> dict:
    with lock(root):
        records = read_records(root)
        matches = [r for r in records if r["id"] == selector]
        if len(matches) != 1:
            raise LibraryError("reorganize requires an exact record ID")
        rec = matches[0]
        old = skill_location(root, rec)
        category_rel = category_path(category)
        if category_rel.parts[0].casefold() in {META.casefold(), ".git"}:
            raise LibraryError("category uses a reserved directory")
        for prior in records:
            prior_path = Path(prior["path"])
            if category_rel == prior_path or prior_path in category_rel.parents:
                raise LibraryError("category cannot be nested inside a skill bundle")
        dest_rel = category_rel / rec["name"]
        dest = root / dest_rel
        if dest != old and dest.exists():
            dest_rel = category_rel / ("variant-" + rec["hash"][:12]) / rec["name"]
            dest = root / dest_rel
        if dest != old and dest.exists():
            raise LibraryError("destination already exists")
        result = {"id": selector, "from": rec["path"], "to": dest_rel.as_posix()}
        if dry_run or dest == old:
            return result
        journal = root / META / "journal.json"
        atomic_json(journal, {"operation": "move", **result})
        previous = rec["path"]
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            old.rename(dest)
            rec["path"] = dest_rel.as_posix()
            write_records(root, records)
            rebuild_indexes(root, records)
            journal.unlink(missing_ok=True)
        except Exception:
            if dest.exists() and not old.exists():
                old.parent.mkdir(parents=True, exist_ok=True)
                dest.rename(old)
            rec["path"] = previous
            write_records(root, records)
            rebuild_indexes(root, records)
            raise
        return result
