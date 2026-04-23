---
icon: material/notebook
---
# Jupyter Notebook :material-notebook:

Jupyter Notebook allows you to interactively work with the data by running Python scripts and visualize results directly within your browser. It is an excellent tool for data exploration and prototyping. More information can be found on the official [Website](https://jupyter.org/).

## Configuration

The configuration is managed via environment variables:

```bash title=".env"
# ==============================================================================
# SERVICE ACTIVATION
# ==============================================================================
# Select profiles to activate
COMPOSE_PROFILES=...,notebook,...  # (1)

# ==============================================================================
# JUPYTER NOTEBOOK (Development Environment)
# ==============================================================================
# Profile: notebook

# Port to expose Jupyter on the host machine
SERVICES_JUPYTER_EXPOSED_PORT=8888 # (2)

# Enable Jupyter Lab interface (yes/no)
SERVICES_JUPYTER_ENABLE_LAB=yes

# Authentication token for Jupyter
SERVICES_JUPYTER_TOKEN=infdb # (3)

# Path to notebook files
SERVICES_JUPYTER_PATH_BASE=..src/notebooks/
```

1.  **Activate service**: The `notebook` profile must be included to activate the Jupyter service.
2.  **Port**: The port on which Jupyter is available.
3.  **Token**: The token used for authentication (default: `infdb`).

## Access

If you activate the service, it should be available on the default port `SERVICES_JUPYTER_EXPOSED_PORT=8888` via your browser:

=== "Local"
    http://localhost:8888

=== "Remote"
    http://IP-ADDRESS-OF-HOST:8888
