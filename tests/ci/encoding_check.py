import argparse
import sys
from pathlib import Path


def check_utf8(exclude_dirs):
    # Convert exclude_dirs into a set for faster lookups
    exclude_dirs = set(exclude_dirs)

    failed = False
    for file in Path(".").rglob("*.py"):
        # Skip excluded directories
        if any(excluded_dir in file.parts for excluded_dir in exclude_dirs):
            continue

        try:
            file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"Non-UTF-8 file: {file}")
            failed = True

    if failed:
        sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="Check for non-UTF-8 encoded Python files.")
    # Argument for excluded folders
    parser.add_argument("--exclude-dirs", nargs="*", default=[], help="List of directories to exclude")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    check_utf8(args.exclude_dirs)
