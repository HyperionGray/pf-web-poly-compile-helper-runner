# Maintainer: PF Runner Team <maintainer@example.com>
pkgbase=pf-runner
pkgname=('pf-runner-core' 'pf-runner-langs' 'pf-runner-tools' 'pf-runner')
pkgver=1.0.0
pkgrel=1
pkgdesc="Polyglot task runner with symbol-free DSL"
arch=('any')
url="https://github.com/example/pf-runner"
license=('MIT')
makedepends=('python' 'python-setuptools' 'python-pip')
source=("$pkgbase-$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
    cd "$srcdir/$pkgbase-$pkgver/pf-runner"
    python setup.py build
}

package_pf-runner-core() {
    pkgdesc="Core pf-runner functionality"
    depends=('python>=3.8' 'python-pip' 'git' 'curl')
    optdepends=(
        'gcc: C/C++ compilation support'
        'make: Build system support'
        'python-dev: Python development headers'
    )
    
    cd "$srcdir/$pkgbase-$pkgver"
    
    # Create installation directories
    install -dm755 "$pkgdir/usr/lib/pf-runner"
    install -dm755 "$pkgdir/usr/bin"
    install -dm755 "$pkgdir/usr/share/bash-completion/completions"
    install -dm755 "$pkgdir/usr/share/zsh/site-functions"
    install -dm755 "$pkgdir/usr/lib/systemd/system"
    
    # Install core pf-runner files
    cp -r pf-runner/* "$pkgdir/usr/lib/pf-runner/"
    
    # Install bundled fabric library
    cp -r fabric "$pkgdir/usr/lib/pf-runner/"
    
    # Create main executable
    cat > "$pkgdir/usr/bin/pf" << 'EOF'
#!/usr/bin/env python3
import sys, os
sys.path.insert(0, "/usr/lib/pf-runner")
from pf_main import main
if __name__ == "__main__": main()
EOF
    chmod +x "$pkgdir/usr/bin/pf"
    
    # Install shell completions
    install -Dm644 pf-runner/completions/pf-completion.bash \
        "$pkgdir/usr/share/bash-completion/completions/pf"
    install -Dm644 pf-runner/completions/_pf \
        "$pkgdir/usr/share/zsh/site-functions/_pf"
    
    # Install systemd service files
    install -Dm644 pf-runner/*.service "$pkgdir/usr/lib/systemd/system/" || true
    
    # Clean up unnecessary files
    find "$pkgdir/usr/lib/pf-runner" -name "*.pyc" -delete
    find "$pkgdir/usr/lib/pf-runner" -name "__pycache__" -type d -exec rm -rf {} + || true
    rm -f "$pkgdir/usr/lib/pf-runner/Makefile"
    rm -f "$pkgdir/usr/lib/pf-runner/test"*.pf
    rm -f "$pkgdir/usr/lib/pf-runner/"*.md
    rm -f "$pkgdir/usr/lib/pf-runner/setup.py"
    
    # Install license and documentation
    install -Dm644 LICENSE* "$pkgdir/usr/share/licenses/$pkgname/"
    install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/"
}

package_pf-runner-langs() {
    pkgdesc="Language toolchain support for pf-runner"
    depends=('pf-runner-core' 'python' 'nodejs' 'npm')
    optdepends=(
        'go: Go language support'
        'rust: Rust language support'
        'gcc: C/C++ language support'
        'make: Build system support'
        'cmake: CMake build system support'
        'jdk11-openjdk: Java language support'
        'gcc-fortran: Fortran language support'
        'lua: Lua language support'
        'ruby: Ruby language support'
    )
    
    # This is a metapackage, no files to install
    mkdir -p "$pkgdir/usr/share/doc/$pkgname"
    echo "This is a metapackage for pf-runner language support." > \
        "$pkgdir/usr/share/doc/$pkgname/README"
}

package_pf-runner-tools() {
    pkgdesc="Additional development tools for pf-runner"
    depends=('pf-runner-core')
    optdepends=(
        'podman: Container runtime support'
        'docker: Container runtime support'
        'git: Version control support'
        'curl: HTTP client support'
        'wget: Download utility'
        'jq: JSON processor'
        'tree: Directory tree viewer'
        'gdb: GNU debugger'
        'lldb: LLVM debugger'
        'strace: System call tracer'
        'ltrace: Library call tracer'
        'valgrind: Memory debugging tool'
    )
    
    # This is a metapackage, no files to install
    mkdir -p "$pkgdir/usr/share/doc/$pkgname"
    echo "This is a metapackage for pf-runner development tools." > \
        "$pkgdir/usr/share/doc/$pkgname/README"
}

package_pf-runner() {
    pkgdesc="Complete pf-runner installation (metapackage)"
    depends=('pf-runner-core' 'pf-runner-langs')
    optdepends=('pf-runner-tools: Additional development tools')
    
    # This is a metapackage, no files to install
    mkdir -p "$pkgdir/usr/share/doc/$pkgname"
    echo "This is the complete pf-runner metapackage." > \
        "$pkgdir/usr/share/doc/$pkgname/README"
}