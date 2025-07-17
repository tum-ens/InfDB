# Release Procedure

This release procedure outlines the steps for managing releases in the GitLab environment.<br>
These symbols help with orientation:
- 🐙 GitLab/GitHub
- 💠 git (Bash)
- 📝 File
- 💻 Command Line (CMD)

**NOTE:** This release procedure is the standard release procedure and will need to be updated in the future according to
best-practice DevOps procedures. A new release draft can be found at the bottom of the file.

## Version Numbers

This software follows the [Semantic Versioning (SemVer)](https://semver.org/).<br>
It always has the format `MAJOR.MINOR.PATCH`, e.g. `1.5.0`.

The data follows the [Calendar Versioning (CalVer)](https://calver.org/).<br>
It always has the format `YYYY-MM-DD`, e.g. `1992-11-07`.


## GitLab Release

### 1. Update the `CHANGELOG.md`
- 📝 **File**: Open the CHANGELOG.md file and add a new entry under the `[Unreleased]` section.
- 💠 **Commit**: Commit your changes to the changelog, noting all new features, changes, and fixes.
- 📝 **Version Entry**: Format the new version entry as follows:
    ```
    ## [0.1.0] - 2022-01-01
  
    ### Added
    - New feature
    - Another new feature
  
    ### Changed
    - Change to existing feature
  
    ### Fixed
    - Bug fix
    ```
  
### 2. Create a `Draft GitLab Release` Issue
- 🐙 **Template**: Use the `📝Release_Checklist` template for the issue.
- 🐙 **Issue**: Create a new issue in the repository with the title `Release - Minor Version - 0.1.0`.
- 🐙 **Description**: Fill in the details of the release, including the name, Git tag, release manager, and date.
- 🐙 **Workflow Checklist**: Check off the steps in the workflow checklist for the release.
  
### 3. Update Version in Code
- 📝 **File**: Locate the version variable in the code (in the template it can be found in [VERSION](VERSION)).
- 💻 **Update**: Change the version number to the new release version following SemVer.
- 💠 **Commit**: Commit this version change with a message like:
    ```
    git commit -m "Bump version to 1.5.0"
    ```

### 4. Create a Release Branch
- 💠 **Branching**: Create a release branch from develop:
    ```bash
    git checkout develop
    git pull
    git checkout -b release-1.5.0
    ```
- 💠 **Push**: Push the release branch to GitLab:
    ```bash
    git push --set-upstream origin release-1.5.0
    ```
  
### 5. Finalize and Merge
- 🐙 **Merge Request**: In GitLab, open a merge request (MR) from `release-1.5.0` into `main`.
- 🐙 **Review**: Assign reviewers to the MR and ensure all tests pass.
- 🐙 **Merge**: Once approved, merge the MR into main and delete the release branch.

### 6. Tag the Release
- 💠 **Checkout** main: Ensure you’re on the main branch.
    ```bash
    git checkout main
    git pull
    ```
- 💠 **Tag**: Tag the new release in GitLab:
    ```bash
    git tag -a v1.5.0 -m "Release 1.5.0"
    git push origin v1.5.0
    ```
  
### 7. Create a GitLab Release
- 🐙 **GitLab Release Page**: Go to the GitLab project’s Releases section and create a new release linked to the v1.5.0 tag.
- 📝 **Release Notes**: Add release notes using information from the changelog.
- 🐙 **GitHub**: Create a release on the GitHub page as well

### 8. Update the Documentation
- 📝 **Documentation**: Update the documentation to reflect the new release version.
- 💻 **Build**: Build the documentation to ensure it’s up to date.
- 💻 **Deploy**: Deploy the documentation to the appropriate location.
- 💻 **Update**: Update any version references in the documentation.
- 💻 **Commit**: Commit the documentation changes.
- 💠 **Push**: Push the documentation changes to the repository.
- 🐙 **Merge**: Merge the documentation changes into the main branch.
- 🐙 **Delete Branch**: Delete the release branch after merging.

### 9. Merge Back into `develop`
- 💠 **Branch**: Create an MR from `main` into `develop` to merge the release changes back into the development branch.
```bash
git checkout develop
git pull
git merge main
git push
```

## Docker Release

### 1. Prepare Docker Configuration
- 📝 **Dockerfile**: Ensure your Dockerfile is optimized for production:
    - Use multi-stage builds to minimize image size
    - Use specific base image versions (not `latest`)
    - Set non-root user for security
    - Include health checks for database connectivity
- 📝 **docker-compose.yml**: Update production docker-compose file with:
    - Proper volume mounts for data persistence
    - Environment variable configurations
    - Network security settings
    - Resource limits (memory, CPU)

### 2. Build and Test Docker Images
- 💻 **Local Build**: Build the Docker image locally with the new version:
    ```bash
    docker build -t your-db-tool:v1.5.0 .
    docker build -t your-db-tool:latest .
    ```
- 💻 **Test Image**: Run comprehensive tests on the Docker image:
    ```bash
    docker run -d --name test-db-tool your-db-tool:v1.5.0
    docker exec test-db-tool /app/tests/health-check.sh
    ```
- 💻 **Security Scan**: Scan the image for vulnerabilities:
    ```bash
    docker scout cves your-db-tool:v1.5.0
    ```

### 3. Configure Container Registry
- 🐙 **GitLab Container Registry**: Ensure GitLab Container Registry is enabled
- 💻 **Authentication**: Login to the registry:
    ```bash
    docker login registry.gitlab.com
    ```
- 📝 **CI/CD Variables**: Set required environment variables in GitLab:
    - `DOCKER_REGISTRY_URL`
    - `DOCKER_IMAGE_NAME`
    - `DOCKER_REGISTRY_USER`
    - `DOCKER_REGISTRY_PASSWORD`

### 4. Tag and Push Images
- 💻 **Tag Images**: Tag images for the registry:
    ```bash
    docker tag your-db-tool:v1.5.0 registry.gitlab.com/your-group/your-db-tool:v1.5.0
    docker tag your-db-tool:v1.5.0 registry.gitlab.com/your-group/your-db-tool:latest
    ```
- 💻 **Push Images**: Push to GitLab Container Registry:
    ```bash
    docker push registry.gitlab.com/your-group/your-db-tool:v1.5.0
    docker push registry.gitlab.com/your-group/your-db-tool:latest
    ```

### 5. Update Deployment Configurations
- 📝 **Kubernetes Manifests**: Update deployment YAML files with new image version
- 📝 **Helm Charts**: Update `values.yaml` with new image tag
- 📝 **Docker Compose**: Update production compose files
- 📝 **Environment Files**: Update `.env` files with new version references

### 6. Database Migration Considerations
- 💻 **Migration Scripts**: Ensure database migration scripts are included in the image
- 💻 **Backup Strategy**: Document backup procedures before deployment
- 💻 **Rollback Plan**: Prepare rollback procedures for database schema changes
- 💻 **Health Checks**: Configure proper health checks for database connectivity

### 7. Production Deployment
- 🐙 **Staging Deployment**: Deploy to staging environment first:
    ```bash
    docker-compose -f docker-compose.staging.yml up -d
    ```
- 💻 **Validation**: Run integration tests against staging deployment
- 🐙 **Production Deployment**: Deploy to production using CI/CD pipeline
- 💻 **Monitor**: Monitor application logs and metrics post-deployment

### 8. Documentation Updates
- 📝 **Docker Hub**: Update Docker Hub repository description and documentation
- 📝 **Installation Guide**: Update installation instructions with new image versions
- 📝 **Configuration Guide**: Update environment variable documentation
- 📝 **Troubleshooting**: Update troubleshooting guide with known issues

### 9. Cleanup and Maintenance
- 💻 **Old Images**: Clean up old Docker images from local and registry:
    ```bash
    docker image prune -a
    ```
- 🐙 **Registry Cleanup**: Configure GitLab Container Registry cleanup policies
- 💻 **Security Updates**: Schedule regular base image updates for security patches

## Improved Release Flow (DRAFT)

### Pre-Release (Automated)
1. **Quality Gates**: All tests pass, code coverage meets threshold
2. **Security Scanning**: Dependency and vulnerability scans pass
3. **Feature Freeze**: No new features merged to `develop`

### Release Process
1. **Create Release Branch**: `git checkout -b release-1.5.0` from `develop`
2. **Version Bump**: Use `bump2version` or similar tool
3. **Update Changelog**: Finalize changelog entries
4. **Release Testing**: Run full test suite on release branch
5. **Create Release MR**: `release-1.5.0` → `main`
6. **Approval Process**: Require approvals from maintainers
7. **Merge to Main**: After approval, merge and auto-tag
8. **Immediate Merge Back**: Auto-merge `main` → `develop`
9. **Automated Deployment**: CI/CD handles Docker builds and deployments

### Post-Release
1. **Monitoring**: Track metrics and error rates
2. **Documentation**: Auto-update docs from release notes
3. **Cleanup**: Remove release branch after successful deployment
