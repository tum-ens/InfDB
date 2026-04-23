import re
from pathlib import Path
from typing import Optional, Union

from bs4 import BeautifulSoup, Tag
from markdownify import markdownify as markdownify_html  # type: ignore[import-not-found]

ROOT_DIR = Path(__file__).resolve().parent.parent

SITE_DIR = ROOT_DIR / "site"
OUT_DIR = ROOT_DIR / "documentation"

SKIP_FILES = {"404.html", "sitemap.xml", "sitemap.xml.gz"}

_LINK_PATTERN = re.compile(r"\]\(([^)]+)\)")


def _select_main_content(soup: BeautifulSoup) -> Tag:
    """Return the main page content for MkDocs Material pages."""
    article = soup.select_one("article.md-content__inner")
    if article:
        return article

    main = soup.select_one("main")
    if main:
        return main

    return soup.body or soup


def _remove_heading_permalinks(container: Tag) -> None:
    """Remove the '¶' anchors injected by MkDocs permalinks."""
    for anchor in container.select("a.headerlink"):
        anchor.decompose()


def _replace_highlight_tables_with_pre(container: Tag) -> None:
    """Replace line-number code tables with a single <pre> block."""
    for table in container.select("table.highlighttable"):
        code_text = None

        code_td = table.select_one("td.code")
        if code_td:
            pre = code_td.find("pre")
            if pre:
                code_text = pre.get_text()

        if not code_text:
            code_text = table.get_text()

        new_pre = soup_new_tag(container, "pre")
        new_pre.string = code_text.rstrip("\n") + "\n"
        table.replace_with(new_pre)


def _remove_mkdocstrings_source_blocks(container: Tag) -> None:
    """Remove mkdocstrings 'Source code in ...' blocks and related tables."""
    candidates: list[Tag] = []
    for el in container.find_all(["p", "div", "span"]):
        txt = el.get_text(" ", strip=True)
        if "Source code in" in txt:
            candidates.append(el)

    for el in candidates:
        nxt = el.find_next_sibling()
        el.decompose()
        if isinstance(nxt, Tag) and nxt.name == "table" and "highlighttable" in (nxt.get("class") or []):
            nxt.decompose()


def soup_new_tag(container: Tag, name: str) -> Tag:
    """Create a new tag using the underlying BeautifulSoup document."""
    root: Optional[Union[Tag, BeautifulSoup]] = container

    while root is not None and not isinstance(root, BeautifulSoup):
        root = root.parent  # type: ignore[assignment]

    if isinstance(root, BeautifulSoup):
        return root.new_tag(name)

    raise RuntimeError("Could not locate BeautifulSoup root.")


def _html_to_markdown(html_fragment: str) -> str:
    """Convert HTML to Markdown."""
    return markdownify_html(html_fragment, heading_style="ATX")


def _rewrite_internal_links(md_text: str) -> str:
    """Rewrite MkDocs pretty URLs to *.md (best-effort)."""

    def repl(match: re.Match[str]) -> str:
        target = match.group(1).strip()

        if target.startswith(("http://", "https://", "mailto:", "tel:")):
            return match.group(0)
        if target.startswith("#"):
            return match.group(0)

        anchor = ""
        query = ""
        base = target

        if "?" in base:
            base, query = base.split("?", 1)
            query = "?" + query

        if "#" in base:
            base, anchor = base.split("#", 1)
            anchor = "#" + anchor

        base = base.lstrip("/")

        if base.endswith("/index.html"):
            base = base[: -len("/index.html")] + ".md"
        elif base.endswith(".html"):
            base = base[: -len(".html")] + ".md"
        elif base.endswith("/"):
            base = base.rstrip("/") + ".md"

        return f"]({base}{query}{anchor})"

    return _LINK_PATTERN.sub(repl, md_text)


def _strip_leftover_permalink_tokens(md_text: str) -> str:
    """Remove leftover '[¶](...)' permalink markers if any survive."""
    md_text = re.sub(r"\[\s*¶\s*\]\([^)]+\)", "", md_text)
    return md_text.replace(' "Permanent link"', "")


def _collapse_blank_lines(md_text: str, max_blank: int = 2) -> str:
    """Collapse runs of blank lines."""
    lines = [ln.rstrip() for ln in md_text.splitlines()]
    out: list[str] = []
    blank = 0

    for ln in lines:
        if ln.strip() == "":
            blank += 1
            if blank <= max_blank:
                out.append("")
        else:
            blank = 0
            out.append(ln)

    return "\n".join(out).strip() + "\n"


def out_path_for_html(html_path: Path) -> Optional[Path]:
    """Map built HTML pages to Markdown paths under OUT_DIR."""
    rel = html_path.relative_to(SITE_DIR)

    if rel.name in SKIP_FILES:
        return None

    if rel.name == "index.html":
        if rel.parent.as_posix() == ".":
            return OUT_DIR / "index.md"
        return OUT_DIR / Path(f"{rel.parent}.md")

    return OUT_DIR / rel.with_suffix(".md")


def export_site() -> None:
    """Export the built MkDocs site (HTML) to Markdown files."""
    if not SITE_DIR.exists():
        cfg = ROOT_DIR / "mkdocs.yml"
        msg = f"{SITE_DIR} not found. Build first with: python3 -m mkdocs build -f {cfg}"
        raise SystemExit(msg)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    html_files = [p for p in SITE_DIR.rglob("*.html") if p.is_file() and p.name not in SKIP_FILES]

    count = 0
    for html_path in html_files:
        out_path = out_path_for_html(html_path)
        if out_path is None:
            continue

        html_text = html_path.read_text(encoding="utf-8", errors="ignore")
        soup = BeautifulSoup(html_text, "html.parser")
        main = _select_main_content(soup)

        _remove_heading_permalinks(main)
        _remove_mkdocstrings_source_blocks(main)
        _replace_highlight_tables_with_pre(main)

        md = _html_to_markdown(str(main))
        md = _strip_leftover_permalink_tokens(md)
        md = _rewrite_internal_links(md)
        md = _collapse_blank_lines(md)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")
        count += 1

    print(f"Exported {count} page(s) to: {OUT_DIR.resolve()}")


if __name__ == "__main__":
    export_site()
