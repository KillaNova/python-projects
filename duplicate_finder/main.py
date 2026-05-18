"""
Duplicate File Finder and Remover
Scans a directory, groups files by content hash, and lets you
interactively delete duplicates while keeping one copy.
"""

import os
import hashlib
import argparse
from collections import defaultdict


def hash_file(path: str, chunk: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while data := f.read(chunk):
            h.update(data)
    return h.hexdigest()


def find_duplicates(root: str) -> dict[str, list[str]]:
    hashes: dict[str, list[str]] = defaultdict(list)
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            full = os.path.join(dirpath, name)
            try:
                hashes[hash_file(full)].append(full)
            except (OSError, PermissionError):
                pass
    return {h: paths for h, paths in hashes.items() if len(paths) > 1}


def human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def interactive_remove(duplicates: dict[str, list[str]], dry_run: bool) -> None:
    if not duplicates:
        print("No duplicates found.")
        return

    total_groups = len(duplicates)
    freed = 0

    for idx, (digest, paths) in enumerate(duplicates.items(), 1):
        size = os.path.getsize(paths[0])
        print(f"\n[{idx}/{total_groups}] Hash: {digest[:12]}…  Size: {human_size(size)} each")
        for i, p in enumerate(paths):
            print(f"  [{i}] {p}")

        print("  Keep which copy? Enter number(s) to DELETE (e.g. 1 2), 'k' to keep all, 's' to skip: ", end="")
        choice = input().strip().lower()

        if choice in ("k", "s", ""):
            continue

        to_delete = []
        for token in choice.split():
            if token.isdigit() and 0 <= int(token) < len(paths):
                to_delete.append(paths[int(token)])

        for path in to_delete:
            if dry_run:
                print(f"  [DRY-RUN] Would delete: {path}")
            else:
                try:
                    os.remove(path)
                    print(f"  Deleted: {path}")
                    freed += size
                except OSError as e:
                    print(f"  Error deleting {path}: {e}")

    if not dry_run:
        print(f"\nDone. Freed ~{human_size(freed)}.")


def auto_remove(duplicates: dict[str, list[str]], dry_run: bool) -> None:
    """Keep the first (shortest path) copy, delete the rest."""
    freed = 0
    for paths in duplicates.values():
        keep = min(paths, key=len)
        size = os.path.getsize(keep)
        for path in paths:
            if path == keep:
                continue
            if dry_run:
                print(f"[DRY-RUN] Would delete: {path}  (keeping {keep})")
            else:
                try:
                    os.remove(path)
                    print(f"Deleted: {path}")
                    freed += size
                except OSError as e:
                    print(f"Error: {e}")
    if not dry_run:
        print(f"\nFreed ~{human_size(freed)}.")


def main():
    parser = argparse.ArgumentParser(description="Duplicate file finder and remover")
    parser.add_argument("directory", help="Root directory to scan")
    parser.add_argument("--auto", action="store_true", help="Auto-delete duplicates, keep shortest path")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory.")
        return

    print(f"Scanning '{args.directory}' …")
    duplicates = find_duplicates(args.directory)
    print(f"Found {len(duplicates)} duplicate group(s) across {sum(len(v) for v in duplicates.values())} files.\n")

    if args.auto:
        auto_remove(duplicates, args.dry_run)
    else:
        interactive_remove(duplicates, args.dry_run)


if __name__ == "__main__":
    main()
