FROM ubuntu:24.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV RUSTUP_HOME=/opt/rust
ENV CARGO_HOME=/opt/cargo
ENV PATH="/opt/cargo/bin:${PATH}"

# Create non-root user
RUN groupadd -r pf --gid=1000 && \
    useradd -r -g pf --uid=1000 --home-dir=/home/pf --shell=/bin/bash pf && \
    mkdir -p /home/pf && \
    chown -R pf:pf /home/pf

# Install base packages and debugging tools
RUN apt-get update && apt-get install -y \
    # Core system tools
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    tree \
    jq \
    unzip \
    zip \
    tar \
    gzip \
    # Build essentials
    build-essential \
    pkg-config \
    cmake \
    make \
    autoconf \
    automake \
    libtool \
    # Debugging tools
    gdb \
    lldb \
    strace \
    ltrace \
    lsof \
    # Network tools
    net-tools \
    iputils-ping \
    netcat-openbsd \
    # Process monitoring
    procps \
    psmisc \
    # SSL/TLS
    ca-certificates \
    openssl \
    # Python for tooling
    python3 \
    python3-pip \
    python3-venv \
    # Additional build dependencies
    libssl-dev \
    libffi-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-0 \
    libsqlite3-dev \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    # Fortran compiler
    gfortran \
    # LLVM tools
    llvm \
    clang \
    # Sudo access
    sudo \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Configure sudo for pf user
RUN echo "pf ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Install Rust toolchain system-wide
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable --profile default && \
    chmod -R a+w $RUSTUP_HOME $CARGO_HOME

# Install wasm-pack for Rust WebAssembly builds
RUN /opt/cargo/bin/cargo install wasm-pack

# Install Node.js 20.x for some build tools
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Emscripten for C/C++ to WebAssembly
RUN git clone https://github.com/emscripten-core/emsdk.git /opt/emsdk && \
    cd /opt/emsdk && \
    ./emsdk install latest && \
    ./emsdk activate latest && \
    chmod -R a+w /opt/emsdk

# Install WABT (WebAssembly Binary Toolkit)
RUN cd /tmp && \
    wget https://github.com/WebAssembly/wabt/releases/download/1.0.34/wabt-1.0.34-ubuntu.tar.gz && \
    tar -xzf wabt-1.0.34-ubuntu.tar.gz && \
    cp wabt-1.0.34/bin/* /usr/local/bin/ && \
    rm -rf wabt-1.0.34*

# Install LFortran (experimental Fortran to WASM)
RUN pip3 install lfortran

# Create application directories
RUN mkdir -p /workspace /app /data /cache /builds && \
    chown -R pf:pf /workspace /app /data /cache /builds

# Switch to non-root user
USER pf
WORKDIR /workspace

# Set up environment for pf user
RUN echo 'export PATH="/opt/cargo/bin:$PATH"' >> ~/.bashrc && \
    echo 'export RUSTUP_HOME=/opt/rust' >> ~/.bashrc && \
    echo 'export CARGO_HOME=/opt/cargo' >> ~/.bashrc && \
    echo 'source /opt/emsdk/emsdk_env.sh' >> ~/.bashrc && \
    echo 'export PS1="\u@\h:\w\$ "' >> ~/.bashrc && \
    echo 'alias ll="ls -la"' >> ~/.bashrc

# Create entrypoint script
COPY --chown=pf:pf containers/build-environment/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD rustc --version && node --version && emcc --version && wat2wasm --version || exit 1

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]
CMD ["bash"]