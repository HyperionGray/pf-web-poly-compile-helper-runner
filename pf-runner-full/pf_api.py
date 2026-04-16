#!/usr/bin/env python3
"""
pf_api.py - FastAPI REST API for pf task runner

This module provides a REST API for executing pf tasks remotely.
Tasks can be accessed via:
  - /pf/{task_name} - Access task by full name
  - /{alias} - Access task by its short alias

The API is designed to be managed via systemd and controlled with:
  - pf rest-on  - Start the REST API service
  - pf rest-off - Stop the REST API service

Features:
  - Auto-generated API docs at /docs (Swagger UI) and /redoc (ReDoc)
  - Task listing and details
  - Task execution with parameters
  - Health check endpoint
"""

import os
import re
import sys
import subprocess
import shlex
import time
import collections
import threading
import re
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Request
    from fastapi.responses import JSONResponse, StreamingResponse
    from pydantic import BaseModel, Field
except ImportError:
    print(
        "Error: FastAPI not installed. Install with: pip install 'pf-runner[api]'",
        file=sys.stderr,
    )
    sys.exit(1)

# Import pf parser functions
from pf_parser import (
    _find_pfyfile,
    _load_pfy_source_with_includes,
    parse_pfyfile_text,
    get_alias_map,
    list_dsl_tasks_with_desc,
    BUILTINS,
)


# Configuration
API_VERSION = "1.0.0"
DEFAULT_HOST = os.environ.get("PF_API_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("PF_API_PORT", "8000"))
DEFAULT_WORKERS = int(os.environ.get("PF_API_WORKERS", "4"))

# Rate limiting configuration (requests per window)
RATE_LIMIT_REQUESTS = int(os.environ.get("PF_API_RATE_LIMIT", "60"))
RATE_LIMIT_WINDOW = int(os.environ.get("PF_API_RATE_WINDOW", "60"))  # seconds
RATE_LIMIT_EXEC_REQUESTS = int(os.environ.get("PF_API_EXEC_RATE_LIMIT", "10"))

# Reserved paths that should not be treated as task aliases
RESERVED_PATHS = frozenset(
    ["docs", "redoc", "openapi.json", "favicon.ico", "pf", "reload", "health"]
)

# Regex for valid task names and parameter keys (alphanumeric, hyphens, underscores, dots)
_VALID_TASK_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_VALID_PARAM_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")


def _validate_task_name(name: str) -> str:
    """Validate and return a sanitized task name, or raise HTTPException."""
    if not _VALID_TASK_NAME_RE.match(name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task name: must match [A-Za-z0-9._-] and be 1-128 chars",
        )
    return name


def _validate_params(params: Dict[str, str]) -> Dict[str, str]:
    """Validate parameter keys and sanitize values for subprocess use."""
    validated: Dict[str, str] = {}
    for key, value in params.items():
        if not _VALID_PARAM_KEY_RE.match(key):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid parameter key '{key}': must be a valid identifier",
            )
        # Sanitize value for safe shell use
        validated[key] = shlex.quote(str(value))
    return validated


class _SlidingWindowRateLimiter:
    """Thread-safe sliding window rate limiter keyed by client IP."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self._max = max_requests
        self._window = window_seconds
        self._buckets: Dict[str, collections.deque] = {}
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        """Return True if the request is within the rate limit."""
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            bucket = self._buckets.setdefault(key, collections.deque())
            # Drop timestamps outside the sliding window
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self._max:
                return False
            bucket.append(now)
            return True


# Global rate limiter instances
_global_limiter = _SlidingWindowRateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW)
_exec_limiter = _SlidingWindowRateLimiter(RATE_LIMIT_EXEC_REQUESTS, RATE_LIMIT_WINDOW)


def _get_client_ip(request: Request) -> str:
    """Extract the real client IP, respecting X-Forwarded-For if present."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


# Pydantic models for request/response
class TaskInfo(BaseModel):
    """Information about a pf task."""

    name: str = Field(..., description="Full task name")
    description: Optional[str] = Field(None, description="Task description")
    aliases: List[str] = Field(
        default_factory=list, description="Short aliases for this task"
    )
    source_file: Optional[str] = Field(
        None, description="Source file where task is defined"
    )
    parameters: Dict[str, str] = Field(
        default_factory=dict, description="Default parameter values"
    )


class TaskListResponse(BaseModel):
    """Response containing list of available tasks."""

    tasks: List[TaskInfo]
    builtins: List[str]
    total_count: int


class TaskExecuteRequest(BaseModel):
    """Request to execute a task."""

    params: Dict[str, str] = Field(
        default_factory=dict, description="Task parameters (key=value)"
    )
    sudo: bool = Field(False, description="Run with sudo")
    sudo_user: Optional[str] = Field(None, description="Run as this user with sudo")
    hosts: List[str] = Field(
        default_factory=lambda: ["@local"], description="Target hosts"
    )


class TaskExecuteResponse(BaseModel):
    """Response from task execution."""

    task: str
    status: str
    exit_code: int
    stdout: str
    stderr: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    tasks_loaded: int


# In-memory task cache
_task_cache: Optional[Dict[str, Any]] = None
_alias_cache: Optional[Dict[str, str]] = None


def _load_tasks() -> tuple:
    """Load and cache tasks from Pfyfile."""
    global _task_cache, _alias_cache

    if _task_cache is None:
        try:
            dsl_src, task_sources = _load_pfy_source_with_includes()
            _task_cache = parse_pfyfile_text(dsl_src, task_sources)

            # Build alias map
            _alias_cache = {}
            for task_name, task in _task_cache.items():
                for alias in task.aliases:
                    _alias_cache[alias] = task_name
        except Exception as e:
            _task_cache = {}
            _alias_cache = {}

    return _task_cache, _alias_cache


def _resolve_task_name(name: str) -> Optional[str]:
    """Resolve a task name or alias to the canonical task name."""
    tasks, aliases = _load_tasks()

    # Check if it's a direct task name
    if name in tasks:
        return name

    # Check if it's a builtin
    if name in BUILTINS:
        return name

    # Check if it's an alias
    if name in aliases:
        return aliases[name]

    return None


_PARAM_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


def _build_safe_pf_args(params: Dict[str, Any]) -> List[str]:
    """
    Validate and convert task parameters into a list of 'key=value' arguments
    safe to pass to pf_parser via subprocess.

    Raises HTTPException(400) if any parameter name or value is invalid.
    """
    safe_args: List[str] = []

    # Import HTTPException lazily to avoid issues when FastAPI is unavailable.
    try:
        from fastapi import HTTPException  # type: ignore
    except Exception:
        HTTPException = RuntimeError  # type: ignore

    for raw_key, raw_value in (params or {}).items():
        key = str(raw_key)

        # Disallow keys that do not match our strict pattern
        if not _PARAM_NAME_PATTERN.match(key):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid parameter name: {key!r}",
            )

        # Convert value to string; limit size to avoid abuse
        value = "" if raw_value is None else str(raw_value)
        if len(value) > 4096:
            raise HTTPException(
                status_code=400,
                detail=f"Parameter value for {key!r} is too long",
            )

        safe_args.append(f"{key}={value}")

    return safe_args


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup: load tasks
    _load_tasks()
    yield
    # Shutdown: cleanup if needed
    pass


# Create FastAPI app
app = FastAPI(
    title="pf REST API",
    description="""
REST API for the pf task runner.

## Features

- **Task Listing**: View all available tasks with descriptions and aliases
- **Task Execution**: Run tasks with parameters via HTTP
- **Alias Support**: Access tasks via short aliases defined in Pfyfile
- **Auto-generated Docs**: Interactive API documentation

## Endpoint Patterns

- `/pf/{task}` - Access any task by its full name
- `/{alias}` - Access tasks by their short alias (if defined)

## Example Usage

```bash
# List all tasks
curl http://localhost:8000/pf/

# Get task details
curl http://localhost:8000/pf/my-task

# Execute a task
curl -X POST http://localhost:8000/pf/my-task \\
  -H "Content-Type: application/json" \\
  -d '{"params": {"key": "value"}}'

# Execute via alias
curl -X POST http://localhost:8000/cmd \\
  -H "Content-Type: application/json" \\
  -d '{}'
```
    """,
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.get("/", response_model=HealthResponse, tags=["Health"])
async def root():
    """Root endpoint - returns API health and info."""
    tasks, _ = _load_tasks()
    return HealthResponse(
        status="ok", version=API_VERSION, tasks_loaded=len(tasks) + len(BUILTINS)
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    tasks, _ = _load_tasks()
    return HealthResponse(
        status="ok", version=API_VERSION, tasks_loaded=len(tasks) + len(BUILTINS)
    )


@app.get("/pf/", response_model=TaskListResponse, tags=["Tasks"])
async def list_tasks(
    request: Request,
    include_builtins: bool = Query(True, description="Include built-in tasks"),
):
    """List all available pf tasks."""
    client_ip = _get_client_ip(request)
    if not _global_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please slow down.",
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
        )

    tasks, _ = _load_tasks()

    task_list = []
    for task_name, task in tasks.items():
        task_list.append(
            TaskInfo(
                name=task_name,
                description=task.description,
                aliases=task.aliases,
                source_file=task.source_file,
                parameters=task.params,
            )
        )

    builtins = list(BUILTINS.keys()) if include_builtins else []

    return TaskListResponse(
        tasks=task_list, builtins=builtins, total_count=len(task_list) + len(builtins)
    )


@app.get("/pf/{task_name}", response_model=TaskInfo, tags=["Tasks"])
async def get_task(task_name: str, request: Request):
    """Get details about a specific task."""
    _validate_task_name(task_name)
    resolved_name = _resolve_task_name(task_name)

    if resolved_name is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found")

    # Check builtins first
    if resolved_name in BUILTINS:
        return TaskInfo(
            name=resolved_name,
            description="Built-in task",
            aliases=[],
            source_file=None,
            parameters={},
        )

    tasks, _ = _load_tasks()
    if resolved_name in tasks:
        task = tasks[resolved_name]
        return TaskInfo(
            name=resolved_name,
            description=task.description,
            aliases=task.aliases,
            source_file=task.source_file,
            parameters=task.params,
        )

    raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found")


@app.post("/pf/{task_name}", response_model=TaskExecuteResponse, tags=["Tasks"])
async def execute_task(task_name: str, request: TaskExecuteRequest):
    """Execute a pf task.

    Security: task names are validated against an allowlist regex and all
    parameter values are shell-quoted before being passed to subprocess.
    The command is executed with ``shell=False`` so no shell interpretation
    occurs on the argument vector.
    """
    _validate_task_name(task_name)
    resolved_name = _resolve_task_name(task_name)

    if resolved_name is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found")

    # Validate and sanitize parameters
    safe_params = _validate_params(request.params)

    # Execute the task
    try:
        pf_runner_dir = os.path.dirname(os.path.abspath(__file__))

        # Build command as a list (shell=False) with sanitized params.
        cmd: List[str] = [
            sys.executable,
            os.path.join(pf_runner_dir, "pf_main.py"),
            "run",
            resolved_name,
        ]
        for key, value in safe_params.items():
            cmd.append(f"{key}={value}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=pf_runner_dir,
        )

        return TaskExecuteResponse(
            task=resolved_name,
            status="completed" if result.returncode == 0 else "failed",
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Task execution timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task execution failed: {str(e)}")


@app.post("/reload", tags=["Admin"])
async def reload_tasks():
    """Reload tasks from Pfyfile (clears cache)."""
    global _task_cache, _alias_cache
    _task_cache = None
    _alias_cache = None
    _load_tasks()

    tasks, aliases = _load_tasks()
    return {
        "status": "reloaded",
        "tasks_count": len(tasks),
        "aliases_count": len(aliases),
        "builtins_count": len(BUILTINS),
    }


# Dynamic alias routes - these allow accessing tasks via their aliases
@app.get("/{alias}", tags=["Aliases"])
async def get_task_by_alias(alias: str, request: Request):
    """Get task details via its alias."""
    # Skip reserved paths that shouldn't be treated as aliases
    if alias in RESERVED_PATHS:
        raise HTTPException(status_code=404, detail="Not found")

    resolved_name = _resolve_task_name(alias)

    if resolved_name is None:
        raise HTTPException(status_code=404, detail=f"Alias '{alias}' not found")

    # Redirect to the canonical task endpoint
    return await get_task(resolved_name, request)


@app.post("/{alias}", tags=["Aliases"])
async def execute_task_by_alias(alias: str, request: TaskExecuteRequest, http_request: Request):
    """Execute a task via its alias."""
    # Skip reserved paths that shouldn't be treated as aliases
    if alias in RESERVED_PATHS:
        raise HTTPException(status_code=404, detail="Not found")

    resolved_name = _resolve_task_name(alias)

    if resolved_name is None:
        raise HTTPException(status_code=404, detail=f"Alias '{alias}' not found")

    return await execute_task(resolved_name, request, http_request)


def run_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    workers: int = DEFAULT_WORKERS,
    reload: bool = False,
):
    """Run the API server using uvicorn."""
    try:
        import uvicorn
    except ImportError:
        print(
            "Error: uvicorn not installed. Install with: pip install 'pf-runner[api]'",
            file=sys.stderr,
        )
        sys.exit(1)

    uvicorn.run(
        "pf_api:app",
        host=host,
        port=port,
        workers=workers if not reload else 1,  # reload only works with 1 worker
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="pf REST API Server")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind to")
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="Port to bind to"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help="Number of worker processes",
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload (development mode)"
    )

    args = parser.parse_args()

    print(f"Starting pf REST API server on http://{args.host}:{args.port}")
    print(f"API docs available at http://{args.host}:{args.port}/docs")
    print(f"ReDoc available at http://{args.host}:{args.port}/redoc")

    run_server(host=args.host, port=args.port, workers=args.workers, reload=args.reload)
