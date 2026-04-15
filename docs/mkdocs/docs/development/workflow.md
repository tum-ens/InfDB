# Workflow
Please follow the development workflow outlined below when contributing to the infDB project:

0. **Set up the environment** following the installation instructions in [Usage -> Get Software](../usage/get-software.md).
1. **Open an issue** to discuss new features, bugs, or changes.
2. **Create a new branch** for each feature or bug fix based on an issue.
3. **Implement the changes** following the [coding guidelines](../development/guidelines/coding-standards.md).
4. **Write tests** for new functionality or bug fixes.
5. **Run tests** to ensure the code works as expected.
6. **Create a merge request** to integrate your changes.
7. **Address review comments** and update your code as needed.
8. **Merge the changes** after approval.


## Developing in a Container
We recommend using Visual Studio Code with the Remote - Containers extension for development of the services. This allows you to work in a consistent environment that matches the production setup.

1. Install the [Remote - Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) in Visual Studio Code.
2. Open the corresponding tool or service folder in Visual Studio Code.
3. Click on the green icon in the bottom-left corner and select "Reopen in Container".
4. The development container will be built and launched, providing you with a ready-to-use environment for development.
!!! hint
    If you want to develop a tool or a service, you need to open the specific tool or service folder (e.g., `services/infdb-api/`) instead of the root project folder.

<!-- ## CI/CD Workflow

The CI/CD workflow is set up using GitLab CI/CD. The workflow runs tests, checks code style, and builds the documentation on every push to the repository. You can view workflow results directly in the repository's CI/CD section. For detailed information about the CI/CD workflow, see the [CI/CD Guide](docs/operations/CI_CD_Guide.md). -->

!!! warning "Troubleshooting on Windows"
    To open the repository in Visual Studio Code (VSC) click the two arrowheads in the lower left corner of VSC and select "Connect to WSL". Then you can open the repository folder from for Linux home directory.

This section summarizes some problems encountered during the first installation and startup of infDB on Windows, along with their solutions.

**1. Ubuntu launched as root instead of Normal User**

- Problem: WSL launched Ubuntu as the root user. May lead to problems while executing commands.
- Cause: No default user was configured during first installation.
- Solution:
```bash
adduser username
```

Set the default user:
```bash
#ubuntu 
config --default-user username
```

Restart WSL:
```bash
wsl --shutdown
```

**2. Docker Command Not Found in WSL2**

- Problem:
The command 'docker' could not be found in this WSL2 distro.

- Cause:
Docker Desktop installed, but WSL integration disabled.

- Fix:
Enable Docker & WSL integration:

Docker Desktop → Settings → Resources → WSL Integration

Enable integration with Ubuntu.
After enabling, check via:
```bash
#ubuntu 

docker version
```
**3. Docker Permission Denied**

- Problem:
permission denied while trying to connect to the Docker daemon socket

- Cause:
Logged in user was not part of the docker group.

- Fix:
```bash
#ubuntu 
sudo usermod -aG docker username
```
Restart WSL:
```bash
#ubuntu 
wsl –shutdown
```

