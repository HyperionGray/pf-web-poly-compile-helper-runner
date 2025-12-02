FROM ubuntu:24.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Create non-root user early
RUN groupadd -r pf --gid=1000 && \
    useradd -r -g pf --uid=1000 --home-dir=/home/pf --shell=/bin/bash pf && \
    mkdir -p /home/pf && \
    chown -R pf:pf /home/pf

# Install essential packages and debugging tools (not bare!)
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
    # Debugging and development tools
    gdb \
    strace \
    ltrace \
    lsof \
    netstat-nat \
    tcpdump \
    # Network tools
    net-tools \
    iputils-ping \
    telnet \
    netcat-openbsd \
    # Process and system monitoring
    procps \
    psmisc \
    # Text processing
    grep \
    sed \
    awk \
    # File utilities
    file \
    which \
    locate \
    # SSL/TLS tools
    ca-certificates \
    openssl \
    # Python basics (needed for many tools)
    python3 \
    python3-pip \
    python3-venv \
    # Shell utilities
    bash-completion \
    # Sudo for privilege escalation
    sudo \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Configure sudo for pf user
RUN echo "pf ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set up locale
RUN apt-get update && apt-get install -y locales && \
    locale-gen en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

# Create common directories
RUN mkdir -p /workspace /app /data /cache && \
    chown -R pf:pf /workspace /app /data /cache

# Switch to non-root user
USER pf
WORKDIR /home/pf

# Set up basic shell environment
RUN echo 'export PS1="\u@\h:\w\$ "' >> ~/.bashrc && \
    echo 'alias ll="ls -la"' >> ~/.bashrc && \
    echo 'alias la="ls -la"' >> ~/.bashrc && \
    echo 'alias l="ls -l"' >> ~/.bashrc

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD echo "Base container healthy" || exit 1

CMD ["/bin/bash"]