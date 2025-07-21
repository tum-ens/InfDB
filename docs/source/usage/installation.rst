Installation
============

To use InfDB, you first need to set up your environment. This includes downloading the code, creating an isolated Python environment, and installing all required dependencies.

Follow these steps to get started:

1. Install UV Package Manager
-----------------------------

First, install the UV package manager which we'll use for dependency management.

.. code-block:: bash

   # On Linux and macOS
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # By pip (alternative method)
   pip install uv

2. Clone the Repository
-----------------------

Begin by downloading the InfDB source code from the official repository.

.. code-block:: bash

   git clone https://gitlab.lrz.de/tum-ens/need/infdb.git
   cd infdb

3. Set Up a Virtual Environment
-------------------------------

Create a virtual environment using UV to isolate InfDB's dependencies from your system Python.

.. code-block:: bash

   # Create virtual environment (only once)
   uv venv --python 3.12

Activate the environment:

- **Windows**:

  .. code-block:: bash

     venv\Scripts\activate

- **Linux/macOS**:

  .. code-block:: bash

     source venv/bin/activate

4. Install Dependencies
-----------------------

Install all required Python packages using UV and the provided `requirements.txt` file.

.. code-block:: bash

   # Install requirements (only once)
   uv pip install -r requirements.txt

These packages include libraries needed to run the Data Loader, manage configurations, and interact with the backend services such as TimescaleDB and 3DCityDB.
