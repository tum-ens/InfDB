Installation
============

To use InfDB, you first need to set up your environment. This includes downloading the code, creating an isolated Python environment, and installing all required dependencies.

Follow these steps to get started:

1. Clone the Repository
-----------------------

Begin by downloading the InfDB source code from the official repository.

.. code-block:: bash

   git clone https://gitlab.lrz.de/tum-ens/need/infdb.git
   cd infdb

2. Set Up a Virtual Environment
-------------------------------

Create a virtual environment to isolate InfDB’s dependencies from your system Python.

.. code-block:: bash

   python -m venv venv

Activate the environment:

- **Windows**:

  .. code-block:: bash

     venv\Scripts\activate

- **Linux/macOS**:

  .. code-block:: bash

     source venv/bin/activate

3. Install Dependencies
-----------------------

Install all required Python packages using the provided `requirements.txt` file.

.. code-block:: bash

   pip install -r requirements.txt

These packages include libraries needed to run the Data Loader, manage configurations, and interact with the backend services such as TimescaleDB and 3DCityDB.
