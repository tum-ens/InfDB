Release Procedure
=================

This release procedure outlines the steps for managing releases in the GitLab environment.

Version Numbers
---------------

This software follows the `Semantic Versioning (SemVer) <https://semver.org/>`_.  
It always has the format ``MAJOR.MINOR.PATCH``, e.g., ``1.5.0``.

The data follows the `Calendar Versioning (CalVer) <https://calver.org/>`_.  
It always has the format ``YYYY-MM-DD``, e.g., ``1992-11-07``.

GitLab Release
--------------

1. Update the ``CHANGELOG.md``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **File**: Open the ``CHANGELOG.md`` file and add a new entry under the ``[Unreleased]`` section.
- **Commit**: Note all new features, changes, and fixes in the changelog.
- **Version Entry**: Format the entry like:

  .. code-block:: text

     ## [0.1.0] - 2022-01-01

     ### Added
     - New feature
     - Another new feature

     ### Changed
     - Change to existing feature

     ### Fixed
     - Bug fix

2. Create a Draft GitLab Release Issue
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Use the ``Release_Checklist`` issue template.
- Create an issue titled: ``Release - Minor Version - 0.1.0``
- Fill in the details: name, Git tag, release manager, date.
- Track the workflow using the checklist.

3. Update Version in Code
^^^^^^^^^^^^^^^^^^^^^^^^^

- **File**: Locate the version file (e.g., ``VERSION``).
- **Update**: Change version number using SemVer.
- **Commit**:

  .. code-block:: bash

     git commit -m "Bump version to 1.5.0"

4. Create a Release Branch
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   git checkout develop
   git pull
   git checkout -b release-1.5.0
   git push --set-upstream origin release-1.5.0

5. Finalize and Merge
^^^^^^^^^^^^^^^^^^^^^

- Create a Merge Request from ``release-1.5.0`` into ``main``.
- Assign reviewers and wait for approvals.
- Merge into ``main`` and delete the release branch.

6. Tag the Release
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   git checkout main
   git pull
   git tag -a v1.5.0 -m "Release 1.5.0"
   git push origin v1.5.0

7. Create GitLab Release (Optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Visit the GitLab project’s Releases section.
- Create a release linked to tag ``v1.5.0``.
- Use changelog content as release notes.

8. Update the Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Update version references in documentation.
- Build the documentation and ensure accuracy.
- Deploy if applicable.

.. code-block:: bash

   git add .
   git commit -m "Update docs for v1.5.0"
   git push

- Merge documentation into ``main``.
- Delete the release branch after merge.

9. Merge Back into ``develop``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   git checkout develop
   git pull
   git merge main
   git push

PyPI Release
------------

0. Check Release on Test-PyPI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Visit `https://test.pypi.org/ <https://test.pypi.org/>`_ to verify.
- GitLab CI/CD will automatically publish on pushes to ``release-*`` or ``test-release`` branches.
- Pre-releases only appear under **Release History** on Test-PyPI.
- Use ``bump2version build`` for testing multiple versions.
- Finalize with ``bump2version release`` and push to the ``release-*`` branch.

1. Create and Publish Package on PyPI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Navigate to the repo:

   .. code-block:: bash

      cd path/to/gitlab/group/repo

#. Build the package:

   .. code-block:: bash

      python setup.py sdist

   Confirm that the ``.tar.gz`` file is generated in the ``dist/`` folder.

#. Activate release environment:

   .. code-block:: bash

      source path/to/release_env/bin/activate

#. Upload to PyPI:

   .. code-block:: bash

      twine upload dist/package_name-X.X.X.tar.gz

   Enter your PyPI credentials when prompted.

#. Verify the release on `https://pypi.org/ <https://pypi.org/>`_

#. Celebrate 🎉

Important Notes
---------------

- **Versioning**: Use ``bump2version`` for consistent version increments.
- **Credentials**: Ensure credentials are set via GitLab CI/CD or ``.pypirc``.
- **Troubleshooting**: See `GitLab CI/CD docs <https://docs.gitlab.com/ee/development/cicd/>`_ and `Python packaging docs <https://packaging.python.org/en/latest/>`_.
