
.. figure:: docs/img/logo_TUM.png
    :width: 200px
    :target: https://gitlab.lrz.de/tum-ens/super-repo
    :alt: Repo logo

==========
ENS Template Repo
==========




**A template repo to kickstart your research projects with best practices in coding, version control, and documentation.**

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


Getting Started
===============
To get started, follow these steps:

Requirements
------------
- Programming language (Python)
- Git for version control (download from https://git-scm.com/)

Installation for local development
----------------------------------
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

#. Our application has dependency on 3dCityDB and Timescale; that's why local environment should be set first. The next command will fetch the timescale and 3dcitydb images and run the containers on your local:

   .. code-block:: bash

    # This will initiate both timescale and 3dcitydb containers on your local machines. 
    docker-compose -f docker-compose.dev.yaml up -d

#. For local development, we need to feed our 3DCityDb. In order to do that please use provided docker-compose file or please ru your own script (Note: If you didn't delete your previous volume, you do not need to run this command again!):

   .. code-block:: bash

    # This has some comments inside please check.
    # Right now we have a simple test.gml file on our repository. We are loading this to work on our locals.
    # Environment variables that are provided in previous step has to match with our env variables (i.e. docker-compose.yaml and docker-compose.import.yaml should have same env vars for db configs)
    docker-compose -f docker-compose.import.yaml up -d

#. While running our application locally, we need to provide environment variable. Please have the same env variables with your docker-compose.dev.yaml file. Environment variables for local development:

   .. code-block:: bash
    
        # TimescaleDB Configuration
        TIMESCALE_USER=
        TIMESCALE_PASSWORD=
        TIMESCALE_HOST=127.0.0.1
        TIMESCALE_PORT=
        TIMESCALE_DB=

        # CityDB Configuration
        CITYDB_USER=
        CITYDB_PASSWORD=
        CITYDB_HOST=127.0.0.1
        CITYDB_PORT=
        CITYDB_DB=

        # General Configuration
        DEBUG=true

#. Now you can start the application:

   .. code-block:: bash

    fastapi dev src/main.py


Installation for docker container
---------------------------------
#. Clone the repository to your local machine:

   .. code-block:: bash

      git clone <repository_url>

#. We need the build image of our database application. To do that please run:

   .. code-block:: bash

    docker-compose build
    
#. Run docker-compose file. The next command will fetch the timescale and 3dcitydb images and run the containers on your machine. It will then start our database (fastapi) application. You may change the env values provided in the compose file:

   .. code-block:: bash

    docker-compose up -d

#. We need to feed our 3DCityDb to test. In order to do that please use provided docker-compose file or please ru your own script (Note: If you didn't delete your previous volume, you do not need to run this command again!):

   .. code-block:: bash

    # Environment variables that are provided in previous step has to match with our env variables (i.e. docker-compose.yaml and docker-compose.import.yaml should have same env vars for db configs)
    docker-compose -f docker-compose.import.yaml up -d


Repository Structure
====================

- **src/**: Main project code. (Rename as needed.)
- **data/**: Data files used in the project. (optional)
- **scripts/**: Utility scripts for data processing, model training, etc. (optional)


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

Open Api Spesifications
============== 
Fastapi provides built in openApi documentation. Please go to following url to see our endpoints: http://127.0.0.1:8000/docs#/


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


