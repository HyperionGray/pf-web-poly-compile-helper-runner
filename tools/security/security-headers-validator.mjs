#!/usr/bin/env node
/**
 * Security Headers Validator
 * 
 * Addresses Amazon Q Code Review security recommendation:
 * "Security Considerations: Check for proper security headers"
 * 
 * Validates that web servers are configured with appropriate security headers
 */

import { setTimeout } from 'node:timers/promises';

// Recommended security headers and their expected values
const SECURITY_HEADERS = {
  'x-frame-options': {
    name: 'X-Frame-Options',
    description: 'Prevents clickjacking attacks',
    severity: 'high',
    recommended: ['DENY', 'SAMEORIGIN'],
    required: true
  },
  'x-content-type-options': {
    name: 'X-Content-Type-Options',
    description: 'Prevents MIME type sniffing',
    severity: 'medium',
    recommended: ['nosniff'],
    required: true
  },
  'strict-transport-security': {
    name: 'Strict-Transport-Security',
    description: 'Enforces HTTPS connections',
    severity: 'high',
    recommended: ['max-age=31536000; includeSubDomains'],
    required: true,
    httpsOnly: true
  },
  'content-security-policy': {
    name: 'Content-Security-Policy',
    description: 'Prevents XSS and other injection attacks',
    severity: 'high',
    recommended: ["default-src 'self'"],
    required: true
  },
  'x-xss-protection': {
    name: 'X-XSS-Protection',
    description: 'Enables browser XSS filter',
    severity: 'medium',
    recommended: ['1; mode=block'],
    required: false,
    deprecated: true,
    note: 'Deprecated in favor of CSP, but still useful for older browsers'
  },
  'referrer-policy': {
    name: 'Referrer-Policy',
    description: 'Controls referrer information',
    severity: 'low',
    recommended: ['strict-origin-when-cross-origin', 'no-referrer', 'same-origin'],
    required: false
  },
  'permissions-policy': {
    name: 'Permissions-Policy',
    description: 'Controls browser features and APIs',
    severity: 'low',
    recommended: ['geolocation=(), microphone=(), camera=()'],
    required: false
  },
  'x-permitted-cross-domain-policies': {
    name: 'X-Permitted-Cross-Domain-Policies',
    description: 'Controls cross-domain policies for Flash/PDF',
    severity: 'low',
    recommended: ['none'],
    required: false
  }
};

// Headers that should NOT be present (information disclosure)
const DANGEROUS_HEADERS = {
  'server': {
    name: 'Server',
    description: 'Reveals web server information',
    severity: 'low'
  },
  'x-powered-by': {
    name: 'X-Powered-By',
    description: 'Reveals technology stack',
    severity: 'low'
  },
  'x-aspnet-version': {
    name: 'X-AspNet-Version',
    description: 'Reveals ASP.NET version',
    severity: 'medium'
  },
  'x-aspnetmvc-version': {
    name: 'X-AspNetMvc-Version',
    description: 'Reveals ASP.NET MVC version',
    severity: 'medium'
  }
};

class SecurityHeadersValidator {
  constructor(options = {}) {
    this.verbose = options.verbose || false;
    this.timeout = options.timeout || 5000;
    this.findings = [];
  }

  log(message) {
    if (this.verbose) {
      console.log(message);
    }
  }

  /**
   * Make HTTP request to check headers
   */
  async fetchHeaders(url) {
    try {
      const controller = new AbortController();
      const timeoutHandle = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, {
        method: 'HEAD', // Only fetch headers, not body
        signal: controller.signal,
        redirect: 'manual' // Don't follow redirects
      });

      clearTimeout(timeoutHandle);

      return {
        url: response.url,
        status: response.status,
        headers: Object.fromEntries(response.headers.entries()),
        isHttps: url.startsWith('https://')
      };
    } catch (error) {
      return {
        error: error.message,
        url
      };
    }
  }

  /**
   * Add a finding
   */
  addFinding(finding) {
    this.findings.push({
      timestamp: new Date().toISOString(),
      ...finding
    });
  }

  /**
   * Validate security headers
   */
  validateHeaders(responseData) {
    const { url, headers, isHttps } = responseData;

    this.log(`Validating security headers for: ${url}\n`);

    // Check for missing required headers
    for (const [key, config] of Object.entries(SECURITY_HEADERS)) {
      // Skip HTTPS-only headers for HTTP sites
      if (config.httpsOnly && !isHttps) {
        continue;
      }

      const headerValue = headers[key];

      if (!headerValue) {
        if (config.required) {
          this.addFinding({
            type: 'missing_header',
            severity: config.severity,
            header: config.name,
            description: `Missing required header: ${config.name}`,
            recommendation: `Add header: ${config.name}: ${config.recommended[0]}`,
            details: config.description
          });
        }
      } else {
        // Header is present, validate value
        const isValid = config.recommended.some(rec => 
          headerValue.toLowerCase().includes(rec.toLowerCase())
        );

        if (!isValid && config.required) {
          this.addFinding({
            type: 'invalid_header',
            severity: 'medium',
            header: config.name,
            currentValue: headerValue,
            description: `Header ${config.name} has non-standard value`,
            recommendation: `Consider using: ${config.recommended.join(' or ')}`,
            details: config.description
          });
        }

        if (config.deprecated) {
          this.addFinding({
            type: 'deprecated_header',
            severity: 'info',
            header: config.name,
            description: `Header ${config.name} is deprecated`,
            note: config.note
          });
        }
      }
    }

    // Check for dangerous headers (information disclosure)
    for (const [key, config] of Object.entries(DANGEROUS_HEADERS)) {
      if (headers[key]) {
        this.addFinding({
          type: 'information_disclosure',
          severity: config.severity,
          header: config.name,
          currentValue: headers[key],
          description: config.description,
          recommendation: `Remove or obfuscate the ${config.name} header`
        });
      }
    }

    // Check for insecure CSP directives
    const csp = headers['content-security-policy'];
    if (csp) {
      if (csp.includes("'unsafe-inline'") || csp.includes("'unsafe-eval'")) {
        this.addFinding({
          type: 'weak_csp',
          severity: 'medium',
          header: 'Content-Security-Policy',
          currentValue: csp,
          description: 'CSP contains unsafe directives',
          recommendation: "Remove 'unsafe-inline' and 'unsafe-eval' directives when possible"
        });
      }
    }

    // Check HSTS settings
    const hsts = headers['strict-transport-security'];
    if (hsts && isHttps) {
      const maxAge = hsts.match(/max-age=(\d+)/);
      if (maxAge && parseInt(maxAge[1]) < 31536000) {
        this.addFinding({
          type: 'weak_hsts',
          severity: 'medium',
          header: 'Strict-Transport-Security',
          currentValue: hsts,
          description: 'HSTS max-age is less than 1 year',
          recommendation: 'Use max-age=31536000 (1 year) or higher'
        });
      }
    }
  }

  /**
   * Validate a URL
   */
  async validate(url) {
    this.findings = [];

    console.log(`🔒 Validating security headers for: ${url}\n`);

    const responseData = await this.fetchHeaders(url);

    if (responseData.error) {
      console.error(`❌ Failed to fetch headers: ${responseData.error}`);
      return null;
    }

    this.validateHeaders(responseData);

    return this.generateReport(responseData);
  }

  /**
   * Generate report
   */
  generateReport(responseData) {
    const summary = {
      url: responseData.url,
      isHttps: responseData.isHttps,
      status: responseData.status,
      totalIssues: this.findings.length,
      bySeverity: {
        high: this.findings.filter(f => f.severity === 'high').length,
        medium: this.findings.filter(f => f.severity === 'medium').length,
        low: this.findings.filter(f => f.severity === 'low').length,
        info: this.findings.filter(f => f.severity === 'info').length
      },
      score: this.calculateScore()
    };

    return {
      summary,
      findings: this.findings,
      headers: responseData.headers,
      scanDate: new Date().toISOString()
    };
  }

  /**
   * Calculate security score (0-100)
   */
  calculateScore() {
    const weights = {
      high: -20,
      medium: -10,
      low: -5,
      info: -1
    };

    let score = 100;
    for (const finding of this.findings) {
      score += weights[finding.severity] || 0;
    }

    return Math.max(0, score);
  }

  /**
   * Print formatted report
   */
  printReport(report = null) {
    if (!report) return;

    console.log('\n' + '='.repeat(70));
    console.log('           SECURITY HEADERS VALIDATION REPORT');
    console.log('='.repeat(70) + '\n');

    console.log(`URL: ${report.summary.url}`);
    console.log(`HTTPS: ${report.summary.isHttps ? '✅ Yes' : '❌ No'}`);
    console.log(`Status: ${report.summary.status}`);
    console.log(`\nSecurity Score: ${report.summary.score}/100`);

    const scoreIcon = report.summary.score >= 80 ? '🟢' : 
                      report.summary.score >= 60 ? '🟡' : 
                      report.summary.score >= 40 ? '🟠' : '🔴';
    console.log(`${scoreIcon} ${this.getScoreRating(report.summary.score)}\n`);

    console.log('Issues by Severity:');
    console.log(`  🔴 High:   ${report.summary.bySeverity.high}`);
    console.log(`  🟠 Medium: ${report.summary.bySeverity.medium}`);
    console.log(`  🟡 Low:    ${report.summary.bySeverity.low}`);
    console.log(`  ℹ️  Info:   ${report.summary.bySeverity.info}`);
    console.log('');

    if (report.findings.length === 0) {
      console.log('✅ All security headers are properly configured!\n');
      return;
    }

    console.log('Findings:\n');

    report.findings.forEach((finding, idx) => {
      const severityIcon = {
        high: '🔴',
        medium: '🟠',
        low: '🟡',
        info: 'ℹ️'
      }[finding.severity] || '⚪';

      console.log(`${idx + 1}. ${severityIcon} ${finding.header || 'Security Issue'} [${finding.severity.toUpperCase()}]`);
      console.log(`   Type: ${finding.type.replace('_', ' ')}`);
      console.log(`   Description: ${finding.description}`);
      
      if (finding.currentValue) {
        console.log(`   Current: ${finding.currentValue}`);
      }
      
      if (finding.recommendation) {
        console.log(`   💡 ${finding.recommendation}`);
      }
      
      if (finding.note) {
        console.log(`   Note: ${finding.note}`);
      }
      
      console.log('');
    });

    console.log('='.repeat(70) + '\n');
  }

  /**
   * Get rating based on score
   */
  getScoreRating(score) {
    if (score >= 90) return 'Excellent';
    if (score >= 80) return 'Good';
    if (score >= 60) return 'Fair';
    if (score >= 40) return 'Poor';
    return 'Critical';
  }
}

// CLI interface
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    console.log(`
Security Headers Validator

Usage:
  security-headers-validator.mjs <url> [options]

Options:
  --verbose, -v    Enable verbose output
  --json           Output results as JSON
  --timeout <ms>   Request timeout in milliseconds (default: 5000)

Examples:
  security-headers-validator.mjs http://localhost:8080
  security-headers-validator.mjs https://example.com --verbose
  security-headers-validator.mjs https://example.com --json
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

  const validator = new SecurityHeadersValidator({ verbose, timeout });

  validator.validate(url)
    .then(report => {
      if (!report) {
        process.exit(1);
      }

      if (json) {
        console.log(JSON.stringify(report, null, 2));
      } else {
        validator.printReport(report);
      }

      // Exit with error code if security score is below 60
      if (report.summary.score < 60) {
        process.exit(1);
      }
    })
    .catch(error => {
      console.error('Error during validation:', error.message);
      process.exit(1);
    });
}

export default SecurityHeadersValidator;
