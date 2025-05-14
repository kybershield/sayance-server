# Custom Synapse Deployment Guide

This guide covers how to deploy your custom version of Synapse using Docker Compose with an external PostgreSQL database.

## Prerequisites

- Docker and Docker Compose installed on your server
- A domain name pointing to your server (for production use)
- Port 8008 accessible
- Access to an external PostgreSQL database

## Database Setup

Your PostgreSQL database must be created with the proper collation settings:

```bash
CREATE DATABASE sayance OWNER sayance_user ENCODING 'UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE=template0;
```

These collation settings (`LC_COLLATE='C'` and `TEMPLATE=template0`) are required for proper operation of Matrix Synapse.

## Deployment Steps

1. Copy the entire project (including your modified Synapse source code) to your server.

2. Ensure your `homeserver.yaml` has the correct PostgreSQL connection information:
   ```yaml
   database:
     name: psycopg2
     args:
       user: sayance_user
       password: secretpassword
       dbname: sayance
       host: YOUR_EXTERNAL_DB_HOST  # Replace with your actual PostgreSQL server address
       port: 5432
   ```

3. Make sure the bind_addresses in homeserver.yaml is set to '0.0.0.0' to accept external connections, or a specfic IP if you want restricted access.

4. Build and deploy with Docker Compose:
   ```bash
   cd docker
   docker-compose build  # Builds your custom Synapse image from source
   docker-compose up -d  # Starts the service
   ```

5. Check logs to ensure everything started correctly:
   ```bash
   docker-compose logs -f
   ```

6. Create an admin user (if not already done):
   ```bash
   docker-compose exec synapse register_new_matrix_user http://localhost:8008 -c /data/homeserver.yaml
   ```

## Rebuilding After Changes

If you make changes to the Synapse source code, you'll need to rebuild the image:

```bash
docker-compose build synapse
docker-compose up -d
```

## Production Considerations

For a production environment:

1. Use a reverse proxy (like Nginx) with SSL/TLS certificates
2. Set up proper backup of your PostgreSQL database
3. Consider using a separate media storage solution for the `/data/media` directory
4. Configure proper resource limits for containers
5. Consider using a specific tag/version for your image in production rather than rebuilding frequently

## Troubleshooting

- Check container logs: `docker-compose logs synapse`
- Verify database connection: Test connection to your external PostgreSQL database
- Check Synapse health endpoint: `curl http://localhost:8008/health`
- Build issues: `docker-compose build --no-cache synapse` to rebuild without cache 