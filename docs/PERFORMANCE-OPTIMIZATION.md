# Performance Optimization Guide

This guide provides strategies and best practices for optimizing the performance of pf-web-poly-compile-helper-runner.

## Table of Contents

1. [API Server Performance](#api-server-performance)
2. [Build System Optimization](#build-system-optimization)
3. [Memory Management](#memory-management)
4. [WebSocket Optimization](#websocket-optimization)
5. [Static File Serving](#static-file-serving)
6. [Monitoring and Profiling](#monitoring-and-profiling)

## API Server Performance

### Concurrency and Parallelism

The API server can handle multiple concurrent builds. Configure based on your system:

```bash
# Set number of worker processes (if using cluster mode)
export PF_API_WORKERS=4
```

**Recommendation**:
- Development: 1-2 workers
- Production: Number of CPU cores

### Request Processing

**Current Optimizations**:
1. **Asynchronous Build Execution**: Builds run in the background using `setImmediate`
2. **Non-blocking I/O**: All file operations are asynchronous
3. **Stream Processing**: Large responses use streaming

### Database Alternatives

Current in-memory storage is fast but limited. For production at scale, consider:

- **Redis**: For build status and caching
- **PostgreSQL**: For persistent build history
- **MongoDB**: For log storage

## Build System Optimization

### Parallel Builds

Enable parallel compilation where supported:

```bash
# For make-based builds
pf autobuild jobs=8

# For cargo builds
pf web-build-rust jobs=8
```

### Caching Strategies

**Compiler Caches**:
- **Rust**: `sccache` for distributed compilation
- **C/C++**: `ccache` for compilation caching
- **Node.js**: npm/yarn cache

**Example Setup**:
```bash
# Install sccache
cargo install sccache

# Configure
export RUSTC_WRAPPER=sccache
export SCCACHE_DIR=/var/cache/sccache
```

### Build Artifact Management

**Current Implementation**:
```javascript
const MAX_BUILDS = 100;
const MAX_LOGS_PER_BUILD = 1000;
```

**Tuning Parameters**:
- Increase `MAX_BUILDS` for systems with more RAM
- Decrease for memory-constrained environments
- Monitor memory usage and adjust accordingly

## Memory Management

### Build Status Cleanup

Automatic cleanup prevents memory leaks:

```javascript
function cleanupOldBuilds() {
  if (buildStatus.size > MAX_BUILDS) {
    // Remove oldest entries
    // ...
  }
}
```

**Best Practices**:
1. Call cleanup regularly (currently on each new build)
2. Monitor Map sizes
3. Set appropriate MAX_BUILDS based on available RAM

### Buffer Size Limits

**Current Limits**:
```javascript
const MAX_BUFFER = 1024 * 1024; // 1MB per stream
const MAX_LOG_SIZE = 10000; // 10KB per log entry
```

**Tuning**:
- Increase for detailed logging needs
- Decrease for memory-constrained systems
- Monitor actual log sizes

### Memory Leak Prevention

**Implemented Safeguards**:
1. **Timeout Handling**: Prevents orphaned processes
2. **Stream Limits**: Prevents unbounded buffer growth
3. **Log Rotation**: Limits log entry count
4. **Old Build Cleanup**: Removes stale data

**Monitoring**:
```bash
# Check Node.js memory usage
node --expose-gc tools/api-server.mjs

# In code, monitor heap
const used = process.memoryUsage();
console.log(`Heap: ${used.heapUsed / 1024 / 1024} MB`);
```

## WebSocket Optimization

### Connection Management

**Best Practices**:
1. Limit concurrent connections
2. Implement connection pooling
3. Close idle connections

**Example**:
```javascript
const MAX_WS_CONNECTIONS = 100;

wss.on('connection', (ws, req) => {
  if (wss.clients.size > MAX_WS_CONNECTIONS) {
    ws.close(1008, 'Too many connections');
    return;
  }
  // ...
});
```

### Message Batching

For high-frequency updates, batch messages:

```javascript
let updateQueue = [];
let batchTimer = null;

function queueUpdate(update) {
  updateQueue.push(update);
  
  if (!batchTimer) {
    batchTimer = setTimeout(() => {
      broadcast({ type: 'batch', updates: updateQueue });
      updateQueue = [];
      batchTimer = null;
    }, 100); // 100ms batch window
  }
}
```

### Compression

Enable WebSocket compression:

```javascript
const wss = new WebSocketServer({ 
  server,
  perMessageDeflate: {
    zlibDeflateOptions: {
      chunkSize: 1024,
      memLevel: 7,
      level: 3
    },
    zlibInflateOptions: {
      chunkSize: 10 * 1024
    },
    threshold: 1024 // Compress messages > 1KB
  }
});
```

## Static File Serving

### Caching Headers

Add caching for static assets:

```javascript
app.use(express.static(ROOT, {
  maxAge: '1d', // Cache for 1 day
  etag: true,
  lastModified: true,
  setHeaders: (res, filePath) => {
    // Longer cache for immutable assets
    if (filePath.includes('.wasm') || filePath.includes('.js')) {
      res.setHeader('Cache-Control', 'public, max-age=31536000, immutable');
    }
  }
}));
```

### Compression

Enable gzip/brotli compression:

```bash
npm install compression
```

```javascript
import compression from 'compression';

app.use(compression({
  level: 6, // Compression level
  threshold: 1024, // Only compress > 1KB
  filter: (req, res) => {
    // Don't compress already compressed formats
    if (req.headers['content-type'] === 'application/wasm') {
      return false;
    }
    return compression.filter(req, res);
  }
}));
```

### CDN Integration

For production, serve static assets via CDN:
- CloudFlare
- AWS CloudFront
- Fastly

## Monitoring and Profiling

### Performance Metrics

Track key metrics:

```javascript
const metrics = {
  requestCount: 0,
  requestDuration: [],
  buildCount: 0,
  buildDuration: [],
  memoryUsage: []
};

// Middleware to track requests
app.use((req, res, next) => {
  const start = Date.now();
  metrics.requestCount++;
  
  res.on('finish', () => {
    metrics.requestDuration.push(Date.now() - start);
  });
  
  next();
});

// Expose metrics endpoint
app.get('/api/metrics', (req, res) => {
  const avgRequestTime = metrics.requestDuration.reduce((a, b) => a + b, 0) / metrics.requestDuration.length;
  
  res.json({
    requestCount: metrics.requestCount,
    avgRequestTime: avgRequestTime.toFixed(2),
    buildCount: metrics.buildCount,
    activeBuilds: buildStatus.size,
    memoryUsage: process.memoryUsage()
  });
});
```

### CPU Profiling

Use Node.js built-in profiler:

```bash
# Start with profiling
node --prof tools/api-server.mjs

# Generate report
node --prof-process isolate-*.log > profile.txt
```

### Memory Profiling

Use heap snapshots:

```bash
# Install heapdump
npm install heapdump

# In code
import heapdump from 'heapdump';

// Take snapshot
heapdump.writeSnapshot('/tmp/heap-' + Date.now() + '.heapsnapshot');
```

Analyze with Chrome DevTools:
1. Open Chrome DevTools
2. Go to Memory tab
3. Load heap snapshot
4. Analyze allocations

### APM Tools

Consider using Application Performance Monitoring:

- **New Relic**: Comprehensive APM
- **DataDog**: Infrastructure and APM
- **Prometheus + Grafana**: Self-hosted metrics
- **Elastic APM**: Open-source alternative

### Load Testing

Test performance under load:

```bash
# Install artillery
npm install -g artillery

# Create load test scenario
cat > load-test.yml <<EOF
config:
  target: 'http://localhost:8080'
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - name: "API Health Check"
    flow:
      - get:
          url: "/api/health"
  - name: "Build Request"
    flow:
      - post:
          url: "/api/build/rust"
          json:
            target: "wasm"
EOF

# Run load test
artillery run load-test.yml
```

## Optimization Checklist

### Development Environment

- [ ] Use single worker process
- [ ] Enable debug logging
- [ ] Use hot reload for rapid iteration
- [ ] Profile memory usage periodically

### Production Environment

- [ ] Configure multiple workers (based on CPU cores)
- [ ] Set production log level (info or warn)
- [ ] Enable compression
- [ ] Configure caching headers
- [ ] Set up CDN for static assets
- [ ] Implement metrics collection
- [ ] Configure monitoring and alerting
- [ ] Run load tests
- [ ] Profile under realistic load
- [ ] Optimize database queries (if applicable)
- [ ] Enable HTTP/2
- [ ] Configure keep-alive connections

## Platform-Specific Optimizations

### Linux

**Kernel Parameters**:
```bash
# Increase file descriptors
ulimit -n 65535

# TCP tuning
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_max_syn_backlog=65535
```

**Process Management**:
```bash
# Use systemd for process management
# See quadlet/ directory for systemd units
```

### Docker/Containers

**Dockerfile Optimization**:
```dockerfile
# Multi-stage build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
CMD ["node", "tools/api-server.mjs"]
```

**Resource Limits**:
```yaml
# docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Advanced Optimization Techniques

### Worker Threads

For CPU-intensive tasks:

```javascript
import { Worker } from 'worker_threads';

function runBuildInWorker(language, target) {
  return new Promise((resolve, reject) => {
    const worker = new Worker('./build-worker.js', {
      workerData: { language, target }
    });
    
    worker.on('message', resolve);
    worker.on('error', reject);
    worker.on('exit', (code) => {
      if (code !== 0) {
        reject(new Error(`Worker stopped with exit code ${code}`));
      }
    });
  });
}
```

### Clustering

Scale across CPU cores:

```javascript
import cluster from 'cluster';
import os from 'os';

if (cluster.isPrimary) {
  const numCPUs = os.cpus().length;
  
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }
  
  cluster.on('exit', (worker, code, signal) => {
    console.log(`Worker ${worker.process.pid} died`);
    cluster.fork(); // Restart worker
  });
} else {
  // Worker process runs the server
  import('./api-server.mjs');
}
```

### Caching Layer

Implement Redis caching:

```javascript
import Redis from 'redis';

const redis = Redis.createClient();

async function getCachedOrBuild(language, target) {
  const cacheKey = `build:${language}:${target}`;
  
  // Try cache first
  const cached = await redis.get(cacheKey);
  if (cached) {
    return JSON.parse(cached);
  }
  
  // Build and cache
  const result = await executeBuild(language, target);
  await redis.setex(cacheKey, 3600, JSON.stringify(result));
  
  return result;
}
```

## Troubleshooting Performance Issues

### High CPU Usage

**Symptoms**: Server becomes unresponsive, slow response times

**Solutions**:
1. Profile CPU usage: `node --prof`
2. Check for infinite loops or recursive calls
3. Optimize hot code paths
4. Consider caching expensive computations

### High Memory Usage

**Symptoms**: Process crashes with OOM, slow garbage collection

**Solutions**:
1. Take heap snapshots
2. Look for memory leaks (event listener leaks, unclosed connections)
3. Reduce buffer sizes
4. Implement stricter cleanup policies

### Slow Response Times

**Symptoms**: API requests take too long

**Solutions**:
1. Add timing logs to identify bottlenecks
2. Check database query performance
3. Implement caching
4. Optimize synchronous operations
5. Use connection pooling

### WebSocket Disconnections

**Symptoms**: Clients frequently disconnect

**Solutions**:
1. Implement heartbeat/ping-pong
2. Handle reconnection gracefully
3. Increase timeout values
4. Check network stability

## Additional Resources

- [Node.js Performance Best Practices](https://nodejs.org/en/docs/guides/simple-profiling/)
- [Express Performance Best Practices](https://expressjs.com/en/advanced/best-practice-performance.html)
- [Web.dev Performance Guide](https://web.dev/performance/)
- [V8 Performance Tuning](https://v8.dev/docs/turbofan)

---

**Last Updated**: 2025-12-07
**Maintained By**: pf-web-poly-compile-helper-runner Contributors
