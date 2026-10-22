#!/usr/bin/env python3
"""Validate the standalone skill package using only the Python standard library."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "finance-project-economics"
MANIFEST_PATH = ROOT / "dev" / "source-files.json"
EXPECTED_FILE_COUNT = 10
EXPECTED_LINK_COUNT = 22
EXPECTED_SOURCE_HASH_COUNT = 4
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class CheckError(Exception):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CheckError(f"cannot read JSON {path.relative_to(ROOT)}: {exc}") from exc
    require(isinstance(value, dict), f"expected an object in {path.relative_to(ROOT)}")
    return value


def load_file_manifest() -> list[dict[str, str]]:
    data = read_json(MANIFEST_PATH)
    entries = data.get("files")
    require(isinstance(entries, list), "dev/source-files.json must contain a files array")
    require(len(entries) == EXPECTED_FILE_COUNT, f"expected {EXPECTED_FILE_COUNT} copied files, found {len(entries)}")
    seen: set[str] = set()
    normalized: list[dict[str, str]] = []
    for entry in entries:
        require(isinstance(entry, dict), "each copied-file manifest entry must be an object")
        rel = entry.get("path")
        digest = entry.get("sha256")
        require(isinstance(rel, str) and isinstance(digest, str), "manifest entries need path and sha256 strings")
        posix = PurePosixPath(rel)
        require(not posix.is_absolute() and ".." not in posix.parts, f"unsafe manifest path: {rel}")
        require(rel.startswith("skills/finance-project-economics/"), f"manifest path is outside the copied skill: {rel}")
        require(rel not in seen, f"duplicate manifest path: {rel}")
        require(bool(SHA256_RE.fullmatch(digest)), f"invalid SHA-256 for {rel}")
        seen.add(rel)
        normalized.append({"path": rel, "sha256": digest})

    actual = sorted(path.relative_to(ROOT).as_posix() for path in SKILL_DIR.rglob("*") if path.is_file())
    expected = sorted(seen)
    require(actual == expected, f"copied skill inventory differs from manifest (actual {len(actual)}, manifest {len(expected)})")
    for entry in normalized:
        path = ROOT / entry["path"]
        require(path.is_file(), f"missing copied file: {entry['path']}")
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        require(actual_hash == entry["sha256"], f"SHA-256 mismatch: {entry['path']}")
    return normalized


def check_frontmatter() -> None:
    path = SKILL_DIR / "SKILL.md"
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    require(bool(lines) and lines[0].strip() == "---", "SKILL.md must start with YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise CheckError("SKILL.md frontmatter has no closing ---") from exc
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            fields[match.group(1)] = match.group(2).strip()
    require(fields.get("name") == "finance-project-economics", "SKILL.md frontmatter name is missing or incorrect")
    require(bool(fields.get("description")), "SKILL.md frontmatter description is empty")


def markdown_target(raw: str) -> str | None:
    value = raw.strip()
    if value.startswith("<"):
        close = value.find(">")
        if close >= 0:
            value = value[1:close]
    else:
        value = value.split()[0] if value else ""
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    return unquote(parsed.path)


def check_links() -> int:
    checked = 0
    markdown_files = sorted(path for path in SKILL_DIR.rglob("*.md") if path.is_file())
    for markdown in markdown_files:
        content = markdown.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(content):
            target = markdown_target(match.group(1))
            if target is None:
                continue
            checked += 1
            resolved = (markdown.parent / target).resolve()
            require(resolved.is_relative_to(SKILL_DIR.resolve()), f"link escapes skill package: {markdown.relative_to(ROOT)} -> {target}")
            require(resolved.is_file(), f"broken package-relative link: {markdown.relative_to(ROOT)} -> {target}")
    require(checked == EXPECTED_LINK_COUNT, f"expected {EXPECTED_LINK_COUNT} package-relative links, found {checked}")
    return checked


def check_source_hashes() -> int:
    data = read_json(SKILL_DIR / "references" / "source-manifest.json")
    sources = data.get("sources")
    require(isinstance(sources, list), "references/source-manifest.json must contain a sources array")
    require(len(sources) == EXPECTED_SOURCE_HASH_COUNT, f"expected {EXPECTED_SOURCE_HASH_COUNT} source hashes, found {len(sources)}")
    for source in sources:
        require(isinstance(source, dict), "each source entry must be an object")
        require(isinstance(source.get("id"), str) and isinstance(source.get("path"), str), "source entries need id and path")
        digest = source.get("sha256")
        require(isinstance(digest, str) and bool(SHA256_RE.fullmatch(digest)), f"invalid source SHA-256 for {source.get('id', '<unknown>')}")
    return len(sources)


def check_zip(path: Path, entries: list[dict[str, str]]) -> None:
    require(path.is_file(), f"ZIP bundle not found: {path}")
    try:
        with zipfile.ZipFile(path) as archive:
            names = [name for name in archive.namelist() if not name.endswith("/")]
            for entry in entries:
                rel = entry["path"]
                matches = [name for name in names if name == rel or name.endswith("/" + rel)]
                require(len(matches) == 1, f"ZIP {path.name} must contain exactly one copy of {rel}; found {len(matches)}")
                archived = archive.read(matches[0])
                packaged = (ROOT / rel).read_bytes()
                require(archived == packaged, f"ZIP bytes differ for {rel} in {path.name}")
    except zipfile.BadZipFile as exc:
        raise CheckError(f"invalid ZIP bundle {path}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", action="append", type=Path, help="optional ZIP bundle to compare; root-level ZIPs are detected automatically")
    args = parser.parse_args()
    try:
        entries = load_file_manifest()
        check_frontmatter()
        link_count = check_links()
        source_hash_count = check_source_hashes()
        bundles = [path.resolve() for path in args.zip] if args.zip else sorted(ROOT.glob("*.zip"))
        for bundle in bundles:
            check_zip(bundle, entries)
    except (CheckError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"PASS: {len(entries)} copied skill files match dev/source-files.json SHA-256 values.")
    print("PASS: SKILL.md frontmatter has the required name and a description.")
    print(f"PASS: {link_count} package-relative links resolve within the skill package.")
    print(f"PASS: {source_hash_count} source-manifest SHA-256 entries are valid.")
    if bundles:
        print(f"PASS: ZIP byte correspondence checked for {len(entries)} files in {len(bundles)} bundle(s).")
    else:
        print("SKIP: ZIP byte correspondence; no ZIP bundle was supplied or bundled.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
