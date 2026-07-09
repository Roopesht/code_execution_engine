# Open Source Readiness Checklist

## Pre-Release Requirements

### 1. Remove Certificates from Git History
**Status:** ⏳ Pending

```bash
# Remove certificate files from git tracking
git rm --cached certs/*.pem certs/*.srl certs/*.csr

# Verify removal
git status
```

**Files Removed:**
- `certs/ca-key.pem` (private key)
- `certs/key.pem` (private key)
- `certs/server-key.pem` (private key)
- `certs/ca-cert.pem`
- `certs/cert.pem`
- `certs/server-cert.pem`
- `certs/server.csr`

---

### 2. Update .gitignore
**Status:** ⏳ Pending

Add to `.gitignore`:
```
certs/
```

---

### 3. Verify .env Configuration
**Status:** ✅ Complete

- `.env` is already in `.gitignore`
- `.env.example` exists with dummy values
- No secrets will be committed

---

### 4. Commit Changes
**Status:** ⏳ Pending

```bash
git add .gitignore
git commit -m "Remove certificates from git history and add certs/ to gitignore"
```

---

### 5. Generate Certificates Locally
**Status:** ⏳ Pending (After git history is clean)

Developers cloning the repo must generate certificates locally. See [CERTIFICATE_GENERATION.md](CERTIFICATE_GENERATION.md) for step-by-step instructions.

**Quick reference:**
```bash
cd certs

# Generate CA and server certificates
openssl genrsa -out ca-key.pem 4096
openssl req -new -x509 -days 365 -key ca-key.pem -out ca-cert.pem \
  -subj "/CN=LocalExecutionEngine-CA/O=Learning/C=US"
openssl genrsa -out server-key.pem 4096
openssl req -new -key server-key.pem -out server.csr \
  -subj "/CN=localhost/O=Learning/C=US"
openssl x509 -req -in server.csr -CA ca-cert.pem -CAkey ca-key.pem \
  -CAcreateserial -out server-cert.pem -days 365
cp server-cert.pem cert.pem && cp server-key.pem key.pem
```

---

## Verification

```bash
# Ensure no certificates are tracked
git ls-files | grep -E '\.(pem|key|crt|pfx|p12|srl)$'

# Should return empty

# Verify certificate chain
cd certs && openssl verify -CAfile ca-cert.pem server-cert.pem
# Expected: server-cert.pem: OK
```

Once completed, the project is ready for public release.
