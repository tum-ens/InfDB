# InfDB Documentation

This directory contains all documentation for the InfDB (Infrastructure Database) project. The documentation is organized into several subdirectories, each focusing on a specific aspect of the project.

## Directory Structure

### [architecture/](architecture/)
Contains documentation about the system architecture, including component diagrams, data flow diagrams, and architectural decisions.

### [contributing/](contributing/)
Guidelines and information for contributors to the project, including:
- Code of Conduct
- Contribution workflow
- Release procedures

### [data_formats/](data_formats/)
Specifications and examples of data formats used in the project, including input and output data structures.

### [development/](development/)
Resources for developers working on the project, including:
- Development environment setup
- Workflow guides
- API documentation
- Database schema information

### [guidelines/](guidelines/)
Project guidelines and standards, including:
- Coding guidelines
- Project requirements
- Best practices

### [operations/](operations/)
Documentation related to deploying, operating, and maintaining the system, including:
- CI/CD guides
- Deployment procedures
- Monitoring and logging

### [img/](img/)
Images used throughout the documentation.

### [source/](source/)
Source files for generating documentation, including Sphinx configuration files.

### [build/](build/)
Generated documentation output (not tracked in version control).

## Documentation Standards

When contributing to the documentation:

1. Use Markdown for all internal documentation files except where specific formats are required, e.g. [source](source/) folder for readthedocs.
2. Include a clear title and description at the top of each document.
3. Use relative links when referencing other documentation files.
4. Place images in the `img/` directory and reference them using relative paths.
5. Keep documentation up-to-date with code changes.
6. Follow the Google developer documentation style guide for consistency.

## Building the Documentation

To build the documentation locally:

```bash
# Install documentation dependencies
pip install -r requirements.txt

# Build the documentation
cd docs
make html
```

The built documentation will be available in the `build/html/` directory.
