# Docker Compose Generation
Auto generates docker-compose file wrt `configs/config-service.yml`.

# Services
Each service has their own independent service definition under their respective <service_name>.yml files.
If they have dependencies to other services, this is defined by health check.
As an example pgAdmin:

```bash
services:
  pgadmin:
    image: dpage/pgadmin4
    container_name: pgadmin
    environment:
      - PGADMIN_DEFAULT_EMAIL
      - PGADMIN_DEFAULT_PASSWORD
    ports:
      - ${PGADMIN_EXPOSED_PORT}:${PGADMIN_PORT}
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    networks:
      - ${NETWORK_NAME}
    depends_on:
      citydb:
        condition: service_healthy
      timescaledb:
        condition: service_healthy
```

# ENV Vars
Env variables are auto generated via  `configs/config-service.yml`.
`generate-compose.py` file has 2 functionalities.
    1. Generating .env file.
    2. Generating docker-compose file.

Note:
    For our services to communicate between them, they have to be under the same network.
    For this reason we should use the same network name for all of the services.
    
    