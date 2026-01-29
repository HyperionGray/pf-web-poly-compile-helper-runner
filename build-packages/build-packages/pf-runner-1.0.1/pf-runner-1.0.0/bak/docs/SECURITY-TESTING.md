# Web Application Security Testing

This module provides comprehensive web application security testing and fuzzing capabilities, inspired by industry-standard tools like Burp Suite and libraries like massweb.

## Overview

The security testing suite includes:

1. **Security Scanner** - Automated vulnerability detection
2. **Web Fuzzer** - Mass fuzzing with various payload types
3. **Integration with pf Tasks** - Easy-to-use task runner commands

## Features

### Vulnerability Detection

The security scanner can detect the following vulnerability types:

#### Injection Attacks
- **SQL Injection (SQLi)** - Detects SQL injection vulnerabilities through error-based and blind techniques
- **Cross-Site Scripting (XSS)** - Identifies reflected, stored, and DOM-based XSS vulnerabilities
- **OS Command Injection** - Tests for command injection in system calls
- **XML External Entity (XXE)** - Checks for unsafe XML parsing
- **XPath Injection** - Detects XPath query manipulation

#### Access Control Issues
- **Path Traversal** - Tests for directory traversal vulnerabilities
- **Broken Access Control** - Identifies unauthorized access to sensitive endpoints
- **Missing Authentication** - Detects unprotected sensitive resources

#### Server-Side Vulnerabilities
- **Server-Side Request Forgery (SSRF)** - Tests for internal network access
- **Security Misconfigurations** - Identifies missing security headers and unsafe configurations

#### Session Management
- **Cross-Site Request Forgery (CSRF)** - Checks for CSRF protection mechanisms
- **Insecure Session Handling** - Validates cookie security attributes

#### Information Disclosure
- **Security Headers** - Verifies presence of security headers
- **Information Leakage** - Detects exposed version information and error messages

## Installation

The security tools are included in the repository. No additional installation is required beyond the base dependencies:

```bash
# Install base dependencies
npm install

# Or use pf installer
pf install
```

## Usage

### Using pf Tasks (Recommended)

The easiest way to run security tests is through pf tasks:

```bash
# Run full security scan
pf security-scan url=http://localhost:8080

# Run specific vulnerability checks
pf security-scan url=http://localhost:8080/api checks=sqli,xss

# Run web fuzzer
pf security-fuzz url=http://localhost:8080/search

# Run fuzzer with specific payload type
pf security-fuzz url=http://localhost:8080/api type=sqli

# Generate JSON report
pf security-scan-json url=http://localhost:8080

# Run complete security test suite
pf security-test-all url=http://localhost:8080
```

### Direct Command Line Usage

You can also run the tools directly:

#### Security Scanner

```bash
# Basic scan
node tools/security/scanner.mjs http://localhost:8080

# Verbose output
node tools/security/scanner.mjs http://localhost:8080 --verbose

# Run specific checks
node tools/security/scanner.mjs http://localhost:8080 --checks sqli,xss,csrf

# JSON output
node tools/security/scanner.mjs http://localhost:8080 --json

# Custom timeout
node tools/security/scanner.mjs http://localhost:8080 --timeout 10000
```

#### Web Fuzzer

```bash
# Basic fuzzing
node tools/security/fuzzer.mjs http://localhost:8080/search

# Fuzz with specific payload type
node tools/security/fuzzer.mjs http://localhost:8080/api --type sqli

# Add delay between requests
node tools/security/fuzzer.mjs http://localhost:8080/search --delay 100

# Verbose mode
node tools/security/fuzzer.mjs http://localhost:8080/api --verbose --type xss

# JSON output
node tools/security/fuzzer.mjs http://localhost:8080/search --json
```

### Programmatic Usage

You can also use the tools programmatically in your Node.js applications:

```javascript
import SecurityScanner from './tools/security/scanner.mjs';
import WebFuzzer from './tools/security/fuzzer.mjs';

// Security Scanner
const scanner = new SecurityScanner({
  baseUrl: 'http://localhost:8080',
  verbose: true,
  timeout: 5000
});

const report = await scanner.scan('http://localhost:8080/api');
scanner.printReport(report);

// Web Fuzzer
const fuzzer = new WebFuzzer({
  baseUrl: 'http://localhost:8080',
  verbose: true,
  timeout: 5000,
  delay: 50
});

const fuzzReport = await fuzzer.fuzzMultiple(
  ['http://localhost:8080/search', 'http://localhost:8080/api'],
  'sqli'
);
fuzzer.printReport(fuzzReport);
```

## Available Checks

### Scanner Checks

- `sqli` - SQL Injection
- `xss` - Cross-Site Scripting
- `traversal` - Path Traversal
- `cmdi` - Command Injection
- `xxe` - XML External Entity
- `ssrf` - Server-Side Request Forgery
- `csrf` - Cross-Site Request Forgery
- `headers` - Security Headers
- `auth` - Authentication/Access Control

### Fuzzer Payload Types

- `sqli` - SQL Injection payloads
- `xss` - Cross-Site Scripting payloads
- `traversal` - Path Traversal payloads
- `cmdi` - Command Injection payloads
- `ssrf` - Server-Side Request Forgery payloads
- `all` - All payload types (default)

## Vulnerability Severity Levels

Findings are categorized by severity:

- **🔴 Critical** - Immediate action required (e.g., RCE, SQLi with data access)
- **🟠 High** - High risk vulnerabilities (e.g., XSS, Path Traversal)
- **🟡 Medium** - Moderate risk issues (e.g., CSRF without sensitive operations)
- **🟢 Low** - Low risk findings (e.g., Missing headers, Information disclosure)

## Report Formats

### Console Output

Default format provides human-readable output with color-coded severity levels:

```
============================================================
               SECURITY SCAN REPORT
============================================================

Summary:
  Total Findings: 5
  🔴 Critical: 1
  🟠 High: 2
  🟡 Medium: 1
  🟢 Low: 1

Findings:

1. 🔴 SQL Injection [CRITICAL]
   URL: http://localhost:8080/search?test=%27+OR+%271%27%3D%271
   Payload: ' OR '1'='1
   Evidence: you have an error in your sql syntax
   Description: Potential SQL injection vulnerability...
```

### JSON Output

JSON format for integration with other tools:

```json
{
  "summary": {
    "total": 5,
    "critical": 1,
    "high": 2,
    "medium": 1,
    "low": 1
  },
  "findings": [
    {
      "timestamp": "2024-01-01T00:00:00.000Z",
      "type": "SQL Injection",
      "severity": "critical",
      "url": "http://localhost:8080/search?test=%27+OR+%271%27%3D%271",
      "payload": "' OR '1'='1",
      "evidence": "you have an error in your sql syntax",
      "description": "Potential SQL injection vulnerability..."
    }
  ],
  "scanDate": "2024-01-01T00:00:00.000Z"
}
```

## Best Practices

### Pre-Testing Checklist

1. **Authorization** - Ensure you have permission to test the target
2. **Scope** - Define and stick to the scope of testing
3. **Backup** - Have backups of the application and data
4. **Rate Limiting** - Use appropriate delays to avoid overwhelming the server

### Testing Methodology

1. **Reconnaissance** - Start with passive scanning (headers, configurations)
2. **Active Scanning** - Run targeted vulnerability checks
3. **Fuzzing** - Use mass fuzzing for comprehensive coverage
4. **Manual Verification** - Verify automated findings manually
5. **Reporting** - Document all findings with evidence

### Configuration Recommendations

```javascript
// For development/testing
const devConfig = {
  verbose: true,
  timeout: 5000,
  delay: 0
};

// For production scanning (be gentle)
const prodConfig = {
  verbose: false,
  timeout: 10000,
  delay: 100  // 100ms delay between requests
};
```

## Integration with CI/CD

You can integrate security testing into your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
name: Security Scan
on: [push, pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start application
        run: npm start &
      - name: Wait for server
        run: sleep 10
      - name: Run security scan
        run: node tools/security/scanner.mjs http://localhost:8080 --json > security-report.json
      - name: Upload report
        uses: actions/upload-artifact@v2
        with:
          name: security-report
          path: security-report.json
```

## Comparison with Burp Suite

This security scanner provides similar capabilities to Burp Suite's automated scanner:

| Feature | Burp Suite | This Scanner |
|---------|------------|--------------|
| SQL Injection | ✓ | ✓ |
| XSS Detection | ✓ | ✓ |
| CSRF Detection | ✓ | ✓ |
| Path Traversal | ✓ | ✓ |
| Command Injection | ✓ | ✓ |
| XXE Detection | ✓ | ✓ |
| SSRF Detection | ✓ | ✓ |
| Security Headers | ✓ | ✓ |
| Custom Payloads | ✓ | ✓ (via code) |
| GUI | ✓ | ✗ |
| Proxy | ✓ | ✗ |
| Active Scanning | ✓ | ✓ |
| Passive Scanning | ✓ | ✓ (headers) |
| Cost | $$$ (Pro) | Free |

## Limitations

- **No Proxy Functionality** - Unlike Burp Suite, this tool doesn't intercept traffic
- **Limited Passive Scanning** - Focuses primarily on active testing
- **Basic Fuzzing** - Not as comprehensive as dedicated fuzzing tools
- **No Authentication Handling** - Limited support for authenticated scanning
- **Rate Limiting** - Simple delay mechanism, not sophisticated traffic shaping

## Advanced Usage

### Custom Payloads

You can extend the scanner with custom payloads:

```javascript
import SecurityScanner from './tools/security/scanner.mjs';

class CustomScanner extends SecurityScanner {
  async checkCustomVulnerability(url) {
    const customPayloads = [
      'custom-payload-1',
      'custom-payload-2'
    ];
    
    for (const payload of customPayloads) {
      const testUrl = `${url}?param=${encodeURIComponent(payload)}`;
      const response = await this.makeRequest(testUrl);
      
      if (response.body.includes('vulnerable-pattern')) {
        this.addFinding({
          type: 'Custom Vulnerability',
          severity: 'high',
          url: testUrl,
          payload: payload,
          description: 'Custom vulnerability detected'
        });
      }
    }
  }
}

const scanner = new CustomScanner({ baseUrl: 'http://localhost:8080' });
await scanner.checkCustomVulnerability('http://localhost:8080/api');
```

### Event-Based Fuzzing

The fuzzer emits events for progress tracking:

```javascript
import WebFuzzer from './tools/security/fuzzer.mjs';

const fuzzer = new WebFuzzer({
  baseUrl: 'http://localhost:8080',
  verbose: false
});

fuzzer.on('progress', ({ current, total, result }) => {
  console.log(`Progress: ${current}/${total}`);
  
  if (result.anomaly) {
    console.log(`Anomaly detected: ${result.url}`);
  }
});

await fuzzer.fuzzMultiple(['http://localhost:8080/api'], 'all');
```

## Troubleshooting

### Common Issues

1. **Connection Timeouts**
   - Increase timeout: `--timeout 10000`
   - Check if target is accessible

2. **Too Many Requests**
   - Add delay: `--delay 100`
   - Reduce concurrency

3. **False Positives**
   - Review findings manually
   - Adjust detection signatures
   - Use `--checks` to run specific tests

4. **Rate Limiting**
   - Increase delay between requests
   - Use authenticated scanning if available

## Contributing

To add new vulnerability checks:

1. Create a new method in `SecurityScanner` class
2. Add detection signatures
3. Include in the scan execution flow
4. Update documentation

Example:

```javascript
async checkNewVulnerability(url) {
  this.log(`[NewVuln] Testing ${url}`);
  
  const payloads = ['payload1', 'payload2'];
  const signatures = [/pattern1/, /pattern2/];
  
  for (const payload of payloads) {
    const testUrl = `${url}?param=${encodeURIComponent(payload)}`;
    const response = await this.makeRequest(testUrl);
    
    if (!response.error) {
      for (const signature of signatures) {
        if (signature.test(response.body)) {
          this.addFinding({
            type: 'New Vulnerability Type',
            severity: 'medium',
            url: testUrl,
            payload: payload,
            evidence: response.body.match(signature)?.[0],
            description: 'Description of the vulnerability'
          });
        }
      }
    }
  }
}
```

## Resources

### References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [PortSwigger Web Security Academy](https://portswigger.net/web-security)
- [Burp Suite Documentation](https://portswigger.net/burp/documentation)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

### Related Tools

- [Burp Suite](https://portswigger.net/burp) - Professional web security testing platform
- [OWASP ZAP](https://www.zaproxy.org/) - Open-source security scanner
- [SQLMap](https://sqlmap.org/) - SQL injection tool
- [XSSer](https://xsser.03c8.net/) - XSS detection framework
- [Wfuzz](https://github.com/xmendez/wfuzz) - Web application fuzzer
- [massweb](https://github.com/HyperionGray/massweb) - Mass web fuzzing library

## License

This security testing module is part of the pf-web-poly-compile-helper-runner project and follows the same license.

## Disclaimer

⚠️ **IMPORTANT**: Only use these tools on applications you own or have explicit permission to test. Unauthorized security testing may be illegal in your jurisdiction. Always follow responsible disclosure practices when reporting vulnerabilities.
