#!/bin/bash
set -e

# This script initializes the PostgreSQL database with correct collation settings
# It's executed by the Docker PostgreSQL image on first startup

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Drop the default database created by postgres container
    DROP DATABASE IF EXISTS sayance;
    
    -- Create the database with proper collation settings
    CREATE DATABASE sayance 
    WITH OWNER = sayance_user
         ENCODING = 'UTF8'
         LC_COLLATE = 'C'
         LC_CTYPE = 'C'
         TEMPLATE = template0;
    
    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE sayance TO sayance_user;
EOSQL

echo "PostgreSQL database 'sayance' initialized with correct collation settings" 