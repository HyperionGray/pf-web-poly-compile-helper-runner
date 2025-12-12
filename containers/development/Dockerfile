FROM ubuntu:24.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONPATH="/workspace/pf-runner:${PYTHONPATH}"
ENV PATH="/home/pf/.local/bin:${PATH}"

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
    # Python development
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    # Additional development tools
    ssh \
    rsync \
    less \
    man-db \
    manpages \
    manpages-dev \
    # Text processing
    grep \
    sed \
    awk \
    # File utilities
    file \
    which \
    locate \
    # Shell utilities
    bash-completion \
    # Sudo access
    sudo \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Configure sudo for pf user
RUN echo "pf ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Create application directories
RUN mkdir -p /workspace /app /data /cache && \
    chown -R pf:pf /workspace /app /data /cache

# Switch to non-root user
USER pf
WORKDIR /workspace

# Install Python dependencies for pf-runner
RUN pip3 install --user \
    fabric>=3.2,<4 \
    rich \
    click \
    pyyaml \
    requests \
    lark

# Copy pf-runner source code
COPY --chown=pf:pf pf-runner/ ./pf-runner/

# Copy main project files
COPY --chown=pf:pf Pfyfile*.pf ./
COPY --chown=pf:pf *.md ./
COPY --chown=pf:pf demos/ ./demos/
COPY --chown=pf:pf tools/ ./tools/
COPY --chown=pf:pf examples/ ./examples/

# Set up pf-runner
RUN cd pf-runner && \
    make setup && \
    make install-local

# Install shell completions
RUN mkdir -p ~/.bash_completion.d && \
    cp pf-runner/completions/pf-completion.bash ~/.bash_completion.d/ && \
    echo 'source ~/.bash_completion.d/pf-completion.bash' >> ~/.bashrc

# Set up environment
RUN echo 'export PATH="/home/pf/.local/bin:$PATH"' >> ~/.bashrc && \
    echo 'export PYTHONPATH="/workspace/pf-runner:$PYTHONPATH"' >> ~/.bashrc && \
    echo 'export PS1="\u@\h:\w\$ "' >> ~/.bashrc && \
    echo 'alias ll="ls -la"' >> ~/.bashrc && \
    echo 'alias la="ls -la"' >> ~/.bashrc && \
    echo 'alias l="ls -l"' >> ~/.bashrc && \
    echo 'alias pf-help="pf list"' >> ~/.bashrc

# Create entrypoint script
COPY --chown=pf:pf containers/development/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD pf --version || exit 1

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]
CMD ["bash"]