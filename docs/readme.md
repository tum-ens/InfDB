# Project Documentation

This project uses [Sphinx](https://www.sphinx-doc.org/) for documentation, which is built and published automatically on [Read the Docs](https://readthedocs.org/).

## 🛠️ Setup

To build the documentation locally:

1. Navigate to the `docs` folder:

    ```bash
    cd docs
    ```

2. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Building Locally

To build the HTML version of the documentation manually:

```bash
make html
```

## To automatically rebuild and serve the documentation with live reloading (suggested to use)
Assuming that you are already in /docs directory:

```bash
sphinx-autobuild source/ source/_build/html --port 9000
```

This will start a local server at http://localhost:9000. I do not suggest 8000 since it is a common port for many services.

## 📖 Documentation Standards

When contributing to the documentation:

1. Use **Markdown** for all internal documentation files, **except** where specific formats like reStructuredText (`.rst`) are required (e.g., in the `source/` folder for Read the Docs).
2. Always include a **clear title and description** at the top of each document.
3. Use **relative links** when referencing other files.
4. Place images in the `img/` directory and reference them using relative paths.
5. Keep documentation in sync with code and implementation changes.
6. Follow the [Google developer documentation style guide](https://developers.google.com/style) for writing standards.

## 📂 Folder Structure

- ``docs/source/`` is used by `Sphinx <https://www.sphinx-doc.org/>`_ to refer to the **source files for documentation**. These are the reStructuredText (``.rst``) or Markdown (``.md``) files that Sphinx processes to generate output formats like HTML or PDF.

For example:
- The official `Sphinx RTD tutorial <https://sphinx-rtd-tutorial.readthedocs.io/en/latest/folders.html>`_ follows this pattern.
- The accompanying repository `simpleble <https://github.com/sglvladi/simpleble>`_ stores its documentation in a ``docs/source/`` directory as well.

In our project:

- The documentation "source" is made up of subfolders like ``user/``, ``developer/``, and ``changelog/``.

Following this convention:
- Keep static assets like images (``img/``) and stylesheets (``css/``) at the same level as ``source/``, enabling shared use across multiple documentation sections.


A quick overview of the documentation directory structure:

- `docs/` – Root directory for all documentation-related files.
- `docs/css/` – Contains custom CSS files for theming the generated HTML.
- `docs/img/` – Holds images used throughout the documentation.
- `docs/data_formats/` – (Optional) Reference or example data files used in docs.
- `docs/source/` – Main Sphinx source folder for `.rst` files and configuration.
- `docs/source/_build/` – Output directory where built documentation (HTML, PDF, etc.) is generated.
- `docs/source/changelog/` – Contains version history or release notes.
- `docs/source/developer/` – Developer-focused documentation (architecture, CI/CD, contribution guidelines).
  - `api/` – Development guide for the API structure.
  - `architecture/` – System-level architecture and design docs.
  - `ci_cd/`, `repository/`, `services/`, `workflow/`, etc. – Internal guides and module-specific details.
- `docs/source/user/` – User-facing documentation (API usage, architecture explanation, service access).
  - `api/`, `architecture/`, `services/` – User-accessible functionality and how to interact with it.
- `docs/source/index.rst` – Root entry file for the entire Sphinx documentation.
- `docs/source/conf.py` – Sphinx configuration file (theme, extensions, source paths, etc.).
- `Makefile` / `make.bat` – Build scripts for generating documentation (e.g., `make html`).
- `requirements.txt` – Python dependencies required to build the documentation.
- `readme.md` – This Markdown file with setup instructions and structure overview.