#!/usr/bin/env python3
"""
pf_containerize.py - Automatic containerization module for pf-runner

This module provides:
- Project detection using heuristics (language, build system, dependencies)
- Automatic Dockerfile generation that "just works"
- Retry mechanisms with error pattern matching
- Quadlet file generation for systemd integration
- Support for user hints (--install-hint-deps, --main-bin-hint, etc.)

File Structure (1225 lines, organized by class):
  - Enums and Data Classes (lines 26-109):
    - ProjectLanguage: Detected languages
    - BuildSystem: Detected build systems
    - ProjectProfile: Project characteristics
    - RetryConfig: Retry behavior
    - ContainerBuildResult: Build results
  
  - Error Pattern Handlers (lines 114-191):
    - Error pattern registry and fix functions
    - Common build error handlers (apt, pip, npm, cargo, etc.)
  
  - ProjectDetector class (lines 193-608): [415 lines]
    - Language detection heuristics
    - Build system detection
    - Dependency analysis
    - Main binary detection
  
  - DockerfileGenerator class (lines 610-743): [133 lines]
    - Smart Dockerfile generation
    - Multi-stage builds
    - Base image selection
  
  - QuadletGenerator class (lines 745-834): [89 lines]
    - Systemd Quadlet file generation
    - Service configuration
  
  - ContainerBuilder class (lines 836-989): [153 lines]
    - Build execution with retry logic
    - Error pattern matching
    - Build logging
  
  - Public API functions (lines 991+):
    - containerize(): Main entry point
    - generate_dockerfile_only(): Dockerfile generation
    - generate_quadlet_files(): Quadlet generation

Design:
  - Modular class-based architecture
  - Extensible error pattern matching
  - Heuristic-based intelligent defaults
"""

import os
import re
import json
import subprocess
import shlex
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Tuple, Any, Callable
from pathlib import Path


class ProjectLanguage(Enum):
    """Detected programming languages."""
    PYTHON = "python"
    RUST = "rust"
    GO = "go"
    NODE = "node"
    C = "c"
    CPP = "cpp"
    JAVA = "java"
    FORTRAN = "fortran"
    RUBY = "ruby"
    ELIXIR = "elixir"
    PHP = "php"
    DOTNET = "dotnet"
    UNKNOWN = "unknown"


class BuildSystem(Enum):
    """Detected build systems."""
    CARGO = "cargo"
    GO_MOD = "go"
    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"
    PIP = "pip"
    POETRY = "poetry"
    PIPENV = "pipenv"
    CMAKE = "cmake"
    MAKE = "make"
    MESON = "meson"
    AUTOTOOLS = "autotools"
    MAVEN = "maven"
    GRADLE = "gradle"
    MIX = "mix"
    COMPOSER = "composer"
    BUNDLER = "bundler"
    DOTNET = "dotnet"
    UNKNOWN = "unknown"


@dataclass
class ProjectProfile:
    """Profile of detected project characteristics."""
    languages: List[ProjectLanguage] = field(default_factory=list)
    build_systems: List[BuildSystem] = field(default_factory=list)
    main_language: Optional[ProjectLanguage] = None
    main_build_system: Optional[BuildSystem] = None
    detected_files: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    apt_packages: List[str] = field(default_factory=list)
    build_commands: List[str] = field(default_factory=list)
    run_commands: List[str] = field(default_factory=list)
    main_binary: Optional[str] = None
    port: Optional[int] = None
    working_dir: str = "/app"
    base_image: str = "ubuntu:24.04"
    user_hints: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    build_timeout: int = 600  # 10 minute default, can be overridden
    retry_on_patterns: List[str] = field(default_factory=list)


@dataclass
class ContainerBuildResult:
    """Result of a container build attempt."""
    success: bool
    image_name: Optional[str] = None
    build_output: str = ""
    error_output: str = ""
    attempts: int = 1
    dockerfile_content: str = ""
    quadlet_content: str = ""
    fixes_applied: List[str] = field(default_factory=list)


# Error patterns and their fixes
ERROR_PATTERNS: List[Tuple[str, str, Callable[['ProjectProfile'], List[str]]]] = []


def register_error_pattern(pattern: str, description: str, fix_func: Callable[['ProjectProfile'], List[str]]):
    """Register an error pattern and its fix function."""
    ERROR_PATTERNS.append((pattern, description, fix_func))


# Common error patterns and fixes
def _fix_missing_apt_package(profile: ProjectProfile) -> List[str]:
    """Fix for missing apt packages."""
    return ["apt-get update && apt-get install -y build-essential"]


def _fix_missing_python_pkg(profile: ProjectProfile) -> List[str]:
    """Fix for missing Python packages."""
    return ["pip install --upgrade pip setuptools wheel"]


def _fix_missing_node_modules(profile: ProjectProfile) -> List[str]:
    """Fix for missing node_modules."""
    return ["npm install"]


def _fix_permission_denied(profile: ProjectProfile) -> List[str]:
    """Fix for permission denied errors."""
    return ["chmod -R 755 /app", "chown -R 1000:1000 /app"]


def _fix_network_timeout(profile: ProjectProfile) -> List[str]:
    """Fix for network timeout errors - usually just needs retry."""
    return []


def _fix_cargo_lock_missing(profile: ProjectProfile) -> List[str]:
    """Fix for missing Cargo.lock."""
    return ["cargo generate-lockfile"]


def _fix_go_mod_missing(profile: ProjectProfile) -> List[str]:
    """Fix for missing go.mod."""
    return ["go mod init app"]


# Register common error patterns
register_error_pattern(
    r"E: Unable to locate package",
    "Missing apt package",
    _fix_missing_apt_package
)
register_error_pattern(
    r"ModuleNotFoundError|ImportError",
    "Missing Python module",
    _fix_missing_python_pkg
)
register_error_pattern(
    r"Cannot find module|Module not found",
    "Missing Node module",
    _fix_missing_node_modules
)
register_error_pattern(
    r"Permission denied|EACCES",
    "Permission denied",
    _fix_permission_denied
)
register_error_pattern(
    r"timeout|ETIMEDOUT|ECONNRESET",
    "Network timeout",
    _fix_network_timeout
)
register_error_pattern(
    r"Cargo\.lock.*not found|no Cargo\.lock file",
    "Missing Cargo.lock",
    _fix_cargo_lock_missing
)
register_error_pattern(
    r"go\.mod.*not found|no go\.mod file",
    "Missing go.mod",
    _fix_go_mod_missing
)


class ProjectDetector:
    """Detect project characteristics using heuristics."""

    # File patterns that indicate languages/build systems
    DETECTION_RULES: Dict[str, Tuple[ProjectLanguage, Optional[BuildSystem]]] = {
        "Cargo.toml": (ProjectLanguage.RUST, BuildSystem.CARGO),
        "go.mod": (ProjectLanguage.GO, BuildSystem.GO_MOD),
        "go.sum": (ProjectLanguage.GO, BuildSystem.GO_MOD),
        "package.json": (ProjectLanguage.NODE, BuildSystem.NPM),
        "yarn.lock": (ProjectLanguage.NODE, BuildSystem.YARN),
        "pnpm-lock.yaml": (ProjectLanguage.NODE, BuildSystem.PNPM),
        "requirements.txt": (ProjectLanguage.PYTHON, BuildSystem.PIP),
        "pyproject.toml": (ProjectLanguage.PYTHON, BuildSystem.POETRY),
        "setup.py": (ProjectLanguage.PYTHON, BuildSystem.PIP),
        "Pipfile": (ProjectLanguage.PYTHON, BuildSystem.PIPENV),
        "CMakeLists.txt": (ProjectLanguage.CPP, BuildSystem.CMAKE),
        "Makefile": (ProjectLanguage.C, BuildSystem.MAKE),
        "GNUmakefile": (ProjectLanguage.C, BuildSystem.MAKE),
        "meson.build": (ProjectLanguage.C, BuildSystem.MESON),
        "configure.ac": (ProjectLanguage.C, BuildSystem.AUTOTOOLS),
        "configure": (ProjectLanguage.C, BuildSystem.AUTOTOOLS),
        "pom.xml": (ProjectLanguage.JAVA, BuildSystem.MAVEN),
        "build.gradle": (ProjectLanguage.JAVA, BuildSystem.GRADLE),
        "build.gradle.kts": (ProjectLanguage.JAVA, BuildSystem.GRADLE),
        "mix.exs": (ProjectLanguage.ELIXIR, BuildSystem.MIX),
        "Gemfile": (ProjectLanguage.RUBY, BuildSystem.BUNDLER),
        "composer.json": (ProjectLanguage.PHP, BuildSystem.COMPOSER),
        "*.csproj": (ProjectLanguage.DOTNET, BuildSystem.DOTNET),
        "*.fsproj": (ProjectLanguage.DOTNET, BuildSystem.DOTNET),
    }

    # File extensions to languages
    EXTENSION_MAP: Dict[str, ProjectLanguage] = {
        ".py": ProjectLanguage.PYTHON,
        ".rs": ProjectLanguage.RUST,
        ".go": ProjectLanguage.GO,
        ".js": ProjectLanguage.NODE,
        ".ts": ProjectLanguage.NODE,
        ".jsx": ProjectLanguage.NODE,
        ".tsx": ProjectLanguage.NODE,
        ".c": ProjectLanguage.C,
        ".h": ProjectLanguage.C,
        ".cc": ProjectLanguage.CPP,
        ".cpp": ProjectLanguage.CPP,
        ".cxx": ProjectLanguage.CPP,
        ".hpp": ProjectLanguage.CPP,
        ".java": ProjectLanguage.JAVA,
        ".f90": ProjectLanguage.FORTRAN,
        ".f95": ProjectLanguage.FORTRAN,
        ".f03": ProjectLanguage.FORTRAN,
        ".rb": ProjectLanguage.RUBY,
        ".ex": ProjectLanguage.ELIXIR,
        ".exs": ProjectLanguage.ELIXIR,
        ".php": ProjectLanguage.PHP,
        ".cs": ProjectLanguage.DOTNET,
        ".fs": ProjectLanguage.DOTNET,
    }

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()

    def detect(self) -> ProjectProfile:
        """Detect project characteristics."""
        profile = ProjectProfile()

        if not self.project_path.exists():
            profile.errors.append(f"Project path does not exist: {self.project_path}")
            return profile

        # Scan for known files
        self._scan_known_files(profile)

        # Scan file extensions
        self._scan_extensions(profile)

        # Determine main language and build system
        self._determine_main(profile)

        # Detect dependencies
        self._detect_dependencies(profile)

        # Determine apt packages needed
        self._determine_apt_packages(profile)

        # Determine build/run commands
        self._determine_commands(profile)

        # Try to detect main binary
        self._detect_main_binary(profile)

        # Detect port if applicable
        self._detect_port(profile)

        # Select base image
        self._select_base_image(profile)

        return profile

    def _scan_known_files(self, profile: ProjectProfile):
        """Scan for known indicator files."""
        for name, (lang, build_sys) in self.DETECTION_RULES.items():
            if name.startswith("*"):
                # Glob pattern
                ext = name[1:]
                for f in self.project_path.rglob(f"*{ext}"):
                    if not any(part.startswith('.') for part in f.parts):
                        profile.detected_files[str(f.relative_to(self.project_path))] = name
                        if lang not in profile.languages:
                            profile.languages.append(lang)
                        if build_sys and build_sys not in profile.build_systems:
                            profile.build_systems.append(build_sys)
                        break
            else:
                file_path = self.project_path / name
                if file_path.exists():
                    profile.detected_files[name] = name
                    if lang not in profile.languages:
                        profile.languages.append(lang)
                    if build_sys and build_sys not in profile.build_systems:
                        profile.build_systems.append(build_sys)

    def _scan_extensions(self, profile: ProjectProfile):
        """Scan file extensions to detect languages."""
        ext_counts: Dict[ProjectLanguage, int] = {}

        for f in self.project_path.rglob("*"):
            if f.is_file() and not any(part.startswith('.') for part in f.parts):
                ext = f.suffix.lower()
                if ext in self.EXTENSION_MAP:
                    lang = self.EXTENSION_MAP[ext]
                    ext_counts[lang] = ext_counts.get(lang, 0) + 1
                    if lang not in profile.languages:
                        profile.languages.append(lang)

    def _determine_main(self, profile: ProjectProfile):
        """Determine the main language and build system."""
        # Priority order for languages
        priority = [
            ProjectLanguage.RUST, ProjectLanguage.GO, ProjectLanguage.NODE,
            ProjectLanguage.PYTHON, ProjectLanguage.JAVA, ProjectLanguage.CPP,
            ProjectLanguage.C, ProjectLanguage.DOTNET
        ]

        for lang in priority:
            if lang in profile.languages:
                profile.main_language = lang
                break

        if not profile.main_language and profile.languages:
            profile.main_language = profile.languages[0]

        # Determine main build system
        if profile.build_systems:
            profile.main_build_system = profile.build_systems[0]

    def _detect_dependencies(self, profile: ProjectProfile):
        """Detect project dependencies from files."""
        # Python requirements.txt
        req_file = self.project_path / "requirements.txt"
        if req_file.exists():
            with open(req_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        dep = re.split(r'[<>=!~\[]', line)[0].strip()
                        if dep:
                            profile.dependencies.append(f"pip:{dep}")

        # Node package.json
        pkg_json = self.project_path / "package.json"
        if pkg_json.exists():
            try:
                with open(pkg_json) as f:
                    data = json.load(f)
                    for dep in data.get("dependencies", {}):
                        profile.dependencies.append(f"npm:{dep}")
                    for dep in data.get("devDependencies", {}):
                        profile.dependencies.append(f"npm-dev:{dep}")
            except json.JSONDecodeError:
                pass

        # Rust Cargo.toml
        cargo_toml = self.project_path / "Cargo.toml"
        if cargo_toml.exists():
            with open(cargo_toml) as f:
                in_deps = False
                for line in f:
                    if "[dependencies]" in line or "[dev-dependencies]" in line:
                        in_deps = True
                        continue
                    if in_deps and line.startswith("["):
                        in_deps = False
                        continue
                    if in_deps and "=" in line:
                        dep = line.split("=")[0].strip()
                        if dep:
                            profile.dependencies.append(f"cargo:{dep}")

    def _determine_apt_packages(self, profile: ProjectProfile):
        """Determine apt packages needed based on detected features."""
        apt_pkgs = set()

        # Base packages always needed
        apt_pkgs.add("ca-certificates")
        apt_pkgs.add("curl")

        # Language-specific packages
        lang_packages = {
            ProjectLanguage.PYTHON: ["python3", "python3-pip", "python3-venv"],
            ProjectLanguage.NODE: [],  # Node installed separately
            ProjectLanguage.RUST: [],  # Rust installed via rustup
            ProjectLanguage.GO: [],  # Go installed separately
            ProjectLanguage.C: ["build-essential", "clang", "cmake"],
            ProjectLanguage.CPP: ["build-essential", "clang", "cmake", "libstdc++-11-dev"],
            ProjectLanguage.JAVA: ["openjdk-17-jdk", "maven"],
            ProjectLanguage.FORTRAN: ["gfortran"],
            ProjectLanguage.RUBY: ["ruby", "ruby-dev", "bundler"],
            ProjectLanguage.PHP: ["php", "php-cli", "composer"],
            ProjectLanguage.ELIXIR: ["erlang", "elixir"],
            ProjectLanguage.DOTNET: [],  # .NET installed separately
        }

        for lang in profile.languages:
            if lang in lang_packages:
                apt_pkgs.update(lang_packages[lang])

        # Build system packages
        build_packages = {
            BuildSystem.CMAKE: ["cmake"],
            BuildSystem.MAKE: ["build-essential", "make"],
            BuildSystem.MESON: ["meson", "ninja-build"],
            BuildSystem.AUTOTOOLS: ["autoconf", "automake", "libtool"],
        }

        for build_sys in profile.build_systems:
            if build_sys in build_packages:
                apt_pkgs.update(build_packages[build_sys])

        profile.apt_packages = sorted(apt_pkgs)

    def _determine_commands(self, profile: ProjectProfile):
        """Determine build and run commands based on detected systems."""
        build_cmds = []
        run_cmds = []

        if profile.main_build_system == BuildSystem.CARGO:
            build_cmds.append("cargo build --release")
            run_cmds.append("./target/release/${PROJECT_NAME:-app}")

        elif profile.main_build_system == BuildSystem.GO_MOD:
            build_cmds.append("go build -o /app/main .")
            run_cmds.append("/app/main")

        elif profile.main_build_system in (BuildSystem.NPM, BuildSystem.YARN, BuildSystem.PNPM):
            pkg_manager = "npm"
            if profile.main_build_system == BuildSystem.YARN:
                pkg_manager = "yarn"
            elif profile.main_build_system == BuildSystem.PNPM:
                pkg_manager = "pnpm"

            build_cmds.append(f"{pkg_manager} install")
            # Check if there's a build script
            pkg_json = self.project_path / "package.json"
            if pkg_json.exists():
                try:
                    with open(pkg_json) as f:
                        data = json.load(f)
                        scripts = data.get("scripts", {})
                        if "build" in scripts:
                            build_cmds.append(f"{pkg_manager} run build")
                        if "start" in scripts:
                            run_cmds.append(f"{pkg_manager} start")
                        elif "main" in data:
                            run_cmds.append(f"node {data['main']}")
                        else:
                            run_cmds.append("node index.js")
                except json.JSONDecodeError:
                    run_cmds.append("node index.js")

        elif profile.main_build_system in (BuildSystem.PIP, BuildSystem.POETRY, BuildSystem.PIPENV):
            if profile.main_build_system == BuildSystem.POETRY:
                build_cmds.append("pip install poetry && poetry install")
            elif profile.main_build_system == BuildSystem.PIPENV:
                build_cmds.append("pip install pipenv && pipenv install")
            else:
                req_file = self.project_path / "requirements.txt"
                if req_file.exists():
                    build_cmds.append("pip install -r requirements.txt")
                else:
                    build_cmds.append("pip install -e .")
            # Try to find main entry point
            if (self.project_path / "main.py").exists():
                run_cmds.append("python main.py")
            elif (self.project_path / "app.py").exists():
                run_cmds.append("python app.py")
            elif (self.project_path / "run.py").exists():
                run_cmds.append("python run.py")
            else:
                run_cmds.append("python -m app")

        elif profile.main_build_system == BuildSystem.CMAKE:
            build_cmds.extend([
                "cmake -B build -DCMAKE_BUILD_TYPE=Release",
                "cmake --build build -j$(nproc)"
            ])
            run_cmds.append("./build/main")

        elif profile.main_build_system == BuildSystem.MAKE:
            build_cmds.append("make")
            run_cmds.append("./main")

        elif profile.main_build_system == BuildSystem.MAVEN:
            build_cmds.append("mvn package -DskipTests")
            run_cmds.append("java -jar target/*.jar")

        elif profile.main_build_system == BuildSystem.GRADLE:
            if (self.project_path / "gradlew").exists():
                build_cmds.append("./gradlew build -x test")
            else:
                build_cmds.append("gradle build -x test")
            run_cmds.append("java -jar build/libs/*.jar")

        profile.build_commands = build_cmds
        profile.run_commands = run_cmds

    def _detect_main_binary(self, profile: ProjectProfile):
        """Try to detect the main binary/entry point."""
        # Check common entry point files
        entry_points = [
            "main.py", "app.py", "run.py", "server.py",
            "index.js", "server.js", "app.js", "main.js",
            "main.go", "cmd/main.go",
            "src/main.rs", "src/bin/main.rs",
            "src/main.c", "src/main.cpp", "main.c", "main.cpp",
        ]

        for ep in entry_points:
            if (self.project_path / ep).exists():
                profile.main_binary = ep
                break

        # Check Cargo.toml for binary name
        cargo_toml = self.project_path / "Cargo.toml"
        if cargo_toml.exists():
            with open(cargo_toml) as f:
                content = f.read()
                # Look for [[bin]] name
                match = re.search(r'\[\[bin\]\].*?name\s*=\s*"([^"]+)"', content, re.DOTALL)
                if match:
                    profile.main_binary = f"target/release/{match.group(1)}"
                # Look for package name
                elif "name" in content and not profile.main_binary:
                    match = re.search(r'\[package\].*?name\s*=\s*"([^"]+)"', content, re.DOTALL)
                    if match:
                        profile.main_binary = f"target/release/{match.group(1)}"

    def _detect_port(self, profile: ProjectProfile):
        """Try to detect the port the application listens on."""
        # Common port patterns
        port_patterns = [
            r'PORT\s*[=:]\s*(\d+)',
            r'listen\s*\(\s*(\d+)',
            r':(\d+)',
            r'port\s*[=:]\s*(\d+)',
        ]

        files_to_check = [
            "package.json", "docker-compose.yml", "docker-compose.yaml",
            ".env", ".env.example", "config.py", "config.js", "config.json"
        ]

        for fname in files_to_check:
            fpath = self.project_path / fname
            if fpath.exists():
                try:
                    with open(fpath) as f:
                        content = f.read()
                        for pattern in port_patterns:
                            match = re.search(pattern, content, re.IGNORECASE)
                            if match:
                                port = int(match.group(1))
                                if 1000 <= port <= 65535:
                                    profile.port = port
                                    return
                except (IOError, ValueError):
                    pass

        # Default ports based on language
        default_ports = {
            ProjectLanguage.NODE: 3000,
            ProjectLanguage.PYTHON: 8000,
            ProjectLanguage.RUBY: 3000,
            ProjectLanguage.GO: 8080,
            ProjectLanguage.JAVA: 8080,
        }

        if profile.main_language in default_ports:
            profile.port = default_ports[profile.main_language]

    def _select_base_image(self, profile: ProjectProfile):
        """Select the appropriate base image."""
        base_images = {
            ProjectLanguage.NODE: "node:20-slim",
            ProjectLanguage.PYTHON: "python:3.12-slim",
            ProjectLanguage.RUST: "rust:1-slim",
            ProjectLanguage.GO: "golang:1.22-bookworm",
            ProjectLanguage.JAVA: "eclipse-temurin:17-jdk",
            ProjectLanguage.RUBY: "ruby:3.3-slim",
            ProjectLanguage.PHP: "php:8.3-cli",
            ProjectLanguage.ELIXIR: "elixir:1.15-slim",
            ProjectLanguage.DOTNET: "mcr.microsoft.com/dotnet/sdk:8.0",
        }

        if profile.main_language in base_images:
            profile.base_image = base_images[profile.main_language]


class DockerfileGenerator:
    """Generate Dockerfiles based on project profile."""

    def __init__(self, profile: ProjectProfile):
        self.profile = profile

    def generate(self) -> str:
        """Generate a Dockerfile based on the project profile."""
        lines = []

        # Apply user hints
        hints = self.profile.user_hints

        # Base image
        base_image = hints.get("base_image", self.profile.base_image)
        lines.append(f"FROM {base_image}")
        lines.append("")

        # Labels
        lines.append("# Labels for identification")
        lines.append('LABEL maintainer="pf-containerize"')
        lines.append('LABEL generator="pf-web-poly-compile-helper-runner"')
        lines.append("")

        # Environment variables
        lines.append("# Environment variables")
        lines.append("ENV DEBIAN_FRONTEND=noninteractive")
        lines.append("ENV TZ=UTC")
        if self.profile.port:
            lines.append(f"ENV PORT={self.profile.port}")
        lines.append("")

        # Install system dependencies
        apt_packages = list(self.profile.apt_packages)

        # Add hint packages
        if "install_deps" in hints:
            extra_deps = hints["install_deps"]
            if isinstance(extra_deps, str):
                apt_packages.extend(extra_deps.split())
            elif isinstance(extra_deps, list):
                apt_packages.extend(extra_deps)

        if apt_packages:
            lines.append("# Install system dependencies")
            lines.append("RUN apt-get update && apt-get install -y \\")
            for pkg in sorted(set(apt_packages)):
                lines.append(f"    {pkg} \\")
            lines[-1] = lines[-1].rstrip(" \\")
            lines.append("    && rm -rf /var/lib/apt/lists/*")
            lines.append("")

        # Language-specific setup
        self._add_language_setup(lines)

        # Working directory
        workdir = hints.get("workdir", self.profile.working_dir)
        lines.append(f"# Set working directory")
        lines.append(f"WORKDIR {workdir}")
        lines.append("")

        # Copy source files
        lines.append("# Copy source files")
        lines.append("COPY . .")
        lines.append("")

        # Build commands
        build_commands = self.profile.build_commands
        if "build_commands" in hints:
            build_commands = hints["build_commands"]
            if isinstance(build_commands, str):
                build_commands = [build_commands]

        if build_commands:
            lines.append("# Build the application")
            for cmd in build_commands:
                lines.append(f"RUN {cmd}")
            lines.append("")

        # Expose port
        if self.profile.port:
            lines.append(f"# Expose application port")
            lines.append(f"EXPOSE {self.profile.port}")
            lines.append("")

        # Run command
        run_commands = self.profile.run_commands
        if "main_bin" in hints:
            run_commands = [hints["main_bin"]]
        elif "run_commands" in hints:
            run_commands = hints["run_commands"]
            if isinstance(run_commands, str):
                run_commands = [run_commands]

        if run_commands:
            lines.append("# Default command")
            # Use exec form for CMD
            cmd = run_commands[0]
            if isinstance(cmd, str):
                # Parse the command into parts for exec form
                parts = shlex.split(cmd)
                cmd_json = json.dumps(parts)
                lines.append(f"CMD {cmd_json}")
            else:
                lines.append(f"CMD {json.dumps(cmd)}")

        return "\n".join(lines)

    def _add_language_setup(self, lines: List[str]):
        """Add language-specific setup commands."""
        lang = self.profile.main_language

        if lang == ProjectLanguage.RUST:
            lines.append("# Install Rust toolchain")
            lines.append("RUN rustup default stable")
            lines.append("")

        elif lang == ProjectLanguage.GO:
            lines.append("# Go build settings")
            lines.append("ENV CGO_ENABLED=0")
            lines.append("ENV GOOS=linux")
            lines.append("")

        elif lang == ProjectLanguage.NODE:
            lines.append("# Node.js settings")
            lines.append("ENV NODE_ENV=production")
            lines.append("")

        elif lang == ProjectLanguage.PYTHON:
            lines.append("# Python settings")
            lines.append("ENV PYTHONDONTWRITEBYTECODE=1")
            lines.append("ENV PYTHONUNBUFFERED=1")
            lines.append("")


class QuadletGenerator:
    """Generate Quadlet files for systemd integration."""

    def __init__(self, profile: ProjectProfile, image_name: str):
        self.profile = profile
        self.image_name = image_name

    def generate_container(self, service_name: str = "app") -> str:
        """Generate a .container quadlet file."""
        lines = [
            "[Unit]",
            f"Description={service_name} container service",
            "Documentation=https://github.com/containers/podman/blob/main/docs/source/markdown/podman-systemd.unit.5.md",
            "",
            "[Container]",
            f"ContainerName={service_name}",
            f"Image={self.image_name}",
            "",
        ]

        # Add volume mounts
        lines.append("# Volume mounts")
        lines.append(f"Volume={service_name}-data:/app/data:rw,z")
        lines.append("")

        # Add port mapping
        if self.profile.port:
            lines.append("# Port mapping")
            lines.append(f"PublishPort={self.profile.port}:{self.profile.port}")
            lines.append("")

        # Environment variables
        lines.append("# Environment variables")
        lines.append("Environment=TZ=UTC")
        if self.profile.port:
            lines.append(f"Environment=PORT={self.profile.port}")
        lines.append("")

        # Security options
        lines.append("# Security options")
        lines.append("NoNewPrivileges=true")
        lines.append("")

        # Resource limits
        lines.append("# Resource limits")
        lines.append("Memory=512m")
        lines.append("CPUQuota=100%")
        lines.append("")

        # Health check
        lines.append("# Health check")
        if self.profile.port:
            lines.append(f"HealthCmd=curl -f http://localhost:{self.profile.port}/health || exit 1")
        else:
            lines.append("HealthCmd=pgrep -f app || exit 1")
        lines.append("HealthInterval=30s")
        lines.append("HealthTimeout=10s")
        lines.append("HealthRetries=3")
        lines.append("")

        # Labels
        lines.append("# Labels")
        lines.append(f"Label=app={service_name}")
        lines.append('Label=generator=pf-containerize')
        lines.append("")

        # Restart policy
        lines.append("# Restart policy")
        lines.append("Restart=always")
        lines.append("")

        # Install section
        lines.extend([
            "[Install]",
            "WantedBy=default.target"
        ])

        return "\n".join(lines)

    def generate_volume(self, service_name: str = "app") -> str:
        """Generate a .volume quadlet file."""
        return "\n".join([
            "[Volume]",
            f"VolumeName={service_name}-data",
            "",
            "# Labels",
            f"Label=app={service_name}",
            'Label=generator=pf-containerize',
        ])


class ContainerBuilder:
    """Build containers with retry and error recovery."""

    def __init__(self, project_path: str, retry_config: Optional[RetryConfig] = None):
        self.project_path = Path(project_path).resolve()
        self.retry_config = retry_config or RetryConfig()
        self.detector = ProjectDetector(str(self.project_path))

    def build(
        self,
        image_name: Optional[str] = None,
        tag: str = "latest",
        user_hints: Optional[Dict[str, Any]] = None
    ) -> ContainerBuildResult:
        """Build a container with automatic detection and retry."""
        result = ContainerBuildResult(success=False)

        # Detect project profile
        profile = self.detector.detect()
        if profile.errors:
            result.error_output = "\n".join(profile.errors)
            return result

        # Apply user hints
        profile.user_hints = user_hints or {}

        # Generate image name if not provided
        if not image_name:
            project_name = self.project_path.name.lower().replace("_", "-")
            image_name = f"localhost/{project_name}"

        full_image_name = f"{image_name}:{tag}"

        # Generate Dockerfile
        dockerfile_gen = DockerfileGenerator(profile)
        dockerfile_content = dockerfile_gen.generate()
        result.dockerfile_content = dockerfile_content

        # Generate Quadlet files
        quadlet_gen = QuadletGenerator(profile, full_image_name)
        result.quadlet_content = quadlet_gen.generate_container()

        # Write Dockerfile to temp location
        dockerfile_path = self.project_path / "Dockerfile.pf-generated"

        # Retry loop
        attempt = 0
        delay = self.retry_config.initial_delay

        while attempt < self.retry_config.max_attempts:
            attempt += 1
            result.attempts = attempt

            # Write current Dockerfile
            with open(dockerfile_path, "w") as f:
                f.write(dockerfile_content)

            # Try to build
            build_success, build_output, error_output = self._run_build(
                dockerfile_path, full_image_name
            )

            result.build_output += build_output
            result.error_output += error_output

            if build_success:
                result.success = True
                result.image_name = full_image_name
                # Clean up
                if dockerfile_path.exists():
                    dockerfile_path.unlink()
                return result

            # Check for fixable errors
            fixes = self._find_fixes(error_output, profile)
            if not fixes and attempt < self.retry_config.max_attempts:
                # No specific fix, but retry anyway (might be transient)
                time.sleep(delay)
                delay = min(delay * self.retry_config.backoff_factor, self.retry_config.max_delay)
                continue

            # Apply fixes and regenerate Dockerfile
            for fix_name, fix_commands in fixes:
                result.fixes_applied.append(fix_name)
                # Add fix commands to build
                for cmd in fix_commands:
                    if cmd not in profile.build_commands:
                        profile.build_commands.insert(0, cmd)

            # Regenerate Dockerfile with fixes
            dockerfile_gen = DockerfileGenerator(profile)
            dockerfile_content = dockerfile_gen.generate()
            result.dockerfile_content = dockerfile_content

            time.sleep(delay)
            delay = min(delay * self.retry_config.backoff_factor, self.retry_config.max_delay)

        # Clean up on failure
        if dockerfile_path.exists():
            dockerfile_path.unlink()

        return result

    def _run_build(
        self, dockerfile_path: Path, image_name: str
    ) -> Tuple[bool, str, str]:
        """Run the container build command."""
        # Prefer podman, fall back to docker
        runtime = "podman"
        try:
            subprocess.run(["podman", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            runtime = "docker"

        cmd = [
            runtime, "build",
            "-t", image_name,
            "-f", str(dockerfile_path),
            str(self.project_path)
        ]

        timeout = self.retry_config.build_timeout
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return (
                proc.returncode == 0,
                proc.stdout,
                proc.stderr
            )
        except subprocess.TimeoutExpired:
            return (False, "", f"Build timed out after {timeout // 60} minutes")
        except FileNotFoundError:
            return (False, "", f"Container runtime '{runtime}' not found")

    def _find_fixes(
        self, error_output: str, profile: ProjectProfile
    ) -> List[Tuple[str, List[str]]]:
        """Find applicable fixes for errors in build output."""
        fixes = []

        for pattern, description, fix_func in ERROR_PATTERNS:
            if re.search(pattern, error_output, re.IGNORECASE):
                fix_commands = fix_func(profile)
                if fix_commands:
                    fixes.append((description, fix_commands))

        return fixes


def containerize(
    project_path: str,
    image_name: Optional[str] = None,
    tag: str = "latest",
    install_hint_deps: Optional[str] = None,
    main_bin_hint: Optional[str] = None,
    port_hint: Optional[int] = None,
    base_image_hint: Optional[str] = None,
    build_commands_hint: Optional[List[str]] = None,
    max_retries: int = 3,
    build_timeout: int = 600
) -> ContainerBuildResult:
    """
    Main entry point for automatic containerization.

    Args:
        project_path: Path to the project directory
        image_name: Optional image name (auto-generated if not provided)
        tag: Image tag (default: "latest")
        install_hint_deps: Hint for additional apt packages to install
        main_bin_hint: Hint for the main binary/entry point
        port_hint: Hint for the port to expose
        base_image_hint: Hint for the base image to use
        build_commands_hint: Hint for custom build commands
        max_retries: Maximum number of build attempts
        build_timeout: Build timeout in seconds (default: 600)

    Returns:
        ContainerBuildResult with build status and generated files
    """
    user_hints = {}

    if install_hint_deps:
        user_hints["install_deps"] = install_hint_deps

    if main_bin_hint:
        user_hints["main_bin"] = main_bin_hint

    if port_hint:
        user_hints["port"] = port_hint

    if base_image_hint:
        user_hints["base_image"] = base_image_hint

    if build_commands_hint:
        user_hints["build_commands"] = build_commands_hint

    retry_config = RetryConfig(max_attempts=max_retries, build_timeout=build_timeout)
    builder = ContainerBuilder(project_path, retry_config)

    return builder.build(
        image_name=image_name,
        tag=tag,
        user_hints=user_hints
    )


def generate_dockerfile_only(
    project_path: str,
    install_hint_deps: Optional[str] = None,
    main_bin_hint: Optional[str] = None,
    port_hint: Optional[int] = None,
    base_image_hint: Optional[str] = None,
    build_commands_hint: Optional[List[str]] = None
) -> Tuple[str, ProjectProfile]:
    """
    Generate a Dockerfile without building.

    Returns:
        Tuple of (dockerfile_content, profile)
    """
    detector = ProjectDetector(project_path)
    profile = detector.detect()

    user_hints = {}
    if install_hint_deps:
        user_hints["install_deps"] = install_hint_deps
    if main_bin_hint:
        user_hints["main_bin"] = main_bin_hint
    if port_hint:
        user_hints["port"] = port_hint
    if base_image_hint:
        user_hints["base_image"] = base_image_hint
    if build_commands_hint:
        user_hints["build_commands"] = build_commands_hint

    profile.user_hints = user_hints

    generator = DockerfileGenerator(profile)
    return generator.generate(), profile


def generate_quadlet_files(
    project_path: str,
    image_name: str,
    service_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate Quadlet files for systemd integration.

    Returns:
        Dict with file names as keys and content as values
    """
    detector = ProjectDetector(project_path)
    profile = detector.detect()

    if not service_name:
        service_name = Path(project_path).name.lower().replace("_", "-")

    generator = QuadletGenerator(profile, image_name)

    return {
        f"{service_name}.container": generator.generate_container(service_name),
        f"{service_name}-data.volume": generator.generate_volume(service_name)
    }


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Automatic containerization for pf-runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-containerize a project
  python pf_containerize.py /path/to/project

  # With hints
  python pf_containerize.py /path/to/project --install-hint-deps="apt install libssl-dev"

  # Generate Dockerfile only (no build)
  python pf_containerize.py /path/to/project --dockerfile-only

  # Generate Quadlet files
  python pf_containerize.py /path/to/project --quadlet-only --image-name=myapp:latest
"""
    )

    parser.add_argument("project_path", help="Path to the project directory")
    parser.add_argument("--image-name", "-n", help="Image name (auto-generated if not provided)")
    parser.add_argument("--tag", "-t", default="latest", help="Image tag")
    parser.add_argument("--install-hint-deps", help="Additional apt packages to install")
    parser.add_argument("--main-bin-hint", help="Main binary/entry point")
    parser.add_argument("--port-hint", type=int, help="Port to expose")
    parser.add_argument("--base-image-hint", help="Base image to use")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum build attempts")
    parser.add_argument("--dockerfile-only", action="store_true", help="Only generate Dockerfile")
    parser.add_argument("--quadlet-only", action="store_true", help="Only generate Quadlet files")
    parser.add_argument("--output-dir", "-o", help="Output directory for generated files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    project_path = args.project_path
    output_dir = args.output_dir or project_path

    if args.dockerfile_only:
        dockerfile, profile = generate_dockerfile_only(
            project_path,
            install_hint_deps=args.install_hint_deps,
            main_bin_hint=args.main_bin_hint,
            port_hint=args.port_hint,
            base_image_hint=args.base_image_hint
        )
        print("Generated Dockerfile:")
        print("-" * 40)
        print(dockerfile)

        if args.output_dir:
            output_path = Path(args.output_dir) / "Dockerfile"
            with open(output_path, "w") as f:
                f.write(dockerfile)
            print(f"\nSaved to: {output_path}")

    elif args.quadlet_only:
        if not args.image_name:
            print("Error: --image-name is required for --quadlet-only")
            exit(1)

        quadlet_files = generate_quadlet_files(
            project_path,
            args.image_name
        )

        for filename, content in quadlet_files.items():
            print(f"\n{filename}:")
            print("-" * 40)
            print(content)

            if args.output_dir:
                output_path = Path(args.output_dir) / filename
                with open(output_path, "w") as f:
                    f.write(content)
                print(f"Saved to: {output_path}")

    else:
        result = containerize(
            project_path,
            image_name=args.image_name,
            tag=args.tag,
            install_hint_deps=args.install_hint_deps,
            main_bin_hint=args.main_bin_hint,
            port_hint=args.port_hint,
            base_image_hint=args.base_image_hint,
            max_retries=args.max_retries
        )

        if result.success:
            print(f"✅ Successfully built: {result.image_name}")
            print(f"   Attempts: {result.attempts}")
            if result.fixes_applied:
                print(f"   Fixes applied: {', '.join(result.fixes_applied)}")
        else:
            print(f"❌ Build failed after {result.attempts} attempts")
            if args.verbose:
                print("\nBuild output:")
                print(result.build_output)
                print("\nError output:")
                print(result.error_output)

        if args.verbose:
            print("\nGenerated Dockerfile:")
            print("-" * 40)
            print(result.dockerfile_content)

        if args.output_dir:
            # Save Dockerfile
            with open(Path(args.output_dir) / "Dockerfile.generated", "w") as f:
                f.write(result.dockerfile_content)
            # Save Quadlet
            with open(Path(args.output_dir) / "app.container", "w") as f:
                f.write(result.quadlet_content)
            print(f"\nGenerated files saved to: {args.output_dir}")
