# Infdb-basedata-ways
This guide explains how to use the `pyinfdb` python package to interact with your InfDB instance.

## Contents

- Objective (Scope, Motivation)
- Usage (Quick Start, Requirements, Configuration)
- Architecture (Design, Implementation)
    - Structure (Project/Code)
    - Data Pipeline
    - Code (Classes and Functions)
    - Dependencies

## Structure
The `pyinfdb` package consists of a superior class InfDB based on the internal classes InDBConfig, InfDBClient, InfDBLogger and InfDBIO as shown in the following figure:
![alt text](demo-figure.png)
The user only interacts with the superior InfDB class, the internal classes are not directly accessible. This abstraction ensures the python interface is consistent despite changes in the internal structure of the package.
It provides functions for database access, configuration management, logging and data handling. The central idea is to provide standard methods to interact with InfDB in order to simplify the interaction with InfDB.

## Installation
pyinfdb is available on [PyPI](https://pypi.org/project/infdb/) and can be installed via pip:
```bash
uv pip install pyinfdb
```

## Quick Start
