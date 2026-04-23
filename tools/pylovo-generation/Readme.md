# pylovo synthetic low-voltage grid generation

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [License and Citation](#license-and-citation)
- 
## Overview

This tool generates synthetic low-voltage grids based on the building and ways basedata schema in infdb.
For further information, please refer to the [pylovo documentation](https://github.com/tum-ens/pylovo).
**Use Cases:**
- Analyse impacts of DERs on voltages in existing LV grid structures
- Analyse grid reinforcement vs asset optimization e.g. with HEMS
- Analyse large-scale low-voltage grid regions and their influence on higher voltage levels

## Prerequisites

Before using this tool, ensure you have:

- infDB instance running (see [infDB documentation](https://tum-ens.github.io/InfDB/))
- Docker and Docker Compose installed
- If the pylovo submodules is empty or out of sync, use ``git submodule update --init --recursive`` to initialize and update it.

## Configuration
tbd

### Getting Help

If you encounter issues:
1. Check the logs for error messages
2. Verify configuration settings
3. Ensure infDB is running and accessible
4. Review the [troubleshooting section in infDB docs](https://tum-ens.github.io/InfDB/)
5. Open an issue on the repository

## License and Citation

This tool is licensed under the **MIT License** (MIT).  
See [LICENSE](LICENSE) for rights and obligations.  
See the *Cite this repository* function or [CITATION.cff](CITATION.cff) for citation.

Copyright (c) 2025 Technical University of Munich - Chair of Renewable and Sustainable Energy Systems

---

**Part of the infDB ecosystem**: [https://tum-ens.github.io/InfDB/](https://tum-ens.github.io/InfDB/)
