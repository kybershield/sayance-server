# Custom Synapse Deployment Guide

This guide covers how to deploy your custom version of Synapse using Docker Compose either with an external PostgreSQL database or with a local PostgreSQL container.

## Prerequisites

- Docker and Docker Compose installed on your server
- A domain name pointing to your server (for production use)
- Port 8008 accessible

## Deployment Options

### Option 1: Local Development with PostgreSQL Container

For local development or testing, you can use the included Docker Compose configuration that sets up both Synapse and PostgreSQL in containers:

```bash
cd docker
chmod +x postgres-init.sh  # Make the initialization script executable
docker-compose -f docker-compose.local.yml up -d
```

This setup:
- Runs Synapse and PostgreSQL in separate containers
- Creates a PostgreSQL database with the proper collation settings (`LC_COLLATE='C'` and `LC_CTYPE='C'`)
- Configures Synapse to connect to the PostgreSQL container
- Stores all data in Docker volumes for persistence

#### Volumes Used:
- `synapse-data`: Synapse configuration and data
- `synapse-keys`: Cryptographic keys for Synapse
- `postgres-data`: PostgreSQL database files

To completely reset the environment (including all data):
```bash
docker-compose -f docker-compose.local.yml down -v
```

### Option 2: Production with External PostgreSQL

For production environments, you may want to use an external PostgreSQL database.

## Database Setup

### External PostgreSQL Setup

Your PostgreSQL database must be created with the proper collation settings:

```bash
CREATE DATABASE sayance OWNER sayance_user ENCODING 'UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE=template0;
```

These collation settings (`LC_COLLATE='C'` and `TEMPLATE=template0`) are required for proper operation of Matrix Synapse.

## Deployment Steps

1. Copy the entire project (including your modified Synapse source code) to your server.

2. Configure the database connection:

   a. For local PostgreSQL container (option 1), ensure `homeserver.yaml` has:
   ```yaml
   database:
     name: psycopg2
     args:
       user: sayance_user
       password: secretpassword
       dbname: sayance
       host: postgres  # This points to the Docker container service name
       port: 5432
   ```

   b. For external PostgreSQL database (option 2), ensure `homeserver.yaml` has:
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

3. Make sure the bind_addresses in homeserver.yaml is set to '0.0.0.0' to accept external connections, or a specific IP if you want restricted access.

4. Build and deploy with Docker Compose:

   a. For local PostgreSQL container:
   ```bash
   cd docker
   docker-compose -f docker-compose.local.yml build  # Builds your custom Synapse image from source
   docker-compose -f docker-compose.local.yml up -d  # Starts the services
   ```

   b. For external PostgreSQL:
   ```bash
   cd docker
   docker-compose build  # Builds your custom Synapse image from source
   docker-compose up -d  # Starts the service
   ```

5. Check logs to ensure everything started correctly:
   ```bash
   docker-compose logs -f  # or docker-compose -f docker-compose.local.yml logs -f
   ```

6. Create an admin user (if not already done):
   ```bash
   docker-compose exec synapse register_new_matrix_user http://localhost:8008 -c /data/homeserver.yaml
   ```

## Switching Between Deployments

To switch from local PostgreSQL to external PostgreSQL:

1. Edit `homeserver.yaml`:
   - Comment out the Docker database configuration section
   - Uncomment or update the external database configuration section
2. Restart Synapse to apply the changes

## Rebuilding After Changes

If you make changes to the Synapse source code, you'll need to rebuild the image:

```bash
docker-compose build synapse
docker-compose up -d
```

Or for the local PostgreSQL setup:
```bash
docker-compose -f docker-compose.local.yml build synapse
docker-compose -f docker-compose.local.yml up -d
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
- Verify database connection: Test connection to your PostgreSQL database
- Check Synapse health endpoint: `curl http://localhost:8008/health`
- Build issues: `docker-compose build --no-cache synapse` to rebuild without cache 