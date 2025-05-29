# Docker Compose Generation
Auto generates docker-compose file wrt `configs/config_service.yaml`.

# Services
Each service has their own independent service definition under their respective <service_name>.yaml files.
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
      - ${PGADMIN_PORT}:80
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    networks:
      - ${NETWORK_EXTERNAL_NAME}
    depends_on:
      citydb:
        condition: service_healthy
      timescaledb:
        condition: service_healthy
```

# ENV Vars
Env variables are auto generated via  `configs/config_service.yaml`.
`generate_compose.py` file has 2 functionalities.
    1. Generating .env file.
    2. Generating docker-compose file.

Note:
    For our services to communicate between them, they have to be under the same network.
    For this reason we should use the same network name for all of the services.
    If you check under `configs/config_service.yaml`, there is a field called: `network_external_name`.
    This is needed to have mapping between the network name and network definition.
    
    