---
icon: material/download
---

!!! warning
    All commands need to be executed on **macOS or Linux**. 

## Local Folder Structure
The InfDB allows a modular folder structure to manage multiple database instances independently. Each instance represents a separate deployment with its own data, configuration, and services—ideal for handling different regions, projects, or environments.


!!! example
        infdb/
        ├── infdb-demo/
        ├── muenchen/
        ├── koeln/
        ├── waermeliniendichte/
        ├── netzplanung/
        └── ...
    The recommended structure places all instance data in docker managed volumes while keeping each instance's configuration and tools in separate directories (e.g. by region `muenchen/`, `koeln/`). This approach simplifies backups, migrations, and multi-instance management.

First of all, create the main `infdb` directory and navigate into it:
```bash
mkdir infdb
cd infdb
```


!!! warning "Windows Users"
    Create this directory to your Ubuntu home directory to have the following path:
    ````
    \\wsl.localhost\Ubuntu\home\[PC username]\infdb
    ````
    (in file explorer Windows shows \\wsl.localhost as Linux) and execute scripts from Linux terminal (search for Ubuntu in applications)


## Clone InfDB
Then, you can clone the repository into this new directory either with SSH or HTTPS as you like:

You can either use **SSH** or **HTTPS**:

- **SSH** (Secure Shell) uses cryptographic key pairs for authentication. Once set up, you won't need to enter credentials for each operation. Recommended for frequent Git operations. 
- **HTTPS** uses username and password (or personal access token) for authentication. Simpler to set up initially but may require credentials for each operation unless you configure credential caching.

=== "SSH"
    ``` bash
    # Replace "infdb-demo" by name of instance 
    git clone --recurse-submodules git@github.com:tum-ens/InfDB.git infdb-demo
    ```

=== "HTTPS"
    ```bash
    # Replace "infdb-demo" by name of instance
    git clone --recurse-submodules https://github.com/tum-ens/InfDB.git infdb-demo
    ```

Both methods are secure and work identically for cloning, pushing, and pulling. Your choice depends on your workflow preferences and environment constraints.

Navigate to the instance directory:
```bash
cd infdb-demo
```