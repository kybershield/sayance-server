# PostgreSQL Database Setup

This document outlines the steps to set up a local PostgreSQL database for Sayance.

## Prerequisites

- PostgreSQL installed and running on your machine

## Setup Steps

1. Create the database user:
```bash
psql -c "CREATE USER sayance_user WITH PASSWORD 'secretpassword';" postgres
```

2. Create the database with the user as owner:
```bash
psql -c "CREATE DATABASE sayance OWNER sayance_user;" postgres
```

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