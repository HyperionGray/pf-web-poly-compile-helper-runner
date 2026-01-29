/**
 * Security Headers Middleware
 * 
 * This middleware adds comprehensive security headers to all HTTP responses
 * to protect against common web vulnerabilities.
 * 
 * Based on OWASP recommendations and security best practices.
 */

/**
 * Security headers middleware factory
 * @param {Object} options - Configuration options
 * @param {boolean} options.enableHSTS - Enable HSTS header (default: true for HTTPS)
 * @param {string} options.cspPolicy - Custom CSP policy (optional)
 * @param {boolean} options.enableFrameGuard - Enable X-Frame-Options (default: true)
 * @returns {Function} Express middleware function
 */
export function securityHeaders(options = {}) {
  const {
    enableHSTS = true,
    cspPolicy = null,
    enableFrameGuard = true,
    enableXSSProtection = true,
    enableNoSniff = true
  } = options;

  return function securityHeadersMiddleware(req, res, next) {
    // Prevent clickjacking attacks
    if (enableFrameGuard) {
      res.setHeader('X-Frame-Options', 'DENY');
    }

    // Prevent MIME type sniffing
    if (enableNoSniff) {
      res.setHeader('X-Content-Type-Options', 'nosniff');
    }

    // Note: X-XSS-Protection is deprecated and may introduce vulnerabilities in older browsers
    // Modern browsers rely on CSP for XSS protection. Only enable if needed for legacy browser support.
    if (enableXSSProtection) {
      res.setHeader('X-XSS-Protection', '1; mode=block');
    }

    // Content Security Policy
    // WARNING: Default CSP includes 'unsafe-inline' and 'unsafe-eval' for development convenience
    // These directives significantly weaken XSS protection and should NOT be used in production
    // Use productionSecurityHeaders() for production deployments
    const defaultCSP = [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'", // REMOVE unsafe-* for production!
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: https:",
      "font-src 'self' data:",
      "connect-src 'self'",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'"
    ].join('; ');

    res.setHeader('Content-Security-Policy', cspPolicy || defaultCSP);

    // HTTP Strict Transport Security (only for HTTPS connections)
    if (enableHSTS && (req.secure || req.headers['x-forwarded-proto'] === 'https')) {
      res.setHeader(
        'Strict-Transport-Security',
        'max-age=31536000; includeSubDomains; preload'
      );
    }

    // Referrer Policy - control referrer information
    res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');

    // Permissions Policy - control browser features
    res.setHeader(
      'Permissions-Policy',
      'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()'
    );

    // Remove X-Powered-By header to hide server information
    res.removeHeader('X-Powered-By');

    next();
  };
}

/**
 * Production-optimized security headers
 * More restrictive CSP and additional protections
 */
export function productionSecurityHeaders() {
  return securityHeaders({
    enableHSTS: true,
    cspPolicy: [
      "default-src 'self'",
      "script-src 'self'", // No unsafe-inline in production
      "style-src 'self'",
      "img-src 'self' data: https:",
      "font-src 'self'",
      "connect-src 'self'",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "upgrade-insecure-requests"
    ].join('; '),
    enableFrameGuard: true,
    enableXSSProtection: true,
    enableNoSniff: true
  });
}

/**
 * Development-friendly security headers
 * Allows inline scripts and styles for easier development
 */
export function developmentSecurityHeaders() {
  return securityHeaders({
    enableHSTS: false, // Often not using HTTPS in dev
    enableFrameGuard: true,
    enableXSSProtection: true,
    enableNoSniff: true
    // Uses default CSP with unsafe-inline
  });
}

/**
 * Validate security headers on a response
 * @param {Object} headers - HTTP response headers
 * @returns {Object} Validation results
 */
export function validateSecurityHeaders(headers) {
  const results = {
    valid: true,
    warnings: [],
    errors: [],
    recommendations: []
  };

  // Check for required headers
  const requiredHeaders = [
    'X-Frame-Options',
    'X-Content-Type-Options',
    'Content-Security-Policy'
  ];

  for (const header of requiredHeaders) {
    const headerKey = header.toLowerCase();
    if (!headers[headerKey]) {
      results.errors.push(`Missing required header: ${header}`);
      results.valid = false;
    }
  }

  // Check for recommended headers
  const recommendedHeaders = [
    'Strict-Transport-Security',
    'Referrer-Policy',
    'Permissions-Policy'
  ];

  for (const header of recommendedHeaders) {
    const headerKey = header.toLowerCase();
    if (!headers[headerKey]) {
      results.warnings.push(`Missing recommended header: ${header}`);
    }
  }

  // Check for security anti-patterns
  if (headers['x-powered-by']) {
    results.recommendations.push('Remove X-Powered-By header to avoid information disclosure');
  }

  // Check CSP policy strength
  const csp = headers['content-security-policy'];
  if (csp) {
    if (csp.includes("'unsafe-inline'") || csp.includes("'unsafe-eval'")) {
      results.warnings.push('CSP allows unsafe-inline or unsafe-eval - consider using nonces or hashes');
    }
    if (!csp.includes('frame-ancestors')) {
      results.recommendations.push('Consider adding frame-ancestors directive to CSP');
    }
  }

  // Check HSTS configuration
  const hsts = headers['strict-transport-security'];
  if (hsts) {
    if (!hsts.includes('includeSubDomains')) {
      results.recommendations.push('Consider adding includeSubDomains to HSTS');
    }
    if (!hsts.includes('preload')) {
      results.recommendations.push('Consider adding preload to HSTS for maximum protection');
    }
    const maxAge = hsts.match(/max-age=(\d+)/);
    if (maxAge && parseInt(maxAge[1]) < 31536000) {
      results.recommendations.push('HSTS max-age should be at least 1 year (31536000 seconds)');
    }
  }

  return results;
}

/**
 * Example usage in Express app:
 * 
 * import express from 'express';
 * import { securityHeaders, productionSecurityHeaders } from './security-headers-middleware.mjs';
 * 
 * const app = express();
 * 
 * // Use default security headers
 * app.use(securityHeaders());
 * 
 * // Or use production-optimized headers
 * if (process.env.NODE_ENV === 'production') {
 *   app.use(productionSecurityHeaders());
 * } else {
 *   app.use(developmentSecurityHeaders());
 * }
 * 
 * // Your routes here...
 */

export default securityHeaders;
