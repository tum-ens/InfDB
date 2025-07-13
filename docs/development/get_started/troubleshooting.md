# Troubleshooting

## Database Issues
  - Ensure containers are running: ``docker ps``
  - Check the current networks in your host in case of any network error ``docker network ls``
  - You should prune your networks, and start from scratch if you have mixed up the configurations ``docker network prune``
  - When you change configuration regarding a docker setup delete the volumes if not applied.
  - Double-check `.env` or `configs/`
  - Verify exposed ports and credentials

## Application Startup 
  - Use Python ≥ 3.10
  - Check missing dependencies
  - Read logs carefully

## Test Data Import
  - Check volumes and paths
  - Run: ``docker-compose logs -f`` to debug
