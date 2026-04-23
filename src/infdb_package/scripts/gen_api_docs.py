from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

PKG_DIR = ROOT_DIR / "infdb"
DOCS_DIR = ROOT_DIR / "docs"
DOCS_API_DIR = DOCS_DIR / "api"


def write(path: Path, text: str) -> None:
    """Write text to a file, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def nice_label(md_file: Path) -> str:
    """Convert a markdown filename into a readable navigation label."""
    return md_file.stem.replace("_", " ").title()


def main() -> None:
    """Generate API reference markdown files and a literate-nav SUMMARY."""
    DOCS_API_DIR.mkdir(parents=True, exist_ok=True)

    if not PKG_DIR.exists():
        raise FileNotFoundError(f"Package directory not found: {PKG_DIR}")

    md_files: list[Path] = []

    for py in sorted(PKG_DIR.rglob("*.py")):
        rel = py.relative_to(PKG_DIR)

        if rel.name == "__init__.py":
            continue

        out_path = DOCS_API_DIR / rel.with_suffix(".md")
        mod = ".".join(("infdb",) + tuple(rel.with_suffix("").parts))
        title = rel.stem.replace("_", " ").title()

        write(out_path, f"# {title}\n\n::: {mod}\n")
        md_files.append(out_path)

    lines = ["# API\n\n"]
    for md in sorted(md_files):
        link = md.relative_to(DOCS_DIR).as_posix()
        lines.append(f"- [{nice_label(md)}]({link})\n")

    write(DOCS_API_DIR / "SUMMARY.md", "".join(lines))


if __name__ == "__main__":
    main()
