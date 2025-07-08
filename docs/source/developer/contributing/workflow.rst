Workflow
========

Overview
--------

This document outlines the step-by-step process for contributing to the InfDB project, from setting up your environment to submitting your changes.

Table of Contents
-----------------

1. Setting Up Your Environment
2. Understanding the Issue Tracking System
3. Creating a Feature Branch
4. Making Changes
5. Testing Your Changes
6. Submitting a Merge Request
7. Code Review Process
8. Merging and Closing the Issue

Setting Up Your Environment
---------------------------

Before you can contribute to the InfDB project, you need to set up your development environment:

1. **Clone the repository**:

   .. code-block:: bash

      git clone https://gitlab.lrz.de/tum-ens/need/infdb.git
      cd infdb

2. **Set up your development environment** following the instructions in the :doc:`../development/index`.

3. **Install pre-commit hooks** to ensure code quality:

   .. code-block:: bash

      pip install pre-commit
      pre-commit install

Understanding the Issue Tracking System
---------------------------------------

InfDB uses GitLab's issue tracking system to manage tasks, bugs, and feature requests.

Issue Types
^^^^^^^^^^^

- **Feature Request**: New functionality or enhancements
- **Bug Report**: Something isn't working as expected
- **Documentation Request**: Improvements or additions to documentation
- **Technical Debt**: Code refactoring or improvements

Issue Templates
^^^^^^^^^^^^^^^

When creating a new issue, select the appropriate template:

- Each template provides a structured format to ensure all necessary information is included
- Fill out all required sections to help developers understand the issue

Issue Labels
^^^^^^^^^^^^

Issues are categorized using labels:

- **Priority**: urgent, high, medium, low
- **Type**: feature, bug, documentation, technical-debt
- **Status**: in-progress, review-needed, blocked
- **Component**: api, database, documentation, infrastructure

Creating a Feature Branch
--------------------------

Follow these steps to create a branch for your work.

Branch Naming Convention
^^^^^^^^^^^^^^^^^^^^^^^^

Use the following format: ``type-issue_number-short_description``

- **Type**:
  - ``feature`` for new features
  - ``bugfix`` for bug fixes
  - ``hotfix`` for critical fixes
  - ``docs`` for documentation changes
  - ``refactor`` for code refactoring

- **Issue Number**: The GitLab issue number (without the # symbol)

- **Short Description**: Brief description of the change (use hyphens between words)

Example: ``feature-42-add-energy-balance-calculations``

Creating the Branch
^^^^^^^^^^^^^^^^^^^

1. **Ensure you're on the develop branch**:

   .. code-block:: bash

      git checkout develop
      git pull

2. **Create your feature branch**:

   .. code-block:: bash

      git checkout -b feature-42-add-energy-balance-calculations

Making Changes
--------------

Follow these guidelines when making changes to the codebase.

Coding Standards
^^^^^^^^^^^^^^^^

- Follow the :doc:`../guidelines/coding_guidelines`
- Use consistent code style and formatting
- Write clear, descriptive comments and docstrings
- Follow the domain-specific guidelines for energy system modeling

Commit Best Practices
^^^^^^^^^^^^^^^^^^^^^

- Make small, focused commits that address a single concern
- Write clear commit messages that explain the purpose of the change

Commit message format:

.. code-block:: text

   Short summary of changes (50 chars or less)

   More detailed explanation if necessary. Wrap lines at 72 characters.
   Explain the problem that this commit is solving and why this change
   is the best approach.

   Closes #42

- Include the issue number using "Closes #XX", "Fixes #XX", or "Relates to #XX"

Updating Documentation
^^^^^^^^^^^^^^^^^^^^^^

- Update relevant documentation when making code changes
- Add docstrings to new functions, classes, and methods
- Update the ``CHANGELOG.md`` file with your changes

Testing Your Changes
--------------------

Ensure your changes work as expected and don't break existing functionality.

Running Tests
^^^^^^^^^^^^^

.. code-block:: bash

   # Run all tests
   pytest

   # Run specific test files
   pytest tests/unit/test_models.py

   # Run tests with coverage report
   pytest --cov=src tests/

Writing Tests
^^^^^^^^^^^^^

- Write tests for new functionality
- Update existing tests if necessary
- Aim for high test coverage
- Test edge cases and error conditions

Local Validation
^^^^^^^^^^^^^^^^

Before submitting your changes:

- Run linting tools: ``flake8 src/``
- Format your code: ``black src/``
- Sort imports: ``isort src/``
- Run type checking: ``mypy src/``

Submitting a Merge Request
--------------------------

When your changes are ready for review:

Creating a Merge Request
^^^^^^^^^^^^^^^^^^^^^^^^

1. **Push your branch to GitLab**:

   .. code-block:: bash

      git push -u origin feature-42-add-energy-balance-calculations

2. **Create a Merge Request** in GitLab:
   - Go to the repository on GitLab
   - Click on "Merge Requests" > "New Merge Request"
   - Select your branch as the source and ``develop`` as the target
   - Fill out the merge request template

Merge Request Description
^^^^^^^^^^^^^^^^^^^^^^^^^

Include the following in your merge request description:

- Summary of changes
- Link to the issue being addressed (use "Closes #XX")
- Testing performed
- Screenshots or examples if applicable
- Any special considerations or notes for reviewers

Code Review Process
-------------------

The code review process ensures code quality and knowledge sharing.

Review Guidelines
^^^^^^^^^^^^^^^^^

- Be respectful and constructive in your feedback
- Focus on the code, not the person
- Provide specific suggestions for improvement
- Explain the reasoning behind your suggestions

Addressing Feedback
^^^^^^^^^^^^^^^^^^^

- Respond to all comments
- Make requested changes or explain why you disagree
- Push additional commits to address feedback
- Mark comments as resolved when addressed

Approval Process
^^^^^^^^^^^^^^^^

- At least one approval is required before merging
- CI/CD pipeline must pass
- All discussions must be resolved
- Code must meet the project's quality standards

Merging and Closing the Issue
-----------------------------

Once your merge request is approved:

Merging Process
^^^^^^^^^^^^^^^

1. **Ensure all requirements are met**:
   - All discussions are resolved
   - CI/CD pipeline passes
   - Required approvals are obtained

2. **Merge the changes**:
   - Use "Merge" button in GitLab
   - Select "Delete source branch" option

After Merging
^^^^^^^^^^^^^

- The issue will be automatically closed if you used "Closes #XX" in the merge request description
- If not, manually close the issue with a comment referencing the merge request
- Delete your local feature branch:

  .. code-block:: bash

     git checkout develop
     git pull
     git branch -d feature-42-add-energy-balance-calculations

Celebrating Your Contribution
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Congratulations on your contribution to the InfDB project!  
Your work helps improve the digital twin database for energy infrastructure systems.
