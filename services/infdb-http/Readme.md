# infdb-http

A simple Nginx-based HTTP file server with Basic Authentication.

## Usage

### Docker Compose

Run the service using Docker Compose:

```bash
docker compose up -d
```

The server will be available at `http://localhost:8080`.

### Configuration

| Environment Variable | Description | Default |
| -------------------- | ----------- | ------- |
| `BASIC_AUTH_USER` | Username for Basic Auth | `user` |
| `BASIC_AUTH_PASSWORD` | Password for Basic Auth | `password` |

### Data

Mount your files to `/usr/share/nginx/html` in the container.

Example `docker-compose.yml` configuration:

```yaml
    volumes:
      - ./your-data:/usr/share/nginx/html
```
