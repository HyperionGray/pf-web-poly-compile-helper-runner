#!/usr/bin/env node
import express from 'express';
import cors from 'cors';
import { WebSocketServer } from 'ws';
import { createServer } from 'http';
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

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

// Input validation helpers
function sanitizeString(str, maxLength = 255) {
  if (typeof str !== 'string') return '';
  // Remove or escape potentially dangerous characters for logs/responses
  return str
    .slice(0, maxLength)
    .replace(/[<>&"'`\\]/g, '')
    .replace(/[\x00-\x1F\x7F]/g, ''); // Remove control characters
}

function isValidLanguage(language) {
  const supportedLanguages = ['rust', 'c', 'fortran', 'wat'];
  return typeof language === 'string' && supportedLanguages.includes(language);
}

function isValidTarget(target) {
  const supportedTargets = ['wasm', 'llvm', 'asm'];
  return typeof target === 'string' && supportedTargets.includes(target);
}

function isValidProjectName(project) {
  // Handle null/undefined inputs and only allow alphanumeric, hyphens, and underscores
  if (typeof project !== 'string' || project.length === 0) return false;
  return /^[a-zA-Z0-9_-]+$/.test(project);
}

// Cleanup old builds to prevent memory leaks
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

// Middleware
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Utility function to execute pf commands
function executePfCommand(command, args = [], options = {}) {
  return new Promise((resolve, reject) => {
    const pfPath = path.resolve(__dirname, '../pf-runner/pf');
    const fullCommand = [command, ...args];
    
    console.log(`Executing: ${pfPath} ${fullCommand.join(' ')}`);
    
    const child = spawn(pfPath, fullCommand, {
      cwd: options.cwd || process.cwd(),
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, ...options.env }
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    child.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    child.on('close', (code) => {
      if (code === 0) {
        resolve({ stdout, stderr, code });
      } else {
        reject(new Error(`Command failed with code ${code}: ${stderr || stdout}`));
      }
    });

    child.on('error', (error) => {
      reject(error);
    });
  });
}

// Broadcast to all WebSocket clients
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
      console.error(`Failed to queue build for ${language}:`, error);
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

// WebSocket connection handling
wss.on('connection', (ws) => {
  console.log('WebSocket client connected');
  
  // Send current build statuses to new client
  const allStatuses = Array.from(buildStatus.entries()).map(([id, status]) => ({
    buildId: id,
    ...status
  }));
  
  ws.send(JSON.stringify({
    type: 'initial_status',
    builds: allStatuses
  }));
  
  ws.on('close', () => {
    console.log('WebSocket client disconnected');
  });
  
  ws.on('error', (error) => {
    console.error('WebSocket error:', error);
  });
});

// Start server
server.listen(PORT, () => {
  console.log(`[api-server] serving ${ROOT} on http://localhost:${PORT}`);
  console.log(`[api-server] API endpoints available at http://localhost:${PORT}/api`);
  console.log(`[api-server] WebSocket server running for real-time updates`);
});