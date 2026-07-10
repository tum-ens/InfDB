# Security Policy

## Supported Versions

Only the latest release of InfDB receives security updates. Please make sure you are running the most recent version before reporting a vulnerability.

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public issues.**

Instead, report them privately by email to the maintainer:

- Patrick Buchenberg — patrick.buchenberg@tum.de

Please include as much of the following information as possible:

- A description of the vulnerability and its potential impact
- Steps to reproduce the issue
- Affected version(s) and configuration (e.g. activated services)
- Any suggested mitigation or fix, if known

You will receive an acknowledgement within a few working days. We will keep you informed about the progress of a fix and coordinate the disclosure with you.

## Scope

InfDB orchestrates several third-party services (PostgreSQL/PostGIS, pgAdmin, QGIS Web Client, etc.) via Docker. Vulnerabilities in those upstream projects should be reported to the respective projects; issues in InfDB's configuration or integration of these services are in scope here.

## Default Credentials

The default configuration ships with well-known demo credentials (see `.env.template`). These are intended for local evaluation only — **always change all passwords and secrets before exposing an instance to a network**.
