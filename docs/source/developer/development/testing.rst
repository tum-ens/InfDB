Testing
-------

To verify your setup or write new tests:

.. code-block:: bash

   pytest              # Run all tests
   pytest tests/unit   # Unit tests
   pytest --cov=src    # With coverage

Place tests in:

- ``tests/unit/`` — low-level tests
- ``tests/integration/`` — service/db-level tests
- ``tests/e2e/`` — full API interactions
