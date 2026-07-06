# HTTPS CA Setup Guide

## Overview

The Code Execution Engine uses a **self-signed Certificate Authority (CA)** for secure HTTPS communication. Partner sites can trust the CA certificate to avoid untrusted certificate warnings.

---

## Files

```
certs/
├── ca-cert.pem          ← Distribute to partner sites (PUBLIC)
├── ca-key.pem           ← Keep private (DO NOT SHARE)
├── server-cert.pem      ← Server certificate (in container)
├── server-key.pem       ← Server private key (in container)
└── ca-cert.srl          ← CA serial number
```

**⚠️ Security Note:** Only `ca-cert.pem` should be shared with partners. Keep `ca-key.pem` secret.

---

## For Partner Sites - How to Trust the CA

### Option 1: Python/Node.js/JavaScript (Recommended)

**Python:**
```python
import requests
import certifi
from pathlib import Path

# Add CA cert to trusted store
ca_bundle = certifi.where()
with open(ca_bundle, 'a') as f:
    with open('path/to/ca-cert.pem', 'r') as ca:
        f.write(ca.read())

# Or use requests directly
response = requests.post(
    'https://localhost:7998/execute',
    headers={'X-API-Key': 'your-key'},
    json={...},
    verify='path/to/ca-cert.pem'  # Use the CA cert
)
```

**Node.js/JavaScript:**
```javascript
const https = require('https');
const fs = require('fs');

const caCert = fs.readFileSync('path/to/ca-cert.pem');

const options = {
    hostname: 'localhost',
    port: 7998,
    path: '/execute',
    method: 'POST',
    headers: {
        'X-API-Key': 'your-key',
        'Content-Type': 'application/json'
    },
    ca: caCert  // Use the CA cert
};

const req = https.request(options, (res) => {
    // Handle response
});
```

**Curl:**
```bash
curl --cacert ca-cert.pem \
  -X POST https://localhost:7998/execute \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

---

### Option 2: OS Trust Store (Windows)

1. Press `Win+R`, type `certmgr.msc`
2. Navigate to **Trusted Root Certification Authorities** → **Certificates**
3. Right-click → **All Tasks** → **Import**
4. Select `ca-cert.pem`
5. Click **Next** → **Place in: Trusted Root Certification Authorities**
6. Finish

Now all applications on Windows will trust this CA.

---

### Option 3: OS Trust Store (macOS)

```bash
# Add CA to system keychain
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ca-cert.pem

# Verify
security find-certificate -c "LocalExecutionEngine-CA" /Library/Keychains/System.keychain
```

---

### Option 4: OS Trust Store (Linux)

**Ubuntu/Debian:**
```bash
sudo cp ca-cert.pem /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

**RedHat/CentOS:**
```bash
sudo cp ca-cert.pem /etc/pki/ca-trust/source/anchors/
sudo update-ca-trust
```

---

### Option 5: Docker Container (for container-to-container calls)

```dockerfile
FROM python:3.11

# Copy CA cert
COPY ca-cert.pem /etc/ssl/certs/

# Update system certs (Linux)
RUN update-ca-certificates

# Your application can now trust the CA
CMD ["python", "app.py"]
```

---

## Certificate Details

```
Issuer:      CN=LocalExecutionEngine-CA, O=Learning, C=US
Subject:     CN=localhost, O=Learning, C=US
Valid From:  2026-07-05 16:27:35 UTC
Valid Until: 2027-07-05 16:27:35 UTC (1 year)
Key Size:    4096-bit RSA
```

---

## Testing

### Verify certificate chain:
```bash
openssl verify -CAfile ca-cert.pem certs/server-cert.pem
```

### Test HTTPS connection with CA:
```bash
curl --cacert ca-cert.pem https://localhost:7998/health
```

### Expected output:
```json
{"status": "running"}
```

---

## Renewal

Certificates expire after **1 year**. To renew:

```bash
cd certs

# Regenerate server certificate
openssl req -new -key server-key.pem -out server.csr \
  -subj "/CN=localhost/O=Learning/C=US"

openssl x509 -req -in server.csr -CA ca-cert.pem -CAkey ca-key.pem \
  -CAcreateserial -out server-cert.pem -days 365

# Restart container
docker compose restart code-executor
```

---

## Troubleshooting

**"certificate verify failed"**
- Ensure `ca-cert.pem` is in the correct path
- Verify certificate chain: `openssl verify -CAfile ca-cert.pem server-cert.pem`

**"SSL: CERTIFICATE_VERIFY_FAILED"**
- Python: Use `requests.post(..., verify='ca-cert.pem')`
- Node.js: Pass `ca: fs.readFileSync('ca-cert.pem')`

**"curl: (60) SSL certificate problem"**
- Use `curl --cacert ca-cert.pem <url>`

---

## Distribution Checklist

- [ ] Copy `certs/ca-cert.pem` to partner sites
- [ ] Provide this guide to partners
- [ ] Test partner integration with CA cert installed
- [ ] Document partner endpoint in integration guide

---

For questions, contact: roopesht@gmail.com
