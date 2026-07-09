# Certificate Generation Guide

## Overview

This guide explains how to generate self-signed certificates for local development. Certificates are **NOT** stored in git—generate them locally or in your deployment environment.

---

## Quick Start

```bash
cd certs

# 1. Generate CA private key
openssl genrsa -out ca-key.pem 4096

# 2. Generate CA certificate
openssl req -new -x509 -days 365 -key ca-key.pem -out ca-cert.pem \
  -subj "/CN=LocalExecutionEngine-CA/O=Learning/C=US"

# 3. Generate server private key
openssl genrsa -out server-key.pem 4096

# 4. Generate server certificate request
openssl req -new -key server-key.pem -out server.csr \
  -subj "/CN=localhost/O=Learning/C=US"

# 5. Sign server certificate with CA
openssl x509 -req -in server.csr \
  -CA ca-cert.pem -CAkey ca-key.pem -CAcreateserial \
  -out server-cert.pem -days 365

# 6. Generate additional cert for compatibility (if needed)
cp server-cert.pem cert.pem
cp server-key.pem key.pem
```

---

## File Structure

After generation, your `certs/` directory should contain:

```
certs/
├── ca-key.pem           (Private CA key - KEEP SECRET)
├── ca-cert.pem          (Public CA certificate - SHARE WITH PARTNERS)
├── ca-cert.srl          (Auto-generated serial number)
├── server-key.pem       (Server private key)
├── server-cert.pem      (Server certificate)
├── server.csr           (Certificate signing request)
├── key.pem              (Copy of server-key.pem)
└── cert.pem             (Copy of server-cert.pem)
```

---

## Verification

Verify the certificate chain:

```bash
cd certs
openssl verify -CAfile ca-cert.pem server-cert.pem
```

Expected output:
```
server-cert.pem: OK
```

---

## Certificate Details

| Field | Value |
|-------|-------|
| **Issuer** | CN=LocalExecutionEngine-CA, O=Learning, C=US |
| **Subject** | CN=localhost, O=Learning, C=US |
| **Valid Days** | 365 (1 year) |
| **Key Size** | 4096-bit RSA |

---

## Renewal (After Expiration)

```bash
cd certs

# Regenerate server certificate
openssl req -new -key server-key.pem -out server.csr \
  -subj "/CN=localhost/O=Learning/C=US"

openssl x509 -req -in server.csr -CA ca-cert.pem -CAkey ca-key.pem \
  -CAcreateserial -out server-cert.pem -days 365

# Restart the service
docker compose restart code-executor
```

---

## Security Notes

⚠️ **CRITICAL:**
- **NEVER** commit `ca-key.pem` or `server-key.pem` to git
- **NEVER** share `ca-key.pem` with anyone
- Only share `ca-cert.pem` with partner sites

✅ **SAFE TO SHARE:**
- `ca-cert.pem` — public certificate, safe to distribute

---

## Docker Integration

Certificates are mounted into the container via `docker-compose.yml`:

```yaml
volumes:
  - ./certs:/app/certs:ro
```

The application reads from `/app/certs/` inside the container.

---

## For Development

If you need a fresh set of certificates for development:

```bash
# Remove old certificates
rm certs/*.pem certs/*.srl certs/*.csr

# Regenerate (use commands from Quick Start section)
cd certs
# ... run the openssl commands above
```

---

## Troubleshooting

**"certificate verify failed"**
- Verify the CA and server certificates match: `openssl verify -CAfile ca-cert.pem server-cert.pem`

**"No such file or directory"**
- Ensure you're in the `certs/` directory
- Create the directory if it doesn't exist: `mkdir -p certs`

**"SSL: CERTIFICATE_VERIFY_FAILED" in application**
- Restart Docker container: `docker compose restart code-executor`
- Verify mount path is correct in `docker-compose.yml`

---

For certificate usage in partners systems, see [CA_SETUP_GUIDE.md](../others/CA_SETUP_GUIDE.md).
