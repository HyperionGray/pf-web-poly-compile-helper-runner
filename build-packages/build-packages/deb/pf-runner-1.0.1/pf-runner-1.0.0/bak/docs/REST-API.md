# REST API Documentation

The pf-web-poly-compile-helper-runner now includes a comprehensive REST API for managing WebAssembly builds, project information, and real-time build status updates.

## Overview

The REST API server replaces the basic static file server while maintaining backward compatibility. It provides:

- **Build Management**: Trigger builds for different languages (Rust, C, Fortran, WAT)
- **Status Tracking**: Real-time build status and progress monitoring
- **Project Management**: List projects, modules, and build artifacts
- **WebSocket Support**: Real-time updates via WebSocket connections
- **Static File Serving**: Backward compatibility with existing web demo

## Getting Started

### Starting the API Server

```bash
# Start with default settings (port 8080, serves web demo)
pf web-dev

# Or start API server directly
pf api-server

# Custom port and directory
pf web-dev port=3000 dir=custom/path

# Using npm script
npm run api-server
```

### Base URL

All API endpoints are available under `/api`:
```
http://localhost:8080/api
```

## API Endpoints

### Health and System Information

#### GET /api/health
Check API server health status.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "server": "pf-api-server",
  "version": "1.0.0"
}
```

#### GET /api/system
Get system information and capabilities.

**Response:**
```json
{
  "platform": "linux",
  "arch": "x64",
  "nodeVersion": "v18.17.0",
  "cwd": "/workspace",
  "rootDir": "/workspace/demos/pf-web-polyglot-demo-plus-c/web",
  "availableLanguages": ["rust", "c", "fortran", "wat"],
  "buildTargets": ["wasm", "llvm", "asm"]
}
```

### Project Management

#### GET /api/projects
List available projects and their supported languages.

**Response:**
```json
{
  "projects": [
    {
      "name": "pf-web-polyglot-demo-plus-c",
      "path": "/workspace/demos/pf-web-polyglot-demo-plus-c",
      "languages": ["rust", "c", "fortran", "asm"]
    }
  ]
}
```

#### GET /api/modules
List available WebAssembly modules and build artifacts.

**Response:**
```json
{
  "modules": [
    {
      "language": "rust",
      "files": [
        {
          "name": "rust_demo.wasm",
          "path": "/wasm/rust/rust_demo.wasm",
          "size": 12345,
          "modified": "2024-01-01T12:00:00.000Z"
        }
      ]
    }
  ]
}
```

### Build Management

#### POST /api/build/:language
Trigger a build for a specific language.

**Parameters:**
- `language` (path): Language to build (`rust`, `c`, `fortran`, `wat`)

**Request Body:**
```json
{
  "target": "wasm",           // Build target: "wasm", "llvm", "asm"
  "project": "pf-web-polyglot-demo-plus-c",  // Project name
  "opt_level": "3",           // Optimization level (for LLVM builds)
  "parallel": true            // Enable OpenMP (for supported builds)
}
```

**Response:**
```json
{
  "buildId": "rust-wasm-1704110400000",
  "status": "queued",
  "message": "Build queued successfully"
}
```

**Examples:**
```bash
# Build Rust to WebAssembly
curl -X POST http://localhost:8080/api/build/rust \
  -H "Content-Type: application/json" \
  -d '{"target": "wasm"}'

# Build C to LLVM IR with optimization
curl -X POST http://localhost:8080/api/build/c \
  -H "Content-Type: application/json" \
  -d '{"target": "llvm", "opt_level": "2", "parallel": true}'

# Build Fortran to WebAssembly
curl -X POST http://localhost:8080/api/build/fortran \
  -H "Content-Type: application/json" \
  -d '{"target": "wasm"}'
```

#### POST /api/build/all
Trigger builds for all supported languages.

**Request Body:**
```json
{
  "target": "wasm",           // Build target for all languages
  "project": "pf-web-polyglot-demo-plus-c",
  "opt_level": "3"            // Additional options
}
```

**Response:**
```json
{
  "message": "All builds queued successfully",
  "buildIds": [
    "rust-wasm-1704110400000",
    "c-wasm-1704110400001",
    "fortran-wasm-1704110400002",
    "wat-wasm-1704110400003"
  ],
  "target": "wasm",
  "project": "pf-web-polyglot-demo-plus-c"
}
```

### Build Status and Logs

#### GET /api/status
Get build status for all builds or a specific build.

**Query Parameters:**
- `buildId` (optional): Specific build ID to query

**Response (all builds):**
```json
{
  "builds": [
    {
      "buildId": "rust-wasm-1704110400000",
      "language": "rust",
      "target": "wasm",
      "project": "pf-web-polyglot-demo-plus-c",
      "status": "completed",
      "startTime": "2024-01-01T12:00:00.000Z",
      "endTime": "2024-01-01T12:01:30.000Z",
      "duration": 90000,
      "progress": 100
    }
  ]
}
```

**Response (specific build):**
```json
{
  "buildId": "rust-wasm-1704110400000",
  "language": "rust",
  "target": "wasm",
  "project": "pf-web-polyglot-demo-plus-c",
  "status": "running",
  "startTime": "2024-01-01T12:00:00.000Z",
  "progress": 45
}
```

**Build Status Values:**
- `queued`: Build is queued for execution
- `running`: Build is currently executing
- `completed`: Build completed successfully
- `failed`: Build failed with errors

#### GET /api/logs/:buildId
Get detailed logs for a specific build.

**Response:**
```json
{
  "buildId": "rust-wasm-1704110400000",
  "logs": [
    {
      "timestamp": "2024-01-01T12:00:00.000Z",
      "level": "info",
      "message": "Build started",
      "stdout": "Building Rust project...",
      "stderr": ""
    },
    {
      "timestamp": "2024-01-01T12:01:30.000Z",
      "level": "info",
      "message": "Build completed successfully",
      "stdout": "Build finished successfully",
      "stderr": ""
    }
  ]
}
```

## WebSocket API

The API server provides real-time updates via WebSocket connections.

### Connection

Connect to: `ws://localhost:8080`

### Message Types

#### initial_status
Sent when a client first connects, containing current build statuses.

```json
{
  "type": "initial_status",
  "builds": [
    {
      "buildId": "rust-wasm-1704110400000",
      "status": "running",
      "progress": 45
    }
  ]
}
```

#### build_started
Sent when a new build is started.

```json
{
  "type": "build_started",
  "buildId": "rust-wasm-1704110400000",
  "language": "rust",
  "target": "wasm",
  "project": "pf-web-polyglot-demo-plus-c"
}
```

#### build_progress
Sent during build execution to report progress.

```json
{
  "type": "build_progress",
  "buildId": "rust-wasm-1704110400000",
  "status": "running",
  "progress": 75
}
```

#### build_completed
Sent when a build completes successfully.

```json
{
  "type": "build_completed",
  "buildId": "rust-wasm-1704110400000",
  "status": "completed",
  "progress": 100
}
```

#### build_failed
Sent when a build fails.

```json
{
  "type": "build_failed",
  "buildId": "rust-wasm-1704110400000",
  "status": "failed",
  "error": "Compilation error: ..."
}
```

## Client Libraries

### JavaScript/Node.js Example

```javascript
import PfApiClient from './tools/api-client-example.mjs';

const client = new PfApiClient('http://localhost:8080/api');

// Connect to WebSocket for real-time updates
await client.connectWebSocket();

// Trigger a build
const build = await client.buildLanguage('rust', { target: 'wasm' });
console.log('Build started:', build.buildId);

// Wait for completion
const result = await client.waitForBuild(build.buildId);
if (result.success) {
  console.log('Build completed successfully!');
} else {
  console.log('Build failed:', result.status.error);
}
```

### cURL Examples

```bash
# Health check
curl http://localhost:8080/api/health

# Get system info
curl http://localhost:8080/api/system

# List projects
curl http://localhost:8080/api/projects

# Trigger Rust build
curl -X POST http://localhost:8080/api/build/rust \
  -H "Content-Type: application/json" \
  -d '{"target": "wasm"}'

# Check build status
curl http://localhost:8080/api/status?buildId=rust-wasm-1704110400000

# Get build logs
curl http://localhost:8080/api/logs/rust-wasm-1704110400000
```

## Error Handling

The API uses standard HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include details:

```json
{
  "error": "Unsupported language: python. Supported: rust, c, fortran, wat"
}
```

## Integration with pf Tasks

The API server integrates with existing pf tasks:

- `web-build-rust` → `/api/build/rust`
- `web-build-c` → `/api/build/c`
- `web-build-fortran` → `/api/build/fortran`
- `web-build-wat` → `/api/build/wat`

All build options supported by pf tasks are available via the API:

```json
{
  "target": "llvm",
  "opt_level": "3",
  "parallel": true,
  "passes": "mem2reg,instcombine"
}
```

## Backward Compatibility

The API server maintains full backward compatibility:

- Static files are served from the same paths
- CORS headers are preserved for WebAssembly
- The web demo works without modifications
- Original pf tasks continue to function

## Performance Considerations

- Build operations are asynchronous and non-blocking
- WebSocket connections are lightweight
- Static file serving uses Express.js optimizations
- Build status is stored in memory (consider persistence for production)

## Security Notes

- The API currently has no authentication (suitable for development)
- CORS is configured to allow all origins
- File system access is limited to the configured root directory
- Build commands are executed with the same privileges as the server

For production use, consider adding:
- Authentication and authorization
- Rate limiting
- Input validation and sanitization
- Secure WebSocket connections (WSS)
- Process isolation for builds