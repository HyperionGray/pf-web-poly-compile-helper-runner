#!/usr/bin/env node
/**
 * Web Application Security Scanner
 * Inspired by Burp Suite and massweb
 * 
 * Supports scanning for common web vulnerabilities including:
 * - SQL Injection
 * - Cross-Site Scripting (XSS)
 * - Cross-Site Request Forgery (CSRF)
 * - Path Traversal
 * - OS Command Injection
 * - XML External Entity (XXE)
 * - Server-Side Request Forgery (SSRF)
 * - Security Misconfigurations
 * - Insecure Headers
 */

import { setTimeout } from 'node:timers/promises';

export class SecurityScanner {
  constructor(options = {}) {
    this.baseUrl = options.baseUrl || '';
    this.verbose = options.verbose || false;
    this.quiet = options.quiet || false;
    this.timeout = options.timeout || 5000;
    this.results = [];
  }

  log(message) {
    if (this.verbose) {
      console.log(message);
    }
  }

  /**
   * Perform a safe HTTP request with timeout
   */
  async makeRequest(url, options = {}) {
    try {
      const controller = new AbortController();
      const timeoutHandle = globalThis.setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });

      globalThis.clearTimeout(timeoutHandle);
      
      const text = await response.text();
      return {
        status: response.status,
        headers: Object.fromEntries(response.headers.entries()),
        body: text,
        url: response.url
      };
    } catch (error) {
      return {
        error: error.message,
        url: url
      };
    }
  }

  /**
   * Add a vulnerability finding
   */
  addFinding(finding) {
    this.results.push({
      timestamp: new Date().toISOString(),
      ...finding
    });
  }

  /**
   * Check for SQL Injection vulnerabilities
   */
  async checkSQLInjection(url) {
    this.log(`[SQLi] Testing ${url}`);
    
    const payloads = [
      "' OR '1'='1",
      "' OR '1'='1' --",
      "' OR '1'='1' /*",
      "admin' --",
      "1' UNION SELECT NULL--",
      "1' AND 1=1--",
      "1' AND 1=2--"
    ];

    const errorSignatures = [
      /you have an error in your sql syntax/i,
      /warning.*mysql/i,
      /unclosed quotation mark/i,
      /quoted string not properly terminated/i,
      /sql syntax.*error/i,
      /sqlexception/i,
      /ora-\d{5}/i,
      /postgresql.*error/i,
      /db2 sql error/i,
      /microsoft ole db provider/i
    ];

    for (const payload of payloads) {
      const testUrl = `${url}${url.includes('?') ? '&' : '?'}test=${encodeURIComponent(payload)}`;
      const response = await this.makeRequest(testUrl);
      
      if (!response.error) {
        for (const signature of errorSignatures) {
          if (signature.test(response.body)) {
            this.addFinding({
              type: 'SQL Injection',
              severity: 'high',
              url: testUrl,
              payload: payload,
              evidence: response.body.match(signature)?.[0],
              description: 'Potential SQL injection vulnerability detected based on database error messages'
            });
            break;
          }
        }
      }
    }
  }

  /**
   * Check for Cross-Site Scripting (XSS) vulnerabilities
   */
  async checkXSS(url) {
    this.log(`[XSS] Testing ${url}`);
    
    const payloads = [
      "<script>alert(31337)</script>",
      "<img src=x onerror=alert(31337)>",
      "<svg/onload=alert(31337)>",
      "javascript:alert(31337)",
      "<iframe src=\"javascript:alert(31337)\">",
      "'\"><script>alert(31337)</script>",
      "<body onload=alert(31337)>"
    ];

    for (const payload of payloads) {
      const testUrl = `${url}${url.includes('?') ? '&' : '?'}test=${encodeURIComponent(payload)}`;
      const response = await this.makeRequest(testUrl);
      
      if (!response.error && response.body.includes(payload)) {
        this.addFinding({
          type: 'Cross-Site Scripting (XSS)',
          severity: 'high',
          url: testUrl,
          payload: payload,
          evidence: 'Payload reflected in response without sanitization',
          description: 'Potential XSS vulnerability - user input is reflected without proper encoding'
        });
      }
    }
  }

  /**
   * Check for Path Traversal vulnerabilities
   */
  async checkPathTraversal(url) {
    this.log(`[Path Traversal] Testing ${url}`);
    
    const payloads = [
      "../../../etc/passwd",
      "..\\..\\..\\windows\\win.ini",
      "....//....//....//etc/passwd",
      "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
      "..%252f..%252f..%252fetc%252fpasswd"
    ];

    const signatures = [
      /root:x:\d+:\d+:/,
      /\[fonts\]/i,
      /\[extensions\]/i,
      /for 16-bit app support/i
    ];

    for (const payload of payloads) {
      const testUrl = `${url}${url.includes('?') ? '&' : '?'}file=${encodeURIComponent(payload)}`;
      const response = await this.makeRequest(testUrl);
      
      if (!response.error) {
        for (const signature of signatures) {
          if (signature.test(response.body)) {
            this.addFinding({
              type: 'Path Traversal',
              severity: 'high',
              url: testUrl,
              payload: payload,
              evidence: response.body.match(signature)?.[0],
              description: 'Path traversal vulnerability detected - sensitive system files accessible'
            });
            break;
          }
        }
      }
    }
  }

  /**
   * Check for OS Command Injection
   */
  async checkCommandInjection(url) {
    this.log(`[Command Injection] Testing ${url}`);
    
    const payloads = [
      "; cat /etc/passwd",
      "| cat /etc/passwd",
      "& type C:\\windows\\win.ini",
      "`cat /etc/passwd`",
      "$(cat /etc/passwd)"
    ];

    const signatures = [
      /root:x:\d+:\d+:/,
      /\[fonts\]/i,
      /\[extensions\]/i
    ];

    for (const payload of payloads) {
      const testUrl = `${url}${url.includes('?') ? '&' : '?'}cmd=${encodeURIComponent(payload)}`;
      const response = await this.makeRequest(testUrl);
      
      if (!response.error) {
        for (const signature of signatures) {
          if (signature.test(response.body)) {
            this.addFinding({
              type: 'OS Command Injection',
              severity: 'critical',
              url: testUrl,
              payload: payload,
              evidence: response.body.match(signature)?.[0],
              description: 'Command injection vulnerability detected - arbitrary system commands can be executed'
            });
            break;
          }
        }
      }
    }
  }

  /**
   * Check for XML External Entity (XXE) vulnerabilities
   */
  async checkXXE(url) {
    this.log(`[XXE] Testing ${url}`);
    
    const payload = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<data>&xxe;</data>`;

    try {
      const response = await this.makeRequest(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/xml'
        },
        body: payload
      });

      if (!response.error && /root:x:\d+:\d+:/.test(response.body)) {
        this.addFinding({
          type: 'XML External Entity (XXE)',
          severity: 'critical',
          url: url,
          payload: payload,
          evidence: 'System file contents exposed in response',
          description: 'XXE vulnerability detected - external entities are processed unsafely'
        });
      }
    } catch (error) {
      // XXE test failed, likely not vulnerable
    }
  }

  /**
   * Check for Server-Side Request Forgery (SSRF)
   */
  async checkSSRF(url) {
    this.log(`[SSRF] Testing ${url}`);
    
    const payloads = [
      "http://localhost/admin",
      "http://127.0.0.1:22",
      "http://169.254.169.254/latest/meta-data/",
      "file:///etc/passwd"
    ];

    for (const payload of payloads) {
      const testUrl = `${url}${url.includes('?') ? '&' : '?'}url=${encodeURIComponent(payload)}`;
      const response = await this.makeRequest(testUrl);
      
      if (!response.error) {
        // Look for signs that internal request was made
        if (response.body.length > 100 || response.body.includes('ami-id') || /root:x:\d+/.test(response.body)) {
          this.addFinding({
            type: 'Server-Side Request Forgery (SSRF)',
            severity: 'high',
            url: testUrl,
            payload: payload,
            evidence: 'Response suggests internal URL was accessed',
            description: 'Potential SSRF vulnerability - server makes requests to attacker-controlled URLs'
          });
        }
      }
    }
  }

  /**
   * Check for CSRF protection
   */
  async checkCSRF(url) {
    this.log(`[CSRF] Testing ${url}`);
    
    const response = await this.makeRequest(url);
    
    if (!response.error) {
      // Check for CSRF tokens in forms
      const hasCSRFToken = /csrf|token|_token/.test(response.body);
      
      // Check for SameSite cookie attribute
      const cookies = response.headers['set-cookie'] || '';
      const hasSameSite = /samesite=(?:strict|lax)/i.test(cookies);
      
      if (!hasCSRFToken && !hasSameSite) {
        this.addFinding({
          type: 'Missing CSRF Protection',
          severity: 'medium',
          url: url,
          evidence: 'No CSRF tokens or SameSite cookie attributes detected',
          description: 'Application may be vulnerable to CSRF attacks - no protection mechanisms detected'
        });
      }
    }
  }

  /**
   * Check for security headers
   */
  async checkSecurityHeaders(url) {
    this.log(`[Security Headers] Testing ${url}`);
    
    const response = await this.makeRequest(url);
    
    if (!response.error) {
      const headers = response.headers;
      const missingHeaders = [];

      // Check for important security headers
      if (!headers['x-frame-options'] && !headers['content-security-policy']) {
        missingHeaders.push('X-Frame-Options or CSP (Clickjacking protection)');
      }
      
      if (!headers['x-content-type-options']) {
        missingHeaders.push('X-Content-Type-Options (MIME-sniffing protection)');
      }
      
      if (!headers['strict-transport-security']) {
        missingHeaders.push('Strict-Transport-Security (HTTPS enforcement)');
      }
      
      if (!headers['x-xss-protection']) {
        missingHeaders.push('X-XSS-Protection (XSS filter)');
      }

      if (headers['server']) {
        missingHeaders.push('Server header leaks version information');
      }

      if (headers['x-powered-by']) {
        missingHeaders.push('X-Powered-By header leaks technology stack');
      }

      if (missingHeaders.length > 0) {
        this.addFinding({
          type: 'Security Misconfiguration',
          severity: 'low',
          url: url,
          evidence: missingHeaders.join('; '),
          description: 'Missing or insecure security headers detected'
        });
      }
    }
  }

  /**
   * Check for insecure authentication
   */
  async checkAuthentication(url) {
    this.log(`[Authentication] Testing ${url}`);
    
    const response = await this.makeRequest(url);
    
    if (!response.error) {
      // Check if sensitive endpoints are accessible without auth
      const sensitivePatterns = ['/admin', '/api', '/config', '/dashboard', '/.env', '/.git'];
      
      for (const pattern of sensitivePatterns) {
        const testUrl = new URL(pattern, url).href;
        const testResponse = await this.makeRequest(testUrl);
        
        if (!testResponse.error && testResponse.status === 200) {
          this.addFinding({
            type: 'Broken Access Control',
            severity: 'high',
            url: testUrl,
            evidence: `Sensitive endpoint accessible without authentication (HTTP ${testResponse.status})`,
            description: 'Potential access control vulnerability - sensitive resources accessible without proper authentication'
          });
        }
      }
    }
  }

  /**
   * Run a full security scan
   */
  async scan(url, options = {}) {
    this.results = [];
    const targetUrl = url || this.baseUrl;
    
    if (!targetUrl) {
      throw new Error('No URL provided for scanning');
    }

    if (!this.quiet) {
      console.log(`🔍 Starting security scan on: ${targetUrl}\n`);
    }

    const scanFunctions = [
      () => this.checkSecurityHeaders(targetUrl),
      () => this.checkSQLInjection(targetUrl),
      () => this.checkXSS(targetUrl),
      () => this.checkPathTraversal(targetUrl),
      () => this.checkCommandInjection(targetUrl),
      () => this.checkXXE(targetUrl),
      () => this.checkSSRF(targetUrl),
      () => this.checkCSRF(targetUrl),
      () => this.checkAuthentication(targetUrl)
    ];

    if (options.checks) {
      // Run only specified checks
      for (const check of options.checks) {
        const fn = scanFunctions.find(f => f.name.toLowerCase().includes(check.toLowerCase()));
        if (fn) await fn();
      }
    } else {
      // Run all checks
      for (const fn of scanFunctions) {
        await fn();
      }
    }

    return this.getReport();
  }

  /**
   * Generate a security report
   */
  getReport() {
    const summary = {
      total: this.results.length,
      critical: this.results.filter(r => r.severity === 'critical').length,
      high: this.results.filter(r => r.severity === 'high').length,
      medium: this.results.filter(r => r.severity === 'medium').length,
      low: this.results.filter(r => r.severity === 'low').length
    };

    return {
      summary,
      findings: this.results,
      scanDate: new Date().toISOString()
    };
  }

  /**
   * Print a formatted report to console
   */
  printReport(report = null) {
    const r = report || this.getReport();
    
    console.log('\n' + '='.repeat(60));
    console.log('               SECURITY SCAN REPORT');
    console.log('='.repeat(60) + '\n');
    
    console.log('Summary:');
    console.log(`  Total Findings: ${r.summary.total}`);
    console.log(`  🔴 Critical: ${r.summary.critical}`);
    console.log(`  🟠 High: ${r.summary.high}`);
    console.log(`  🟡 Medium: ${r.summary.medium}`);
    console.log(`  🟢 Low: ${r.summary.low}`);
    console.log('');

    if (r.findings.length === 0) {
      console.log('✅ No vulnerabilities detected!\n');
      return;
    }

    console.log('Findings:\n');
    
    r.findings.forEach((finding, idx) => {
      const severityIcon = {
        critical: '🔴',
        high: '🟠',
        medium: '🟡',
        low: '🟢'
      }[finding.severity] || '⚪';

      console.log(`${idx + 1}. ${severityIcon} ${finding.type} [${finding.severity.toUpperCase()}]`);
      console.log(`   URL: ${finding.url}`);
      if (finding.payload) {
        console.log(`   Payload: ${finding.payload}`);
      }
      if (finding.evidence) {
        console.log(`   Evidence: ${finding.evidence}`);
      }
      console.log(`   Description: ${finding.description}`);
      console.log('');
    });

    console.log('='.repeat(60) + '\n');
  }
}

// CLI interface
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  
  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    console.log(`
Web Application Security Scanner

Usage:
  scanner.mjs <url> [options]

Options:
  --verbose, -v       Enable verbose output
  --timeout <ms>      Request timeout in milliseconds (default: 5000)
  --json              Output results as JSON
  --checks <list>     Comma-separated list of checks to run
                      Available: sqli,xss,traversal,cmdi,xxe,ssrf,csrf,headers,auth

Examples:
  scanner.mjs http://localhost:8080
  scanner.mjs http://localhost:8080 --verbose
  scanner.mjs http://localhost:8080 --checks sqli,xss --json
`);
    process.exit(0);
  }

  const url = args[0];
  const verbose = args.includes('--verbose') || args.includes('-v');
  const json = args.includes('--json');
  
  let timeout = 5000;
  const timeoutIdx = args.findIndex(a => a === '--timeout');
  if (timeoutIdx !== -1 && args[timeoutIdx + 1]) {
    timeout = parseInt(args[timeoutIdx + 1], 10);
  }

  let checks = null;
  const checksIdx = args.findIndex(a => a === '--checks');
  if (checksIdx !== -1 && args[checksIdx + 1]) {
    checks = args[checksIdx + 1].split(',');
  }

  const scanner = new SecurityScanner({ baseUrl: url, verbose, timeout, quiet: json });
  
  scanner.scan(url, { checks })
    .then(report => {
      if (json) {
        console.log(JSON.stringify(report, null, 2));
      } else {
        scanner.printReport(report);
      }
      
      // Exit with error code if critical or high severity findings
      if (report.summary.critical > 0 || report.summary.high > 0) {
        process.exit(1);
      }
    })
    .catch(error => {
      console.error('Error during scan:', error.message);
      process.exit(1);
    });
}

export default SecurityScanner;
