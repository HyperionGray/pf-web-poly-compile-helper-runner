# Security Configuration Guide

This guide provides comprehensive instructions for configuring security features in the pf-web-poly-compile-helper-runner project.

## Table of Contents

1. [API Server Security](#api-server-security)
2. [CORS Configuration](#cors-configuration)
3. [Rate Limiting](#rate-limiting)
4. [Environment Variables](#environment-variables)
5. [Security Headers](#security-headers)
6. [Input Validation](#input-validation)
7. [Best Practices](#best-practices)
8. [Security Scanning](#security-scanning)

---

## API Server Security

### Overview

The API server (`tools/api-server.mjs`) includes built-in security features:

- **Rate Limiting:** Prevents abuse and DoS attacks
- **CORS Protection:** Controls cross-origin access
- **Input Validation:** Sanitizes and validates all inputs
- **Structured Logging:** Tracks security events
- **Resource Limits:** Prevents memory exhaustion

### Production Configuration

For production deployments, always configure these security settings:

```bash
# .env file
NODE_ENV=production
CORS_ORIGIN=https://yourdomain.com
TRUST_PROXY=true
LOG_LEVEL=info
PORT=8080
```

---

## CORS Configuration

### Development Mode (Default)

```javascript
// Allows all origins - ONLY for development
CORS_ORIGIN=*
```

### Production Mode (Recommended)

```javascript
// Restrict to specific domains
CORS_ORIGIN=https://yourdomain.com,https://api.yourdomain.com
```

### Advanced CORS Configuration

For more granular control, modify `tools/api-server.mjs`:

```javascript
app.use(cors({
  origin: function(origin, callback) {
    const whitelist = process.env.CORS_ORIGIN?.split(',') || ['*'];
    
    // Allow requests with no origin (mobile apps, curl, etc.)
    if (!origin) return callback(null, true);
    
    if (whitelist.includes('*') || whitelist.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: false, // Set to true if using cookies
  maxAge: 86400 // Cache preflight requests for 24 hours
}));
```

---

## Rate Limiting

### Default Configuration

The API server includes built-in rate limiting:

```javascript
const RATE_LIMIT_WINDOW = 60000; // 1 minute
const MAX_REQUESTS_PER_WINDOW = 100; // 100 requests per minute
```

### Customizing Rate Limits

For production environments, adjust limits based on your needs:

```javascript
// In tools/api-server.mjs
const RATE_LIMIT_WINDOW = 60000; // 1 minute
const MAX_REQUESTS_PER_WINDOW = 50; // More restrictive for production

// Or per environment
const MAX_REQUESTS = process.env.RATE_LIMIT_MAX || 
  (process.env.NODE_ENV === 'production' ? 50 : 100);
```

### Rate Limit Response

When rate limit is exceeded:

```json
HTTP/1.1 429 Too Many Requests
{
  "error": "Too many requests. Please try again later.",
  "retryAfter": 45
}
```

### Monitoring Rate Limits

Add logging to track rate limit hits:

```javascript
function rateLimitMiddleware(req, res, next) {
  const clientIp = getClientIp(req);
  const now = Date.now();
  
  // ... existing logic ...
  
  if (clientData.count >= MAX_REQUESTS_PER_WINDOW) {
    logger.warn('Rate limit exceeded', { 
      ip: clientIp, 
      path: req.path,
      method: req.method
    });
    return res.status(429).json({ 
      error: 'Too many requests. Please try again later.',
      retryAfter: Math.ceil((clientData.resetTime - now) / 1000)
    });
  }
  
  // ... continue ...
}
```

---

## Environment Variables

### Required for Production

```bash
# Server Configuration
NODE_ENV=production
PORT=8080

# Security
CORS_ORIGIN=https://yourdomain.com
TRUST_PROXY=true

# Logging
LOG_LEVEL=info

# Rate Limiting
RATE_LIMIT_MAX=50
RATE_LIMIT_WINDOW=60000
```

### Optional Configuration

```bash
# Database (if applicable)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pf_db
DB_USER=pf_user
DB_PASSWORD=<use-secrets-manager>

# Authentication (if applicable)
JWT_SECRET=<use-secrets-manager>
API_KEY=<use-secrets-manager>

# Monitoring
SENTRY_DSN=https://...
METRICS_ENABLED=true
```

### Loading Environment Variables

```javascript
// Load environment variables from .env file
import dotenv from 'dotenv';
dotenv.config();

// Validate required environment variables
const requiredEnvVars = ['NODE_ENV', 'CORS_ORIGIN'];
for (const envVar of requiredEnvVars) {
  if (!process.env[envVar]) {
    throw new Error(`Missing required environment variable: ${envVar}`);
  }
}
```

---

## Security Headers

### Recommended Headers

Add these security headers to all responses:

```javascript
// Security headers middleware
app.use((req, res, next) => {
  // Prevent clickjacking
  res.setHeader('X-Frame-Options', 'DENY');
  
  // Prevent MIME type sniffing
  res.setHeader('X-Content-Type-Options', 'nosniff');
  
  // Enable XSS protection
  res.setHeader('X-XSS-Protection', '1; mode=block');
  
  // Content Security Policy
  res.setHeader('Content-Security-Policy', 
    "default-src 'self'; " +
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; " +
    "style-src 'self' 'unsafe-inline'; " +
    "img-src 'self' data: https:; " +
    "font-src 'self' data:; " +
    "connect-src 'self'; " +
    "frame-ancestors 'none';"
  );
  
  // HSTS (only for HTTPS)
  if (req.secure || req.headers['x-forwarded-proto'] === 'https') {
    res.setHeader('Strict-Transport-Security', 
      'max-age=31536000; includeSubDomains; preload'
    );
  }
  
  // Referrer Policy
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  
  // Permissions Policy
  res.setHeader('Permissions-Policy', 
    'geolocation=(), microphone=(), camera=()'
  );
  
  next();
});
```

### Validating Security Headers

Use the built-in security headers validator:

```bash
# Start your API server
npm run dev

# In another terminal, validate headers
npm run security:headers http://localhost:8080
```

---

## Input Validation

### Built-in Validation Functions

The API server includes several validation helpers:

```javascript
// Sanitize strings
function sanitizeString(str, maxLength = 255) {
  if (typeof str !== 'string') return '';
  return str
    .slice(0, maxLength)
    .replace(/[<>&"'`\\]/g, '') // Remove dangerous characters
    .replace(/[\x00-\x1F\x7F]/g, ''); // Remove control characters
}

// Validate language parameter
function isValidLanguage(language) {
  const supportedLanguages = ['rust', 'c', 'fortran', 'wat'];
  return typeof language === 'string' && 
         supportedLanguages.includes(language);
}

// Validate target parameter
function isValidTarget(target) {
  const supportedTargets = ['wasm', 'llvm', 'asm'];
  return typeof target === 'string' && 
         supportedTargets.includes(target);
}

// Validate project name
function isValidProjectName(project) {
  if (typeof project !== 'string' || project.length === 0) {
    return false;
  }
  return /^[a-zA-Z0-9_-]+$/.test(project);
}
```

### Example Usage

```javascript
app.post('/api/build/:language', (req, res) => {
  const language = req.params.language;
  const { target, project } = req.body;
  
  // Validate inputs
  if (!isValidLanguage(language)) {
    return res.status(400).json({ 
      error: 'Invalid language specified' 
    });
  }
  
  if (target && !isValidTarget(target)) {
    return res.status(400).json({ 
      error: 'Invalid target specified' 
    });
  }
  
  if (project && !isValidProjectName(project)) {
    return res.status(400).json({ 
      error: 'Invalid project name' 
    });
  }
  
  // Sanitize string inputs
  const sanitizedProject = project ? 
    sanitizeString(project, 50) : 'default';
  
  // Process request...
});
```

---

## Best Practices

### 1. Never Commit Secrets

❌ **Bad:**
```javascript
const API_KEY = 'sk-1234567890abcdef';
const DB_PASSWORD = 'mypassword123';
```

✅ **Good:**
```javascript
const API_KEY = process.env.API_KEY;
const DB_PASSWORD = process.env.DB_PASSWORD;

if (!API_KEY || !DB_PASSWORD) {
  throw new Error('Missing required environment variables');
}
```

### 2. Use HTTPS in Production

Always use HTTPS in production environments:

```bash
# Use a reverse proxy like nginx
server {
  listen 443 ssl http2;
  server_name api.yourdomain.com;
  
  ssl_certificate /path/to/cert.pem;
  ssl_certificate_key /path/to/key.pem;
  
  location / {
    proxy_pass http://localhost:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

### 3. Implement Authentication

For production APIs, implement proper authentication:

```javascript
// JWT authentication middleware
import jwt from 'jsonwebtoken';

function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];
  
  if (!token) {
    return res.status(401).json({ error: 'Missing authentication token' });
  }
  
  jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
    if (err) {
      return res.status(403).json({ error: 'Invalid token' });
    }
    req.user = user;
    next();
  });
}

// Protect routes
app.post('/api/build/:language', authenticateToken, (req, res) => {
  // Only authenticated users can access
});
```

### 4. Implement Request Size Limits

Already configured in the API server:

```javascript
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
```

### 5. Log Security Events

```javascript
// Log security-relevant events
logger.warn('Authentication failed', { 
  ip: getClientIp(req),
  path: req.path,
  timestamp: new Date().toISOString()
});

logger.error('Security violation detected', {
  ip: getClientIp(req),
  violation: 'Invalid input detected',
  input: sanitizeString(req.body.suspicious)
});
```

---

## Security Scanning

### Available Security Tools

Run these tools regularly to ensure security:

```bash
# Scan for hardcoded credentials
npm run security:scan

# Scan for hardcoded credentials (verbose)
npm run security:scan:verbose

# Check dependencies for vulnerabilities
npm run security:deps

# Check dependencies (verbose)
npm run security:deps:verbose

# Validate security headers
npm run security:headers http://localhost:8080

# Run all security checks
npm run security:all
```

### Automated Security Scanning

Add to your CI/CD pipeline:

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * 0' # Weekly

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run security scans
        run: |
          npm run security:scan
          npm run security:deps
      
      - name: Upload scan results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: security-scan-results
          path: |
            security-report.json
            dependency-report.json
```

### TruffleHog Integration

The repository includes TruffleHog for secret scanning:

```bash
# Scan entire repository
./trufflehog filesystem . --json > trufflehog-report.json

# Scan specific directory
./trufflehog filesystem ./tools --json

# Scan git history
./trufflehog git file://. --json
```

---

## Checklist for Production Deployment

- [ ] Set `NODE_ENV=production`
- [ ] Configure `CORS_ORIGIN` to specific domain(s)
- [ ] Enable `TRUST_PROXY` if behind load balancer
- [ ] Set appropriate rate limits
- [ ] Configure HTTPS with valid certificates
- [ ] Implement authentication if needed
- [ ] Add security headers middleware
- [ ] Enable structured logging
- [ ] Set up monitoring and alerting
- [ ] Run security scans
- [ ] Review and audit dependencies
- [ ] Test error handling
- [ ] Set up automated security scanning in CI/CD
- [ ] Document security procedures
- [ ] Train team on security practices

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Express Security Best Practices](https://expressjs.com/en/advanced/best-practice-security.html)
- [Node.js Security Checklist](https://blog.risingstack.com/node-js-security-checklist/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [AWS Well-Architected Framework - Security Pillar](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html)

---

## Support

If you discover a security vulnerability, please email security@yourdomain.com or open a private security advisory on GitHub.

**Do not open public issues for security vulnerabilities.**

---

**Last Updated:** 2025-12-22  
**Version:** 1.0  
**Maintainer:** P4X-ng Development Team
