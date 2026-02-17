FROM ubuntu:24.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV NODE_ENV=production

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
    # Build essentials for native modules
    build-essential \
    pkg-config \
    # Debugging tools
    gdb \
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
    # Sudo access
    sudo \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Node.js 20.x (LTS)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Configure sudo for pf user
RUN echo "pf ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Create application directories
RUN mkdir -p /app /workspace /data /cache && \
    chown -R pf:pf /app /workspace /data /cache

# Switch to non-root user
USER pf
WORKDIR /app

# Copy package files
COPY --chown=pf:pf package*.json ./

# Install Node.js dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# Copy application code
COPY --chown=pf:pf tools/ ./tools/
COPY --chown=pf:pf demos/pf-web-polyglot-demo-plus-c/web/ ./web/

# Create entrypoint script
COPY --chown=pf:pf containers/web-services/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Expose ports
EXPOSE 8080 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]
CMD ["api-server"]