/**
 * API Server Middleware Enhancements
 * 
 * Implements Amazon Q Code Review recommendations:
 * - Performance: Response caching to reduce redundant computations
 * - Architecture: Centralized error handling
 * - Security: Request validation and sanitization
 */

/**
 * Simple in-memory cache with TTL support
 */
export class ResponseCache {
  constructor(options = {}) {
    this.cache = new Map();
    this.ttl = options.ttl || 60000; // Default 1 minute
    this.maxSize = options.maxSize || 100; // Maximum number of cached responses
  }

  /**
   * Generate cache key from request
   */
  generateKey(req) {
    return `${req.method}:${req.path}:${JSON.stringify(req.query)}`;
  }

  /**
   * Get cached response if available and not expired
   */
  get(key) {
    const entry = this.cache.get(key);
    
    if (!entry) {
      return null;
    }

    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }

    entry.hits++;
    return entry.data;
  }

  /**
   * Store response in cache
   */
  set(key, data) {
    // Implement LRU-style eviction if cache is full
    if (this.cache.size >= this.maxSize) {
      // Remove oldest entry
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }

    this.cache.set(key, {
      data,
      expiresAt: Date.now() + this.ttl,
      hits: 0,
      createdAt: Date.now()
    });
  }

  /**
   * Clear entire cache
   */
  clear() {
    this.cache.clear();
  }

  /**
   * Clear expired entries
   */
  cleanup() {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Get cache statistics
   */
  getStats() {
    let totalHits = 0;
    let oldestEntry = null;
    
    for (const [key, entry] of this.cache.entries()) {
      totalHits += entry.hits;
      if (!oldestEntry || entry.createdAt < oldestEntry.createdAt) {
        oldestEntry = entry;
      }
    }

    return {
      size: this.cache.size,
      maxSize: this.maxSize,
      totalHits,
      ttl: this.ttl
    };
  }
}

/**
 * Cache middleware for GET requests
 */
export function cacheMiddleware(cache, options = {}) {
  const cachePaths = options.cachePaths || ['/api/system', '/api/projects', '/api/modules'];
  const skipPaths = options.skipPaths || ['/api/build'];

  return (req, res, next) => {
    // Only cache GET requests
    if (req.method !== 'GET') {
      return next();
    }

    // Skip certain paths
    if (skipPaths.some(path => req.path.startsWith(path))) {
      return next();
    }

    // Only cache specific paths if configured
    if (cachePaths.length > 0 && !cachePaths.some(path => req.path.startsWith(path))) {
      return next();
    }

    const key = cache.generateKey(req);
    const cached = cache.get(key);

    if (cached) {
      // Add cache header
      res.set('X-Cache', 'HIT');
      return res.json(cached);
    }

    // Intercept response to cache it
    const originalJson = res.json.bind(res);
    res.json = function(data) {
      // Only cache successful responses
      if (res.statusCode === 200) {
        cache.set(key, data);
      }
      res.set('X-Cache', 'MISS');
      return originalJson(data);
    };

    next();
  };
}

/**
 * Global error handler middleware
 */
export function errorHandler() {
  return (err, req, res, next) => {
    // Log error details
    console.error('Error:', {
      message: err.message,
      stack: process.env.NODE_ENV === 'development' ? err.stack : undefined,
      path: req.path,
      method: req.method,
      timestamp: new Date().toISOString()
    });

    // Determine status code
    const statusCode = err.statusCode || err.status || 500;

    // Prepare error response
    const errorResponse = {
      error: {
        message: err.message || 'Internal server error',
        code: err.code || 'INTERNAL_ERROR',
        timestamp: new Date().toISOString()
      }
    };

    // Include stack trace in development mode
    if (process.env.NODE_ENV === 'development') {
      errorResponse.error.stack = err.stack;
    }

    // Send error response
    res.status(statusCode).json(errorResponse);
  };
}

/**
 * Request validation middleware
 */
export function validateRequest(schema) {
  return (req, res, next) => {
    const errors = [];

    // Validate body if schema provided
    if (schema.body) {
      for (const [field, rules] of Object.entries(schema.body)) {
        const value = req.body?.[field];

        // Required field check
        if (rules.required && (value === undefined || value === null || value === '')) {
          errors.push(`Field '${field}' is required`);
          continue;
        }

        // Type check
        if (value !== undefined && rules.type) {
          const actualType = Array.isArray(value) ? 'array' : typeof value;
          if (actualType !== rules.type) {
            errors.push(`Field '${field}' must be of type ${rules.type}`);
          }
        }

        // Enum check
        if (value !== undefined && rules.enum) {
          if (!rules.enum.includes(value)) {
            errors.push(`Field '${field}' must be one of: ${rules.enum.join(', ')}`);
          }
        }

        // Pattern check
        if (value !== undefined && rules.pattern) {
          if (typeof value === 'string' && !rules.pattern.test(value)) {
            errors.push(`Field '${field}' has invalid format`);
          }
        }

        // Min/Max length check
        if (value !== undefined && typeof value === 'string') {
          if (rules.minLength && value.length < rules.minLength) {
            errors.push(`Field '${field}' must be at least ${rules.minLength} characters`);
          }
          if (rules.maxLength && value.length > rules.maxLength) {
            errors.push(`Field '${field}' must not exceed ${rules.maxLength} characters`);
          }
        }
      }
    }

    // Validate query parameters if schema provided
    if (schema.query) {
      for (const [param, rules] of Object.entries(schema.query)) {
        const value = req.query?.[param];

        if (rules.required && !value) {
          errors.push(`Query parameter '${param}' is required`);
        }

        if (value && rules.enum && !rules.enum.includes(value)) {
          errors.push(`Query parameter '${param}' must be one of: ${rules.enum.join(', ')}`);
        }
      }
    }

    if (errors.length > 0) {
      return res.status(400).json({
        error: {
          message: 'Validation failed',
          code: 'VALIDATION_ERROR',
          details: errors
        }
      });
    }

    next();
  };
}

/**
 * Security headers middleware
 */
export function securityHeaders() {
  return (req, res, next) => {
    // Prevent clickjacking
    res.setHeader('X-Frame-Options', 'DENY');
    
    // Prevent MIME type sniffing
    res.setHeader('X-Content-Type-Options', 'nosniff');
    
    // Enable XSS filter
    res.setHeader('X-XSS-Protection', '1; mode=block');
    
    // Content Security Policy
    res.setHeader('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'");
    
    // Referrer policy
    res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
    
    // Permissions policy
    res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
    
    // Remove server header to hide technology stack
    res.removeHeader('X-Powered-By');
    
    next();
  };
}

/**
 * Request logging middleware
 */
export function requestLogger() {
  return (req, res, next) => {
    const start = Date.now();

    // Log request
    console.log(JSON.stringify({
      type: 'request',
      method: req.method,
      path: req.path,
      query: req.query,
      ip: req.ip,
      timestamp: new Date().toISOString()
    }));

    // Capture response
    const originalSend = res.send.bind(res);
    res.send = function(data) {
      const duration = Date.now() - start;
      
      console.log(JSON.stringify({
        type: 'response',
        method: req.method,
        path: req.path,
        statusCode: res.statusCode,
        duration,
        timestamp: new Date().toISOString()
      }));

      return originalSend(data);
    };

    next();
  };
}

/**
 * Async handler wrapper to catch errors in async route handlers
 */
export function asyncHandler(fn) {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

export default {
  ResponseCache,
  cacheMiddleware,
  errorHandler,
  validateRequest,
  securityHeaders,
  requestLogger,
  asyncHandler
};
