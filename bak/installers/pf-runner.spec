Name:           pf-runner
Version:        1.0.0
Release:        1%{?dist}
Summary:        Polyglot task runner with symbol-free DSL

License:        MIT
URL:            https://github.com/example/pf-runner
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel >= 3.8
BuildRequires:  python3-setuptools
BuildRequires:  python3-pip

# Core package dependencies
Requires:       python3 >= 3.8
Requires:       python3-pip
Requires:       git
Requires:       curl

%description
pf-runner is a lightweight, single-file task runner with a symbol-free DSL
for managing development workflows. It provides polyglot shell support,
build system helpers, parallel execution, and modular configuration.

%package core
Summary:        Core pf-runner functionality
Requires:       python3 >= 3.8
Requires:       python3-pip
Requires:       git
Requires:       curl
Recommends:     gcc
Recommends:     gcc-c++
Recommends:     make
Recommends:     python3-devel

%description core
This package contains the core pf-runner functionality including:
- Main task runner with Python/Fabric backend
- Symbol-free DSL parser
- Basic shell and build system integration
- Configuration file support

%package langs
Summary:        Language toolchain support for pf-runner
Requires:       %{name}-core = %{version}-%{release}
Requires:       python3
Requires:       nodejs
Requires:       npm
Recommends:     golang
Recommends:     rust
Recommends:     cargo
Recommends:     gcc
Recommends:     gcc-c++
Recommends:     make
Recommends:     cmake
Suggests:       java-11-openjdk-devel
Suggests:       gcc-gfortran
Suggests:       lua
Suggests:       ruby

%description langs
This package provides language toolchain integration for pf-runner,
enabling polyglot development workflows with multiple programming languages.

Supported languages include:
- Python (built-in)
- Node.js/JavaScript
- Go
- Rust
- C/C++
- Java
- Fortran
- Lua
- Ruby

%package tools
Summary:        Additional development tools for pf-runner
Requires:       %{name}-core = %{version}-%{release}
Recommends:     podman
Recommends:     git
Recommends:     curl
Recommends:     wget
Recommends:     jq
Recommends:     tree
Suggests:       gdb
Suggests:       lldb
Suggests:       strace
Suggests:       ltrace
Suggests:       valgrind

%description tools
This package provides additional development and debugging tools
that integrate with pf-runner workflows.

Includes support for:
- Container runtimes (Docker/Podman)
- Debugging tools
- System analysis utilities
- Network and file utilities
- JSON processing tools

%package -n pf-runner
Summary:        Complete pf-runner installation (metapackage)
Requires:       %{name}-core = %{version}-%{release}
Requires:       %{name}-langs = %{version}-%{release}
Recommends:     %{name}-tools = %{version}-%{release}

%description -n pf-runner
This metapackage installs the complete pf-runner suite including
core functionality, language toolchains, and recommended tools.

This is the recommended package for most users who want a full
pf-runner installation with comprehensive language and tool support.

%prep
%autosetup -n %{name}-%{version}

%build
cd pf-runner
%py3_build

%install
cd pf-runner
%py3_install

# Create installation directories
mkdir -p %{buildroot}%{_libdir}/pf-runner
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
mkdir -p %{buildroot}%{_datadir}/zsh/site-functions
mkdir -p %{buildroot}%{_unitdir}

# Install core pf-runner files
cp -r * %{buildroot}%{_libdir}/pf-runner/

# Install bundled fabric library
cp -r ../fabric %{buildroot}%{_libdir}/pf-runner/

# Create main executable
cat > %{buildroot}%{_bindir}/pf << 'EOF'
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, "%{_libdir}/pf-runner")
from pf_main import main
if __name__ == "__main__": main()
EOF
chmod +x %{buildroot}%{_bindir}/pf

# Install shell completions
cp completions/pf-completion.bash %{buildroot}%{_datadir}/bash-completion/completions/pf
cp completions/_pf %{buildroot}%{_datadir}/zsh/site-functions/_pf

# Install systemd service files
cp *.service %{buildroot}%{_unitdir}/ || true

# Clean up unnecessary files
find %{buildroot}%{_libdir}/pf-runner -name "*.pyc" -delete
find %{buildroot}%{_libdir}/pf-runner -name "__pycache__" -type d -exec rm -rf {} + || true
rm -f %{buildroot}%{_libdir}/pf-runner/Makefile
rm -f %{buildroot}%{_libdir}/pf-runner/test*.pf
rm -f %{buildroot}%{_libdir}/pf-runner/*.md
rm -f %{buildroot}%{_libdir}/pf-runner/setup.py

%files core
%license ../LICENSE*
%doc ../README.md
%{_bindir}/pf
%{_libdir}/pf-runner/
%{_datadir}/bash-completion/completions/pf
%{_datadir}/zsh/site-functions/_pf
%{_unitdir}/*.service

%files langs
# This is a metapackage, no files

%files tools  
# This is a metapackage, no files

%files -n pf-runner
# This is a metapackage, no files

%post core
# Update shell completion databases
if [ -x /usr/bin/update-bash-completion ]; then
    /usr/bin/update-bash-completion || true
fi

# Reload systemd daemon if systemd is running
if [ -d /run/systemd/system ]; then
    systemctl daemon-reload || true
fi

# Create symlink for backward compatibility
if [ ! -e %{_libdir}/pf-runner/pf ]; then
    ln -sf pf_main.py %{_libdir}/pf-runner/pf || true
fi

echo "pf-runner-core installed successfully!"
echo "Try: pf --version"
echo "     pf list"

%preun core
# Stop any running pf services
if [ -d /run/systemd/system ]; then
    systemctl stop 'pf-*' || true
    systemctl daemon-reload || true
fi

%postun core
if [ $1 -eq 0 ]; then
    # Remove any remaining configuration files on purge
    rm -rf /etc/pf-runner || true
    
    # Clean up any remaining symlinks
    rm -f %{_libdir}/pf-runner/pf || true
fi

%changelog
* $(date "+%a %b %d %Y") PF Runner Team <maintainer@example.com> - 1.0.0-1
- Initial release of pf-runner
- Polyglot task runner with symbol-free DSL
- Support for 40+ programming languages
- Container and native installation modes
- Package management and build system integration
- Web development and security testing tools
- Binary analysis and debugging capabilities