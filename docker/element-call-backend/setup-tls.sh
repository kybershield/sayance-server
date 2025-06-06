#!/bin/bash

# TLS Certificate Setup for Sayance with Element Call
# This script generates self-signed certificates for local development

echo "Setting up TLS certificates for Sayance..."

# Create SSL directory if it doesn't exist
mkdir -p ssl

# Step 1: Create a Root CA key and cert
openssl genrsa -out ssl/sayance-ca.key 2048
openssl req -x509 -new -nodes \
  -days 3650 \
  -subj "/CN=Sayance Dev CA" \
  -key ssl/sayance-ca.key \
  -out ssl/sayance-ca.crt \
  -sha256 -addext "basicConstraints=CA:TRUE"

# Step 2: Create a private key and CSR for *.sayance.localhost
openssl req -new -nodes -newkey rsa:2048 \
  -keyout ssl/sayance.localhost.key \
  -out ssl/sayance.localhost.csr \
  -subj "/CN=*.sayance.localhost"

# Step 3: Sign the CSR with your CA
openssl x509 \
  -req -in ssl/sayance.localhost.csr \
  -CA ssl/sayance-ca.crt -CAkey ssl/sayance-ca.key \
  -CAcreateserial \
  -out ssl/sayance.localhost.crt \
  -days 3650 \
  -sha256 \
  -extfile <( cat <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = sayance.localhost
DNS.3 = *.sayance.localhost
DNS.4 = app.sayance.localhost
DNS.5 = rtc.sayance.localhost
DNS.6 = call.sayance.localhost
EOF
)

# Create symlinks with expected names for nginx
ln -sf sayance.localhost.crt ssl/cert.pem
ln -sf sayance.localhost.key ssl/key.pem

echo "TLS certificates generated successfully!"
echo "Add ssl/sayance-ca.crt to your browser's trusted certificates for HTTPS access"
echo ""
echo "Generated files:"
echo "  - ssl/sayance-ca.crt (Root CA - add to browser)"
echo "  - ssl/sayance.localhost.crt (Server certificate)"
echo "  - ssl/sayance.localhost.key (Server private key)"
echo "  - ssl/cert.pem (Symlink for nginx)"
echo "  - ssl/key.pem (Symlink for nginx)" 