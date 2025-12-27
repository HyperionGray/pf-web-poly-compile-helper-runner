# Security Scanning Quick Reference Guide

## Quick Start

Run all security scans:
```bash
npm run security:all
```

This executes:
1. Credential scanner (checks for hardcoded secrets)
2. Dependency vulnerability checker (npm audit)

## Individual Security Tools

### 1. Credential Scanner

Detects hardcoded secrets, API keys, passwords, and sensitive data.

**Quick scan (recommended):**
```bash
npm run security:scan
```

**Verbose output:**
```bash
npm run security:scan:verbose
```

**Scan specific directory:**
```bash
node tools/security/credential-scanner.mjs /path/to/scan
```

**JSON output (CI/CD):**
```bash
node tools/security/credential-scanner.mjs . --json
```

**What it detects:**
- Generic API keys and secrets
- Passwords
- AWS Access Keys and Secret Keys
- GitHub tokens
- Private keys (RSA, EC, OpenSSH)
- JWT tokens
- Database connection strings
- Service-specific keys (Slack, Google, Stripe, Twilio)
- Basic auth in URLs
- And more...

### 2. Dependency Vulnerability Checker

Checks for known vulnerabilities in project dependencies.

**Check all dependencies:**
```bash
npm run security:deps
```

**Verbose output:**
```bash
npm run security:deps:verbose
```

**JSON output:**
```bash
node tools/security/dependency-checker.mjs --json
```

**Supported ecosystems:**
- Node.js (npm audit)
- Python (pip-audit, if installed)
- Rust (cargo-audit, if installed)

### 3. Security Headers Validator

Validates HTTP security headers on running servers.

**Check development server:**
```bash
npm run security:headers
```

**Check specific URL:**
```bash
node tools/security/security-headers-validator.mjs https://example.com
```

**What it checks:**
- X-Frame-Options (clickjacking protection)
- X-Content-Type-Options (MIME sniffing)
- Strict-Transport-Security (HTTPS enforcement)
- Content-Security-Policy (XSS/injection prevention)
- Referrer-Policy
- Permissions-Policy
- Information disclosure headers

### 4. Web Application Security Scanner

Comprehensive security testing for web applications.

**Using pf tasks:**
```bash
# Full security scan
pf security-scan url=http://localhost:8080

# Scan with verbose output
pf security-scan-verbose url=http://localhost:8080

# JSON output
pf security-scan-json url=http://localhost:8080

# Scan for specific vulnerabilities
pf security-scan-sqli url=http://localhost:8080    # SQL injection
pf security-scan-xss url=http://localhost:8080     # XSS
pf security-scan-critical url=http://localhost:8080 # Critical only

# Fuzzing endpoints
pf security-fuzz url=http://localhost:8080/api
pf security-fuzz-sqli url=http://localhost:8080
pf security-fuzz-xss url=http://localhost:8080

# Complete test suite
pf security-test-all url=http://localhost:8080
```

**Vulnerability types detected:**
- SQL Injection
- Cross-Site Scripting (XSS)
- Cross-Site Request Forgery (CSRF)
- Path Traversal
- OS Command Injection
- XML External Entity (XXE)
- Server-Side Request Forgery (SSRF)
- Security Misconfigurations
- Broken Access Control

## CI/CD Integration

### GitHub Actions

Security scans run automatically on every commit via:
- `.github/workflows/auto-sec-scan.yml`

View results in the Actions tab.

### Local Pre-commit Hook

Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
echo "Running security scans..."
npm run security:all || {
    echo "Security scan failed! Fix issues before committing."
    exit 1
}
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Interpreting Results

### Credential Scanner

**Output:**
```
Scanned 115 files
Total findings: 0

By Severity:
  🔴 Critical: 0
  🟠 High:     0
  🟡 Medium:   0
  🟢 Low:      0

✅ No hardcoded credentials detected!
```

**Action required:**
- **Critical/High:** Immediate action required
- **Medium:** Address in current sprint
- **Low:** Address in next sprint

**If vulnerabilities found:**
1. Review each finding carefully
2. Move secrets to environment variables
3. Use `.env` files (add to `.gitignore`)
4. Consider secret management systems (AWS Secrets Manager, HashiCorp Vault)

### Dependency Checker

**Output:**
```
Total Vulnerabilities: 0

📦 Node.js (npm):
   ✅ Checked - 0 vulnerabilities found
   🔴 Critical: 0
   🟠 High: 0
   🟡 Moderate: 0
   🟢 Low: 0
```

**If vulnerabilities found:**
```bash
# Automatically fix vulnerabilities
npm audit fix

# Fix with breaking changes
npm audit fix --force

# View detailed report
npm audit

# For Python
pip-audit

# For Rust
cargo audit
```

### Security Headers

**Severity levels:**
- **Critical:** Missing essential security headers (CSP, HSTS)
- **High:** Weak or missing protection headers
- **Medium:** Optional but recommended headers
- **Low:** Informational

**Common fixes:**
See `tools/security/security-headers-middleware.mjs` for implementation examples.

## Best Practices

### 1. Regular Scanning

Run security scans:
- ✅ Before every commit (pre-commit hook)
- ✅ During PR review (CI/CD)
- ✅ Weekly full scan (scheduled job)
- ✅ Before releases (release checklist)

### 2. Credential Management

**Never commit:**
- API keys, tokens, passwords
- Private keys, certificates
- Database credentials
- Service account credentials

**Always use:**
- Environment variables
- `.env` files (in `.gitignore`)
- Secret management systems
- Encrypted configuration files

### 3. Dependency Management

**Keep dependencies updated:**
```bash
# Check for outdated packages
npm outdated

# Update dependencies
npm update

# Major version updates
npm install package@latest
```

**Enable Dependabot:**
Create `.github/dependabot.yml`:
```yaml
version: 2
updates:
  - package-ecosystem: npm
    directory: "/"
    schedule:
      interval: weekly
```

### 4. Security Headers

**Production servers must have:**
- `Strict-Transport-Security` (HTTPS only)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY` or `SAMEORIGIN`
- `Content-Security-Policy` (strict policy)
- `Referrer-Policy: strict-origin-when-cross-origin`

### 5. Continuous Monitoring

- Monitor GitHub Security tab
- Review Dependabot alerts
- Check Action workflow results
- Subscribe to security advisories

## Troubleshooting

### Credential Scanner Running Slow

**Problem:** Scanning takes too long on large repositories

**Solution:** Scan specific directories
```bash
# Instead of scanning everything
node tools/security/credential-scanner.mjs .

# Scan only source code
node tools/security/credential-scanner.mjs src
node tools/security/credential-scanner.mjs tools
```

### False Positives

**Problem:** Scanner reports legitimate code as vulnerability

**Solution:** False positive patterns are built-in, but if you encounter issues:
1. Check if it's example code (marked as such)
2. Verify it's not using environment variables
3. File an issue if it's a genuine false positive

### Missing Audit Tools

**Problem:** `pip-audit not installed` or `cargo-audit not installed`

**Solution:**
```bash
# Install pip-audit
pip install pip-audit

# Install cargo-audit
cargo install cargo-audit
```

### CI/CD Failures

**Problem:** Security scan fails in CI/CD

**Solution:**
1. Run locally: `npm run security:all`
2. Fix any vulnerabilities found
3. Commit fixes
4. Verify in CI/CD

## Quick Reference Card

```
┌─────────────────────────────────────────────────────┐
│           SECURITY SCANNING COMMANDS                │
├─────────────────────────────────────────────────────┤
│ All Scans:        npm run security:all              │
│ Credentials:      npm run security:scan             │
│ Dependencies:     npm run security:deps             │
│ Headers:          npm run security:headers          │
│ Web App:          pf security-test-all url=<URL>    │
├─────────────────────────────────────────────────────┤
│ Verbose:          Add :verbose to npm commands      │
│ JSON Output:      Add --json to tool commands       │
├─────────────────────────────────────────────────────┤
│ Fix npm:          npm audit fix                     │
│ Fix Python:       pip-audit                         │
│ Fix Rust:         cargo audit                       │
└─────────────────────────────────────────────────────┘
```

## Resources

- **Implementation Guide:** `docs/AMAZON-Q-REVIEW-IMPLEMENTATION.md`
- **Security Policy:** `docs/security/SECURITY.md`
- **Tool Documentation:**
  - Credential Scanner: `tools/security/credential-scanner.mjs`
  - Dependency Checker: `tools/security/dependency-checker.mjs`
  - Headers Validator: `tools/security/security-headers-validator.mjs`
- **Web Security:** `docs/SECURITY-TESTING.md`

## Support

For security issues:
1. Check documentation
2. Run scans with `--verbose` flag
3. Review tool source code
4. File an issue on GitHub
5. For vulnerabilities, see `SECURITY.md`

---

**Last Updated:** December 26, 2025
**Version:** 1.0.0
