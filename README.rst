
.. figure:: docs/img/logo_TUM.png
    :width: 200px
    :target: https://gitlab.lrz.de/tum-ens/super-repo
    :alt: Repo logo

==========
ENS Template Repo
==========

**A template repo to kickstart your research projects with best practices in coding, version control, and documentation.**

REMINDER: Remove git history after copying template repo before doing anything else as otherwise the history will be part of the new repo.
==========================================================================================================================================

.. list-table::
   :widths: auto

   * - License
     - |badge_license|
   * - Documentation
     - |badge_documentation|
   * - Development
     - |badge_issue_open| |badge_issue_closes| |badge_pr_open| |badge_pr_closes|
   * - Community
     - |badge_contributing| |badge_contributors| |badge_repo_counts|

.. contents::
    :depth: 2
    :local:
    :backlinks: top

Introduction
============
**ENS Repo Template** provides a standardized structure, tools, and practices to help researchers focus on development while ensuring best practices in coding, version control, and documentation. By using this template, researchers can create organized, maintainable, and collaborative projects that align with modern software engineering standards.

Key Features
------------
- Enforced coding standards and style checks.

- Automated CI/CD workflows for continuous integration.

- Comprehensive documentation setup.


Getting Started
===============
To get started, follow these steps:

Requirements
------------
- Programming language (e.g., Python, R, Julia, etc.)
- Git for version control (download from https://git-scm.com/)

Installation
------------
#. Clone the repository to your local machine:

   .. code-block:: bash

      git clone <repository_url>

#. Set up the virtual environment:

   .. code-block:: bash

      python -m venv venv
      # For Windows
      source venv\Scripts\activate

      # For Linux/MacOS
      source venv/bin/activate


#. Install dependencies:

   .. code-block:: bash

      pip install -r requirements.txt

This template is now ready to use! Follow the repository structure and guidelines below to begin your project.

Repository Structure
====================

- **src/**: Main project code. (Rename as needed.)
- **tests/**: Folder for tests; structured by functionality.
- **docs/**: Documentation source files. Use MkDocs to build and update.
- **examples/**: Example scripts and notebooks.
- **data/**: Data files used in the project. (optional)
- **notebooks/**: Jupyter notebooks for data exploration and analysis. (optional)
- **scripts/**: Utility scripts for data processing, model training, etc. (optional)
- **code_examples/**: Code examples, demonstrating the expected coding style and documentation practices. (Can be removed after the project is set up.)

Usage Guidelines
================

Basic Usage
-----------

Use this template to start new research projects by forking or cloning it. Customize the repository structure and documentation to fit your project's needs.

Basic Workflow
--------------
#. **Open an issue** to discuss new features, bugs, or changes.
#. **Create a new branch** for each feature or bug fix based on an issue.
#. **Write code** and **tests** for the new feature or bug fix.
#. **Run tests** to ensure the code works as expected.
#. **Create a pull request** to merge the new feature or bug fix into the main branch.
#. **Review the code** and **tests** in the pull request.
#. **Merge the pull request** after approval.

Documentation
=============

The documentation is created with Markdown using `MkDocs <https://www.mkdocs.org/>`_. All files are stored in the ``docs`` folder of the repository.

Build the documentation using MkDocs:

.. code-block:: bash

   mkdocs serve

The documentation will be available at http://127.0.0.1:8000/.

CI/CD Workflow
==============

The CI/CD workflow is set up using GitLab CI/CD.
The workflow runs tests, checks code style, and builds the documentation on every push to the repository.
You can view workflow results directly in the repository's CI/CD section.

Contribution and Code Quality
=============================
Everyone is invited to develop this repository with good intentions.
Please follow the workflow described in the `CONTRIBUTING.md <CONTRIBUTING.md>`_.

Coding Standards
----------------
This repository follows consistent coding styles. Refer to `CONTRIBUTING.md <CONTRIBUTING.md>`_ for detailed standards.

Pre-commit Hooks
----------------
Pre-commit hooks are configured to check code quality before commits, helping enforce standards.

Changelog
---------
The changelog is maintained in the `CHANGELOG.md <CHANGELOG.md>`_ file.
It lists all changes made to the repository.
Follow instructions there to document any updates.

License and Citation
====================
| The code of this repository is licensed under the **MIT License** (MIT).
| See `LICENSE <LICENSE>`_ for rights and obligations.
| See the *Cite this repository* function or `CITATION.cff <CITATION.cff>`_ for citation of this repository.
| Copyright: `ens-repo-template <https://gitlab.lrz.de/tum-ens/super-repo>`_ © `TU Munich - ENS <https://www.epe.ed.tum.de/en/ens/homepage/>`_ | `MIT <LICENSE>`_


.. |badge_license| image:: https://img.shields.io/badge/license-MIT-blue
    :target: LICENSE
    :alt: License

.. |badge_documentation| image:: https://img.shields.io/badge/docs-available-brightgreen
    :target: https://gitlab.lrz.de/tum-ens/super-repo
    :alt: Documentation

.. |badge_contributing| image:: https://img.shields.io/badge/contributions-welcome-brightgreen
    :target: CONTRIBUTING.md
    :alt: contributions

.. |badge_contributors| image:: https://img.shields.io/badge/contributors-0-orange
    :alt: contributors

.. |badge_repo_counts| image:: https://img.shields.io/badge/repo-count-brightgreen
    :alt: repository counter

.. |badge_issue_open| image:: https://img.shields.io/badge/issues-open-blue
    :target: https://gitlab.lrz.de/tum-ens/super-repo/-/issues
    :alt: open issues

.. |badge_issue_closes| image:: https://img.shields.io/badge/issues-closed-green
    :target: https://gitlab.lrz.de/tum-ens/super-repo/-/issues
    :alt: closed issues

.. |badge_pr_open| image:: https://img.shields.io/badge/merge_requests-open-blue
    :target: https://gitlab.lrz.de/tum-ens/super-repo/-/merge_requests
    :alt: open merge requests

.. |badge_pr_closes| image:: https://img.shields.io/badge/merge_requests-closed-green
    :target: https://gitlab.lrz.de/tum-ens/super-repo/-/merge_requests
    :alt: closed merge requests
