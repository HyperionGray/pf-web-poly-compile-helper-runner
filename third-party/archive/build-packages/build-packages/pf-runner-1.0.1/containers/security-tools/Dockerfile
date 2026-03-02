FROM ubuntu:24.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PATH="/home/pf/.local/bin:${PATH}"

# Create non-root user
RUN groupadd -r pf --gid=1000 && \
    useradd -r -g pf --uid=1000 --home-dir=/home/pf --shell=/bin/bash pf && \
    mkdir -p /home/pf && \
    chown -R pf:pf /home/pf

# Install base packages and extensive debugging tools
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
    # Debugging and analysis tools
    gdb \
    gdb-multiarch \
    lldb \
    strace \
    ltrace \
    lsof \
    valgrind \
    # Binary analysis tools
    binutils \
    objdump \
    readelf \
    nm \
    strings \
    file \
    hexdump \
    xxd \
    # Network analysis
    net-tools \
    iputils-ping \
    netcat-openbsd \
    tcpdump \
    wireshark-common \
    nmap \
    # Process monitoring
    procps \
    psmisc \
    # Disassemblers and hex editors
    radare2 \
    # Python for exploit development
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    # Reverse engineering dependencies
    libssl-dev \
    libffi-dev \
    zlib1g-dev \
    # Additional security tools
    checksec \
    # SSL/TLS
    ca-certificates \
    openssl \
    # Sudo access
    sudo \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Configure sudo for pf user
RUN echo "pf ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Install additional security and reverse engineering tools
RUN apt-get update && apt-get install -y \
    # Additional binary analysis
    elfutils \
    dwarfdump \
    # Forensics tools
    foremost \
    # Crypto tools
    hashcat \
    john \
    # Network security
    aircrack-ng \
    # Web security
    sqlmap \
    nikto \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create application directories
RUN mkdir -p /workspace /app /data /cache /tools && \
    chown -R pf:pf /workspace /app /data /cache /tools

# Switch to non-root user
USER pf
WORKDIR /workspace

# Install Python security and exploit development tools
RUN pip3 install --user \
    pwntools \
    ropper \
    capstone \
    keystone-engine \
    unicorn \
    angr \
    z3-solver \
    requests \
    beautifulsoup4 \
    scapy \
    pycryptodome \
    rich \
    click

# Install ROPgadget
RUN pip3 install --user ROPgadget

# Install additional tools via git
RUN cd /tmp && \
    # Install pwndbg
    git clone https://github.com/pwndbg/pwndbg && \
    cd pwndbg && \
    ./setup.sh && \
    cd .. && \
    rm -rf pwndbg

# Install Ghidra (headless mode)
RUN cd /opt && \
    sudo wget https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_11.0.1_build/ghidra_11.0.1_PUBLIC_20240130.zip && \
    sudo unzip ghidra_11.0.1_PUBLIC_20240130.zip && \
    sudo mv ghidra_11.0.1_PUBLIC /opt/ghidra && \
    sudo chown -R pf:pf /opt/ghidra && \
    sudo rm ghidra_11.0.1_PUBLIC_20240130.zip

# Install Java for Ghidra
RUN sudo apt-get update && sudo apt-get install -y openjdk-17-jdk && \
    sudo rm -rf /var/lib/apt/lists/*

# Copy security tools and scripts
COPY --chown=pf:pf tools/debugging/ ./tools/debugging/
COPY --chown=pf:pf tools/exploit/ ./tools/exploit/
COPY --chown=pf:pf tools/injection/ ./tools/injection/
COPY --chown=pf:pf tools/kernel-debug/ ./tools/kernel-debug/
COPY --chown=pf:pf tools/lifting/ ./tools/lifting/
COPY --chown=pf:pf tools/security/ ./tools/security/

# Make scripts executable
RUN find ./tools -name "*.sh" -exec chmod +x {} \; && \
    find ./tools -name "*.py" -exec chmod +x {} \;

# Set up environment
RUN echo 'export PATH="/home/pf/.local/bin:/opt/ghidra/support:$PATH"' >> ~/.bashrc && \
    echo 'export GHIDRA_INSTALL_DIR="/opt/ghidra"' >> ~/.bashrc && \
    echo 'export PS1="\u@\h:\w\$ "' >> ~/.bashrc && \
    echo 'alias ll="ls -la"' >> ~/.bashrc && \
    echo 'alias la="ls -la"' >> ~/.bashrc && \
    echo 'alias l="ls -l"' >> ~/.bashrc && \
    echo 'alias gdb="gdb -q"' >> ~/.bashrc && \
    echo 'alias r2="radare2"' >> ~/.bashrc

# Create entrypoint script
COPY --chown=pf:pf containers/security-tools/entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD gdb --version && python3 -c "import pwn" && radare2 -v || exit 1

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]
CMD ["bash"]