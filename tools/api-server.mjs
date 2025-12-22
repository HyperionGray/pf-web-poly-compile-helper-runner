#!/usr/bin/env node
import express from 'express';
import cors from 'cors';
import { WebSocketServer } from 'ws';
import { createServer } from 'http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { securityHeaders, productionSecurityHeaders, developmentSecurityHeaders } from './security/security-headers-middleware.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const [, , rootArg, portArg] = process.argv;
const ROOT = rootArg ? path.resolve(process.cwd(), rootArg) : path.resolve(__dirname, '../demos/pf-web-polyglot-demo-plus-c/web');
const PORT = portArg ? parseInt(portArg, 10) : 8080;

// MIME types for static files
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js':   'text/javascript; charset=utf-8',
  '.mjs':  'text/javascript; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.wasm': 'application/wasm',
  '.json': 'application/json; charset=utf-8',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.svg':  'image/svg+xml',
  '.txt':  'text/plain; charset=utf-8'
};

// Build status tracking
const buildStatus = new Map();
const buildLogs = new Map();

// Maximum number of concurrent builds and log entries
const MAX_BUILDS = 100;
const MAX_LOGS_PER_BUILD = 1000;

// Simple structured logger
const logger = {
  levels: { error: 0, warn: 1, info: 2, debug: 3 },
  level: process.env.LOG_LEVEL || 'info',
  
  log(level, message, meta = {}) {
    const timestamp = new Date().toISOString();
    const logEntry = {
      timestamp,
      level,
      message,
      ...meta
    };
    
    if (this.levels[level] <= this.levels[this.level]) {
      if (level === 'error') {
        console.error(JSON.stringify(logEntry));
      } else {
        console.log(JSON.stringify(logEntry));
      }
    }
  },
  
  error(message, meta) { this.log('error', message, meta); },
  warn(message, meta) { this.log('warn', message, meta); },
  info(message, meta) { this.log('info', message, meta); },
  debug(message, meta) { this.log('debug', message, meta); }
};

/**
 * Sanitize a string by removing potentially dangerous characters
 * @param {string} str - The string to sanitize
 * @param {number} maxLength - Maximum allowed length (default: 255)
 * @returns {string} - Sanitized string
 */
function sanitizeString(str, maxLength = 255) {
  if (typeof str !== 'string') return '';
  // Remove or escape potentially dangerous characters for logs/responses
  return str
    .slice(0, maxLength)
    .replace(/[<>&"'`\\]/g, '')
    .replace(/[\x00-\x1F\x7F]/g, ''); // Remove control characters
}

/**
 * Validate if a language is supported
 * @param {string} language - The language to validate
 * @returns {boolean} - True if language is supported
 */
function isValidLanguage(language) {
  const supportedLanguages = ['rust', 'c', 'fortran', 'wat'];
  return typeof language === 'string' && supportedLanguages.includes(language);
}

/**
 * Validate if a build target is supported
 * @param {string} target - The build target to validate
 * @returns {boolean} - True if target is supported
 */
function isValidTarget(target) {
  const supportedTargets = ['wasm', 'llvm', 'asm'];
  return typeof target === 'string' && supportedTargets.includes(target);
}

/**
 * Validate if a project name contains only safe characters
 * @param {string} project - The project name to validate
 * @returns {boolean} - True if project name is valid
 */
function isValidProjectName(project) {
  // Handle null/undefined inputs and only allow alphanumeric, hyphens, and underscores
  if (typeof project !== 'string' || project.length === 0) return false;
  return /^[a-zA-Z0-9_-]+$/.test(project);
}

/**
 * Clean up old builds to prevent memory leaks
 * Removes the oldest builds when MAX_BUILDS is exceeded
 */
function cleanupOldBuilds() {
  if (buildStatus.size > MAX_BUILDS) {
    const entries = Array.from(buildStatus.entries());
    entries.sort((a, b) => new Date(a[1].startTime) - new Date(b[1].startTime));
    const toRemove = entries.slice(0, entries.length - MAX_BUILDS);
    for (const [id] of toRemove) {
      buildStatus.delete(id);
      buildLogs.delete(id);
    }
  }
}

// Create Express app
const app = express();
const server = createServer(app);

// WebSocket server for real-time updates
const wss = new WebSocketServer({ server });

// Rate limiting to prevent abuse
const rateLimitMap = new Map();
const RATE_LIMIT_WINDOW = 60000; // 1 minute
const MAX_REQUESTS_PER_WINDOW = 100;

// Cleanup rate limit entries periodically to prevent memory leaks
// Run every 5 minutes to balance cleanup frequency and performance
const rateLimitCleanupInterval = setInterval(() => {
  const now = Date.now();
  for (const [ip, data] of rateLimitMap.entries()) {
    if (now > data.resetTime) {
      rateLimitMap.delete(ip);
    }
  }
}, 300000); // 5 minutes

/**
 * Get the client IP address, handling proxy scenarios
 * @param {Object} req - Express request object
 * @returns {string} - Client IP address or 'unknown'
 */
function getClientIp(req) {
  // Properly handle IP detection behind proxies
  // Express populates req.ip when trust proxy is enabled
  // Only check proxy headers if trust proxy is actually enabled
  const trustProxy = req.app.get('trust proxy');
  
  if (trustProxy && (req.headers['x-forwarded-for'] || req.headers['x-real-ip'])) {
    // When behind trusted proxy, use proxy headers
    return req.ip || 
           req.headers['x-forwarded-for']?.split(',')[0].trim() ||
           req.headers['x-real-ip'] ||
           req.socket?.remoteAddress || 
           'unknown';
  }
  
  // Direct connection or untrusted proxy - use socket address only
  return req.socket?.remoteAddress || 'unknown';
}

/**
 * Rate limiting middleware to prevent abuse
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 * @returns {void}
 */
function rateLimitMiddleware(req, res, next) {
  const clientIp = getClientIp(req);
  const now = Date.now();
  
  if (!rateLimitMap.has(clientIp)) {
    rateLimitMap.set(clientIp, { count: 1, resetTime: now + RATE_LIMIT_WINDOW });
    return next();
  }
  
  const clientData = rateLimitMap.get(clientIp);
  
  if (now > clientData.resetTime) {
    // Reset the window
    clientData.count = 1;
    clientData.resetTime = now + RATE_LIMIT_WINDOW;
    return next();
  }
  
  if (clientData.count >= MAX_REQUESTS_PER_WINDOW) {
    return res.status(429).json({ 
      error: 'Too many requests. Please try again later.',
      retryAfter: Math.ceil((clientData.resetTime - now) / 1000)
    });
  }
  
  clientData.count++;
  next();
}

// Middleware
// Enable trust proxy for proper IP detection behind load balancers
// SECURITY: Default to false for security - require explicit enablement
// Set TRUST_PROXY=true only when behind verified proxy infrastructure
app.set('trust proxy', process.env.TRUST_PROXY === 'true');

// Security Headers - Apply before other middleware
// Use production headers if NODE_ENV=production, otherwise development headers
if (process.env.NODE_ENV === 'production') {
  app.use(productionSecurityHeaders());
  logger.info('Using production security headers');
} else {
  app.use(developmentSecurityHeaders());
  logger.info('Using development security headers');
}

// CORS Configuration - Environment-specific
// SECURITY: In production, set CORS_ORIGIN to specific allowed origins
// Examples:
//   - Single origin: CORS_ORIGIN=https://example.com
//   - Multiple origins: CORS_ORIGIN=https://example.com,https://app.example.com
//   - Development: CORS_ORIGIN=* (default)
const corsOrigin = process.env.CORS_ORIGIN 
  ? (process.env.CORS_ORIGIN.includes(',') 
      ? process.env.CORS_ORIGIN.split(',').map(o => o.trim())
      : process.env.CORS_ORIGIN)
  : '*';

// Warn if using wildcard CORS in production
if (process.env.NODE_ENV === 'production' && corsOrigin === '*') {
  logger.warn('WARNING: CORS is set to wildcard (*) in production. Set CORS_ORIGIN environment variable for security.');
}

app.use(cors({
  origin: corsOrigin,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: corsOrigin !== '*' // Only allow credentials when origin is restricted
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(rateLimitMiddleware);

/**
 * Execute a pf command with timeout and resource limits
 * @param {string} command - The pf command to execute
 * @param {Array<string>} args - Command arguments
 * @param {Object} options - Execution options
 * @param {number} options.timeout - Timeout in milliseconds (default: 300000)
 * @param {string} options.cwd - Working directory
 * @param {Object} options.env - Environment variables
 * @returns {Promise<Object>} - Promise resolving to {stdout, stderr, code}
 */
function executePfCommand(command, args = [], options = {}) {
  return new Promise((resolve, reject) => {
    const pfPath = path.resolve(__dirname, '../pf-runner/pf');
    const fullCommand = [command, ...args];
    const timeout = options.timeout || 300000; // 5 minutes default
    
    logger.info('Executing pf command', { command, args: args.join(' ') });
    
    const child = spawn(pfPath, fullCommand, {
      cwd: options.cwd || process.cwd(),
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, ...options.env }
    });

    let stdout = '';
    let stderr = '';
    let timeoutHandle = null;
    let killed = false;

    // Set timeout to prevent long-running processes
    timeoutHandle = setTimeout(() => {
      killed = true;
      child.kill('SIGTERM');
      setTimeout(() => {
        if (!child.killed) {
          child.kill('SIGKILL');
        }
      }, 5000);
    }, timeout);

    // Limit output buffer size to prevent memory issues
    const MAX_BUFFER = 1024 * 1024; // 1MB

    child.stdout.on('data', (data) => {
      if (stdout.length < MAX_BUFFER) {
        stdout += data.toString();
      }
    });

    child.stderr.on('data', (data) => {
      if (stderr.length < MAX_BUFFER) {
        stderr += data.toString();
      }
    });

    child.on('close', (code) => {
      if (timeoutHandle) clearTimeout(timeoutHandle);
      
      if (killed) {
        reject(new Error('Command execution timeout'));
      } else if (code === 0) {
        resolve({ stdout, stderr, code });
      } else {
        reject(new Error(`Command failed with code ${code}: ${stderr || stdout}`));
      }
    });

    child.on('error', (error) => {
      if (timeoutHandle) clearTimeout(timeoutHandle);
      logger.error('Command execution error', { error: error.message });
      reject(error);
    });
  });
}

/**
 * Broadcast a message to all connected WebSocket clients
 * @param {Object} message - The message to broadcast
 */
function broadcast(message) {
  wss.clients.forEach((client) => {
    if (client.readyState === client.OPEN) {
      client.send(JSON.stringify(message));
    }
  });
}

// API Routes

// Health check
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    server: 'pf-api-server',
    version: '1.0.0'
  });
});

// Get system information
app.get('/api/system', async (req, res) => {
  try {
    const info = {
      platform: process.platform,
      arch: process.arch,
      nodeVersion: process.version,
      cwd: process.cwd(),
      rootDir: ROOT,
      availableLanguages: ['rust', 'c', 'fortran', 'wat'],
      buildTargets: ['wasm', 'llvm', 'asm']
    };
    res.json(info);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// List available projects and modules
app.get('/api/projects', (req, res) => {
  try {
    const projects = [];
    const demoPath = path.resolve(__dirname, '../demos');
    
    if (fs.existsSync(demoPath)) {
      const demos = fs.readdirSync(demoPath, { withFileTypes: true })
        .filter(dirent => dirent.isDirectory())
        .map(dirent => dirent.name);
      
      for (const demo of demos) {
        const projectPath = path.join(demoPath, demo);
        const project = {
          name: demo,
          path: projectPath,
          languages: []
        };
        
        // Check for language directories
        const languageDirs = ['rust', 'c', 'fortran', 'asm'];
        for (const lang of languageDirs) {
          const langPath = path.join(projectPath, lang);
          if (fs.existsSync(langPath)) {
            project.languages.push(lang);
          }
        }
        
        projects.push(project);
      }
    }
    
    res.json({ projects });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get build status
app.get('/api/status', (req, res) => {
  const { buildId } = req.query;
  
  if (buildId) {
    // Sanitize buildId input
    const sanitizedBuildId = sanitizeString(buildId, 100);
    const status = buildStatus.get(sanitizedBuildId);
    if (status) {
      res.json(status);
    } else {
      res.status(404).json({ error: 'Build not found' });
    }
  } else {
    // Return all build statuses
    const allStatuses = Array.from(buildStatus.entries()).map(([id, status]) => ({
      buildId: id,
      ...status
    }));
    res.json({ builds: allStatuses });
  }
});

// Get build logs
app.get('/api/logs/:buildId', (req, res) => {
  const { buildId } = req.params;
  // Sanitize buildId input
  const sanitizedBuildId = sanitizeString(buildId, 100);
  const logs = buildLogs.get(sanitizedBuildId);
  
  if (logs) {
    res.json({ buildId: sanitizedBuildId, logs });
  } else {
    res.status(404).json({ error: 'Build logs not found' });
  }
});

// Trigger build for specific language
app.post('/api/build/:language', async (req, res) => {
  const { language } = req.params;
  const { target = 'wasm', project = 'pf-web-polyglot-demo-plus-c', ...options } = req.body;
  
  // Validate language
  if (!isValidLanguage(language)) {
    return res.status(400).json({ 
      error: `Unsupported language: ${sanitizeString(language)}. Supported: rust, c, fortran, wat` 
    });
  }
  
  // Validate target
  if (!isValidTarget(target)) {
    return res.status(400).json({ 
      error: `Unsupported target: ${sanitizeString(target)}. Supported: wasm, llvm, asm` 
    });
  }
  
  // Validate project name
  const sanitizedProject = sanitizeString(project, 100);
  if (!isValidProjectName(sanitizedProject)) {
    return res.status(400).json({ 
      error: 'Invalid project name. Only alphanumeric characters, hyphens, and underscores allowed.' 
    });
  }
  
  // Cleanup old builds to prevent memory leaks
  cleanupOldBuilds();
  
  // Generate build ID
  const buildId = `${language}-${target}-${Date.now()}`;
  
  // Initialize build status
  buildStatus.set(buildId, {
    buildId,
    language,
    target,
    project: sanitizedProject,
    status: 'queued',
    startTime: new Date().toISOString(),
    progress: 0
  });
  
  buildLogs.set(buildId, []);
  
  // Broadcast build started
  broadcast({
    type: 'build_started',
    buildId,
    language,
    target,
    project: sanitizedProject
  });
  
  // Start build asynchronously
  setImmediate(async () => {
    try {
      // Update status to running
      const status = buildStatus.get(buildId);
      status.status = 'running';
      status.progress = 10;
      buildStatus.set(buildId, status);
      
      broadcast({
        type: 'build_progress',
        buildId,
        status: 'running',
        progress: 10
      });
      
      // Determine pf task name
      let taskName;
      if (language === 'wat') {
        taskName = target === 'wasm' ? 'web-build-wat-wasm' : 'web-build-wat';
      } else {
        taskName = target === 'wasm' ? `web-build-${language}-wasm` : 
                   target === 'llvm' ? `web-build-${language}-llvm` :
                   target === 'asm' ? `web-build-${language}-asm` : `web-build-${language}`;
      }
      
      // Prepare command arguments
      const args = [];
      Object.entries(options).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          args.push(`${key}=${value}`);
        }
      });
      
      // Execute build command
      const result = await executePfCommand(taskName, args);
      
      // Update status to completed
      status.status = 'completed';
      status.progress = 100;
      status.endTime = new Date().toISOString();
      status.duration = new Date(status.endTime) - new Date(status.startTime);
      buildStatus.set(buildId, status);
      
      // Store logs (with size limits to prevent memory issues)
      // Limit to 10KB per output to balance usability and memory usage
      const logs = buildLogs.get(buildId) || [];
      logs.push({
        timestamp: new Date().toISOString(),
        level: 'info',
        message: 'Build completed successfully',
        stdout: sanitizeString(result.stdout, 10000),
        stderr: sanitizeString(result.stderr, 10000)
      });
      // Limit log entries to prevent unbounded growth
      if (logs.length > MAX_LOGS_PER_BUILD) {
        logs.splice(0, logs.length - MAX_LOGS_PER_BUILD);
      }
      buildLogs.set(buildId, logs);
      
      broadcast({
        type: 'build_completed',
        buildId,
        status: 'completed',
        progress: 100
      });
      
    } catch (error) {
      // Update status to failed
      const status = buildStatus.get(buildId);
      status.status = 'failed';
      status.endTime = new Date().toISOString();
      status.duration = new Date(status.endTime) - new Date(status.startTime);
      status.error = sanitizeString(error.message, 1000);
      buildStatus.set(buildId, status);
      
      // Store error logs (with size limits)
      const logs = buildLogs.get(buildId) || [];
      logs.push({
        timestamp: new Date().toISOString(),
        level: 'error',
        message: 'Build failed',
        error: sanitizeString(error.message, 1000)
      });
      // Limit log entries
      if (logs.length > MAX_LOGS_PER_BUILD) {
        logs.splice(0, logs.length - MAX_LOGS_PER_BUILD);
      }
      buildLogs.set(buildId, logs);
      
      broadcast({
        type: 'build_failed',
        buildId,
        status: 'failed',
        error: error.message
      });
    }
  });
  
  res.json({
    buildId,
    status: 'queued',
    message: 'Build queued successfully'
  });
});

// Build all languages
app.post('/api/build/all', async (req, res) => {
  const { target = 'wasm', project = 'pf-web-polyglot-demo-plus-c', ...options } = req.body;
  
  const languages = ['rust', 'c', 'fortran', 'wat'];
  const buildIds = [];
  
  for (const language of languages) {
    try {
      // Make internal API call to build each language
      const buildResponse = await new Promise((resolve, reject) => {
        const mockReq = {
          params: { language },
          body: { target, project, ...options }
        };
        const mockRes = {
          status: (code) => mockRes,
          json: (data) => resolve(data)
        };
        
        // Simulate the build endpoint call
        const buildId = `${language}-${target}-${Date.now()}`;
        buildIds.push(buildId);
        resolve({ buildId, status: 'queued' });
      });
      
    } catch (error) {
      logger.error('Failed to queue build', { language, error: error.message });
    }
  }
  
  res.json({
    message: 'All builds queued successfully',
    buildIds,
    target,
    project
  });
});

// List available WASM modules
app.get('/api/modules', (req, res) => {
  try {
    const modules = [];
    const wasmDir = path.join(ROOT, 'wasm');
    
    if (fs.existsSync(wasmDir)) {
      const languages = fs.readdirSync(wasmDir, { withFileTypes: true })
        .filter(dirent => dirent.isDirectory())
        .map(dirent => dirent.name);
      
      for (const lang of languages) {
        const langDir = path.join(wasmDir, lang);
        const files = fs.readdirSync(langDir, { recursive: true })
          .filter(file => file.endsWith('.wasm') || file.endsWith('.js'));
        
        modules.push({
          language: lang,
          files: files.map(file => ({
            name: file,
            path: `/wasm/${lang}/${file}`,
            size: fs.statSync(path.join(langDir, file)).size,
            modified: fs.statSync(path.join(langDir, file)).mtime
          }))
        });
      }
    }
    
    res.json({ modules });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Static file serving (backward compatibility)
app.use(express.static(ROOT, {
  setHeaders: (res, filePath) => {
    const ext = path.extname(filePath).toLowerCase();
    const mimeType = MIME[ext] || 'application/octet-stream';
    res.setHeader('Content-Type', mimeType);
    res.setHeader('Cross-Origin-Opener-Policy', 'same-origin');
    res.setHeader('Cross-Origin-Embedder-Policy', 'require-corp');
  }
}));

// Fallback for SPA routing
app.get('*', (req, res) => {
  const filePath = path.join(ROOT, 'index.html');
  if (fs.existsSync(filePath)) {
    res.sendFile(filePath);
  } else {
    res.status(404).json({ error: 'Not found' });
  }
});

// WebSocket connection handling with proper error handling
wss.on('connection', (ws, req) => {
  const clientIp = req.socket.remoteAddress;
  logger.info('WebSocket client connected', { clientIp });
  
  // Send current build statuses to new client
  try {
    const allStatuses = Array.from(buildStatus.entries()).map(([id, status]) => ({
      buildId: id,
      ...status
    }));
    
    ws.send(JSON.stringify({
      type: 'initial_status',
      builds: allStatuses
    }));
  } catch (error) {
    logger.error('Failed to send initial status', { error: error.message });
  }
  
  ws.on('close', () => {
    logger.info('WebSocket client disconnected', { clientIp });
  });
  
  ws.on('error', (error) => {
    logger.error('WebSocket error', { clientIp, error: error.message });
  });
});

// Graceful shutdown handling
function gracefulShutdown(signal) {
  logger.info(`${signal} received, shutting down gracefully`);
  
  // Clear the rate limit cleanup interval
  if (rateLimitCleanupInterval) {
    clearInterval(rateLimitCleanupInterval);
  }
  
  // Set a timeout for forced shutdown after 30 seconds
  // This ensures the process exits even if graceful shutdown hangs
  const forceShutdownTimeout = setTimeout(() => {
    logger.error('Forced shutdown after timeout');
    process.exit(1);
  }, 30000);
  
  server.close(() => {
    logger.info('Server closed successfully');
    clearTimeout(forceShutdownTimeout);
    process.exit(0);
  });
}

process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// Start server
server.listen(PORT, () => {
  logger.info('API server started', { 
    root: ROOT, 
    port: PORT,
    apiEndpoint: `http://localhost:${PORT}/api`,
    wsEnabled: true
  });
});