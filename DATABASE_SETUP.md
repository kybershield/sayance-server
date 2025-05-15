# PostgreSQL Database Setup

This document outlines the steps to set up a local PostgreSQL database for Sayance.

## Prerequisites

- PostgreSQL installed and running on your machine

## Setup Steps

1. Create the database user:
```bash
psql -c "CREATE USER sayance_user WITH PASSWORD 'secretpassword';" postgres
```

2. Create the database with the user as owner and proper collation:
```bash
psql -c "CREATE DATABASE sayance OWNER sayance_user ENCODING 'UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE=template0;" postgres
```

   **Important**: The `LC_COLLATE='C'` and `TEMPLATE=template0` settings are required for proper operation of Matrix Synapse. Failing to set these correctly can cause issues with database operations.

3. Grant privileges to the user:
```bash
psql -c "GRANT ALL PRIVILEGES ON DATABASE sayance TO sayance_user;" postgres
```

## Configuration

The database configuration in `homeserver.yaml` should match these credentials:

```yaml
database:
  name: psycopg2
  txn_limit: 10000
  args:
    user: sayance_user
    password: secretpassword
    dbname: sayance
    host: localhost
    port: 5432
    cp_min: 5
    cp_max: 10
```

## Verification

To verify the connection, you can connect to the database using:

```bash
psql -U sayance_user -h localhost -d sayance
```

You will be prompted for the password (`secretpassword`). 

## Troubleshooting

If you encounter connection issues like "Connection refused", make sure:
1. PostgreSQL service is running (`pg_ctl status` or `systemctl status postgresql`)
2. PostgreSQL is configured to allow connections (check `pg_hba.conf`)
3. The host and port in `homeserver.yaml` match your PostgreSQL configuration 