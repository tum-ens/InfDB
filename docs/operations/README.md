# Operations Documentation

This directory contains documentation related to deploying, operating, and maintaining the InfDB system.

## Purpose

The operations documentation provides guidance for DevOps engineers, system administrators, and other technical staff responsible for deploying, monitoring, and maintaining the InfDB system in various environments.

## Contents

- [**CI/CD Guide**](CI_CD_GUIDE.md):  
  Explains how the automated pipelines work, including build, test, and deploy stages. It includes GitLab CI/CD details, environment variables, and job responsibilities.

- [**Deployment**](DEPLOYMENT.md):  
  Step-by-step instructions for deploying InfDB, including Docker Compose usage, environment setup, credentials, and optional services.

## Development vs Operations Guide

### Local Development (development/)
- Setting up local development environment
- Running services locally
- Local testing and debugging
- Using development configurations

### Production Operations (operations/)
- Deploying to production environments
- CI/CD pipeline management
- Production monitoring and maintenance
- Production configuration management

### When to Use Which
- Use development/ when:
  - Setting up your local development environment
  - Making code changes
  - Running tests locally
  - Debugging issues

- Use operations/ when:
  - Deploying to staging/production
  - Setting up CI/CD pipelines
  - Managing production configurations
  - Monitoring production systems

### Common Workflows
- Development → Staging → Production
- Local testing → CI/CD pipeline
- Development configuration → Production configuration