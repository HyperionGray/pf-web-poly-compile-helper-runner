# Security Best Practices

This document outlines security considerations and best practices implemented in the pf-web-poly-compile-helper-runner project.

## API Server Security

### Rate Limiting

The API server implements rate limiting to prevent abuse:
- **Window**: 1 minute (60,000 ms)
- **Max Requests**: 100 per window per client IP
- **Response**: HTTP 429 (Too Many Requests) with `retryAfter` header

**Configuration**: Modify `RATE_LIMIT_WINDOW` and `MAX_REQUESTS_PER_WINDOW` in `tools/api-server.mjs`.

### CORS Configuration

CORS is configured with sensible defaults:
- **Origin**: Configurable via `CORS_ORIGIN` environment variable (defaults to `*` for development)
- **Methods**: GET, POST, PUT, DELETE, OPTIONS
- **Headers**: Content-Type, Authorization
- **Credentials**: Disabled by default for security

**Production Recommendation**: Set `CORS_ORIGIN` to specific allowed domains:
```bash
export CORS_ORIGIN=https://yourdomain.com
```

### Input Validation

All user inputs are sanitized and validated:

1. **String Sanitization** (`sanitizeString`):
   - Removes potentially dangerous characters: `<>&"'\`\\`
   - Removes control characters (0x00-0x1F, 0x7F)
   - Enforces maximum length limits (default: 255 chars)

2. **Language Validation** (`isValidLanguage`):
   - Only allows: `rust`, `c`, `fortran`, `wat`
   - Rejects any other input

3. **Target Validation** (`isValidTarget`):
   - Only allows: `wasm`, `llvm`, `asm`
   - Rejects any other input

4. **Project Name Validation** (`isValidProjectName`):
   - Only allows alphanumeric, hyphens, and underscores: `/^[a-zA-Z0-9_-]+$/`
   - Prevents path traversal attacks

### Path Traversal Protection

The static file server implements path traversal protection:
```javascript
const resolvedPath = path.resolve(filePath);
if (!resolvedPath.startsWith(path.resolve(ROOT))) {
  res.statusCode = 403;
  res.end('Forbidden');
  return;
}
```

### Resource Limits

To prevent resource exhaustion attacks:

1. **Build Limits**:
   - Maximum concurrent builds: 100
   - Maximum logs per build: 1,000 entries
   - Automatic cleanup of old builds

2. **Command Execution**:
   - Default timeout: 5 minutes (300,000 ms)
   - Maximum buffer size: 1 MB per stream
   - Automatic process termination on timeout

3. **Request Body Limits**:
   - JSON payload: 10 MB
   - URL-encoded payload: 10 MB

### Structured Logging

Implemented structured JSON logging for security monitoring:

```javascript
logger.info('message', { key: 'value' });
logger.warn('warning', { details });
logger.error('error', { error: error.message });
```

**Log Levels**:
- `error`: Critical errors requiring immediate attention
- `warn`: Warning conditions
- `info`: Informational messages (default)
- `debug`: Detailed debugging information

**Configuration**: Set `LOG_LEVEL` environment variable:
```bash
export LOG_LEVEL=debug
```

### Graceful Shutdown

Proper cleanup on shutdown prevents resource leaks:
- Handles SIGTERM and SIGINT signals
- Closes server connections gracefully
- 30-second timeout before forced shutdown

## Dependency Security

### Vulnerability Scanning

Run regular security audits:
```bash
npm audit
npm audit fix
```

**Status**: Run `npm audit` regularly to check for vulnerabilities. Current dependencies are audited automatically on each release.

### Package Updates

Keep dependencies updated:
```bash
npm outdated
npm update
```

Consider using automated tools:
- Dependabot (GitHub)
- Renovate Bot
- Snyk

## Code Injection Prevention

### Command Execution

When executing external commands:
1. Never pass unsanitized user input directly to `spawn` or `exec`
2. Use argument arrays instead of shell strings
3. Validate all parameters before use

**Example** (from api-server.mjs):
```javascript
const child = spawn(pfPath, fullCommand, {
  stdio: ['pipe', 'pipe', 'pipe'],
  env: { ...process.env, ...options.env }
});
```

### Shell Injection

Avoid shell execution when possible:
- Use `spawn` instead of `exec`
- Pass arguments as array, not concatenated string
- Never use `shell: true` option with user input

## WebSocket Security

### Connection Management

- Log client connections with IP addresses
- Implement proper error handling
- Send sanitized data only
- Handle client disconnections gracefully

### Message Validation

Validate all incoming WebSocket messages:
- Check message format
- Validate message types
- Sanitize message content

## Environment Variables

### Sensitive Configuration

Never commit sensitive data. Use environment variables:

```bash
# .env (DO NOT COMMIT)
CORS_ORIGIN=https://production.com
LOG_LEVEL=info
API_PORT=8080
```

### Available Configuration

- `CORS_ORIGIN`: Allowed CORS origins
- `LOG_LEVEL`: Logging verbosity (error|warn|info|debug)
- `PF_API_HOST`: API server bind address
- `PF_API_PORT`: API server port
- `PF_API_WORKERS`: Number of workers

## Security Headers

### Current Implementation

```javascript
res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
```

### Recommended Additional Headers

Consider adding:
```javascript
res.setHeader('X-Frame-Options', 'DENY');
res.setHeader('X-Content-Type-Options', 'nosniff');
res.setHeader('X-XSS-Protection', '1; mode=block');
res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
res.setHeader('Content-Security-Policy', "default-src 'self'");
```

## Monitoring and Alerting

### Log Analysis

Monitor logs for:
- Repeated 429 (rate limit) responses
- Failed authentication attempts
- Unusual API usage patterns
- Error spikes
- Timeout patterns

### Metrics to Track

1. **API Performance**:
   - Request rate
   - Response times
   - Error rates

2. **Resource Usage**:
   - Memory consumption
   - CPU usage
   - Active connections

3. **Security Events**:
   - Failed validations
   - Rate limit hits
   - Path traversal attempts

## Incident Response

### In Case of Security Incident

1. **Immediate Actions**:
   - Stop the affected service
   - Preserve logs and evidence
   - Assess the scope of impact

2. **Investigation**:
   - Review logs for attack patterns
   - Identify compromised components
   - Determine data exposure

3. **Recovery**:
   - Update dependencies
   - Patch vulnerabilities
   - Restore from clean backups

4. **Post-Incident**:
   - Document findings
   - Update security measures
   - Conduct security review

## Security Checklist

Before deploying to production:

- [ ] Set `CORS_ORIGIN` to specific allowed domains
- [ ] Configure appropriate `LOG_LEVEL`
- [ ] Enable HTTPS/TLS
- [ ] Set up log monitoring and alerting
- [ ] Run `npm audit` and fix vulnerabilities
- [ ] Review and test rate limiting
- [ ] Verify input validation on all endpoints
- [ ] Test error handling and timeouts
- [ ] Implement backup and recovery procedures
- [ ] Document incident response plan
- [ ] Configure security headers
- [ ] Set up automated security scanning

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** create a public GitHub issue
2. Email security concerns to the maintainers
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Node.js Security Best Practices](https://nodejs.org/en/docs/guides/security/)
- [Express Security Guide](https://expressjs.com/en/advanced/best-practice-security.html)
- [npm Security Best Practices](https://docs.npmjs.com/security-best-practices)

---

**Maintained By**: pf-web-poly-compile-helper-runner Contributors  
**Note**: This documentation is updated as part of ongoing development. Check the git history for the latest changes.
