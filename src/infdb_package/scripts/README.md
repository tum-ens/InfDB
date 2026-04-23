# Scripts Makefile

This directory contains a `Makefile` that automates:

1) generating API markdown files  
2) building the MkDocs site  
3) exporting the built HTML pages back into Markdown

## Libraries needed

### `scripts/gen_api_docs.py`

**Standard library only:**
- `pathlib`

No third-party libraries are required for this script.

### `scripts/export_site_to_md.py`

**Standard library:**
- `re`
- `pathlib`
- `typing`

**Third-party libraries:**
- `beautifulsoup4` (imports: `bs4.BeautifulSoup`, `bs4.Tag`)
- `html2text` (imports: `markdownify.markdownify`)

Install them with:

```bash
python3 -m pip install beautifulsoup4 markdownify
```

> Note: the `build` step uses MkDocs, so you also need `mkdocs` plus any plugins
> referenced in `mkdocs.yml` (for example: `mkdocs-material`, `mkdocstrings`,
> `mkdocs-gen-files`, `mkdocs-literate-nav`, etc.).

## Docstring style for new functions

All new Python functions/classes should use **Google-style docstrings** so they
render correctly with `mkdocstrings` (`docstring_style: google`).

Example:

```python
from typing import Optional

def add_user(name: str, age: int, nickname: Optional[str] = None) -> int:
    """Create a user record.

    Args:
        name: Full name of the user.
        age: Age in years.
        nickname: Optional display nickname.

    Returns:
        The numeric ID of the created user.

    Raises:
        ValueError: If `age` is negative.
    """
    if age < 0:
        raise ValueError("age must be non-negative")
    return 123
```

## Makefile keywords

### Variables

- `PYTHON := python3`  
  Python executable used by the Makefile.

- `MKDOCS := $(PYTHON) -m mkdocs`  
  Runs MkDocs using the selected Python interpreter.

### Targets

- `all`  
  Default target. Runs: `gen`, `build`, then `export`.

- `gen`  
  Generates API reference markdown files under `../docs/api/` and writes
  `../docs/api/SUMMARY.md`.

- `build`  
  Builds the MkDocs site using `../mkdocs.yml`. Output goes to `../site/`.

- `serve`  
  Runs the MkDocs using `../mkdocs.yml`. Serving on http://127.0.0.1:8000/.


- `export`  
  Exports content from `../site/` (HTML) to Markdown under `../documentation/`.

- `clean`  
  Removes generated directories:
  - `../docs`
  - `../site`
  - `../documentation`

## How to run

Run commands from the `scripts/` directory:

```bash
make
```

Run a single step:

```bash
make gen
make build
make export
```

Clean everything generated:

```bash
make clean
```

## Output summary

- `make gen` → `../docs/api/*.md` and `../docs/api/SUMMARY.md`
- `make build` → `../site/`
- `make export` → `../documentation/`
