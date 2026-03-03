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
import sys
import subprocess
import shlex
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
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

# Reserved paths that should not be treated as task aliases
RESERVED_PATHS = frozenset(
    ["docs", "redoc", "openapi.json", "favicon.ico", "pf", "reload", "health"]
)


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
    include_builtins: bool = Query(True, description="Include built-in tasks")
):
    """List all available pf tasks."""
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
async def get_task(task_name: str):
    """Get details about a specific task."""
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
    """Execute a pf task."""
    resolved_name = _resolve_task_name(task_name)

    if resolved_name is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found")

    # Build pf command
    cmd = ["python3", "-m", "pf_parser", resolved_name]

    # Add parameters
    for key, value in request.params.items():
        cmd.append(f"{key}={shlex.quote(value)}")

    # Add sudo if requested
    if request.sudo:
        cmd.insert(0, "sudo")
        if request.sudo_user:
            cmd.insert(1, "-u")
            cmd.insert(2, request.sudo_user)

    # Execute the task
    try:
        # Get the pf-runner directory for execution context
        pf_runner_dir = os.path.dirname(os.path.abspath(__file__))

        # Use pf_parser.py directly for task execution
        result = subprocess.run(
            ["python3", os.path.join(pf_runner_dir, "pf_parser.py"), resolved_name]
            + [f"{k}={v}" for k, v in request.params.items()],
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
async def get_task_by_alias(alias: str):
    """Get task details via its alias."""
    # Skip reserved paths that shouldn't be treated as aliases
    if alias in RESERVED_PATHS:
        raise HTTPException(status_code=404, detail="Not found")

    resolved_name = _resolve_task_name(alias)

    if resolved_name is None:
        raise HTTPException(status_code=404, detail=f"Alias '{alias}' not found")

    # Redirect to the canonical task endpoint
    return await get_task(resolved_name)


@app.post("/{alias}", tags=["Aliases"])
async def execute_task_by_alias(alias: str, request: TaskExecuteRequest):
    """Execute a task via its alias."""
    # Skip reserved paths that shouldn't be treated as aliases
    if alias in RESERVED_PATHS:
        raise HTTPException(status_code=404, detail="Not found")

    resolved_name = _resolve_task_name(alias)

    if resolved_name is None:
        raise HTTPException(status_code=404, detail=f"Alias '{alias}' not found")

    return await execute_task(resolved_name, request)


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
