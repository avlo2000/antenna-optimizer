# Use the official Ubuntu 22.04 as the base image
FROM ubuntu:22.04

# Set environment variables to prevent interactive prompts during package installations
ENV DEBIAN_FRONTEND=noninteractive

# Update and install required packages including Python, Git, and the new tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    python3.10 \
    python3.10-dev \
    python3.10-venv \
    gettext \
    autopoint \
    libglib2.0-dev-bin \
    pkg-config \
    autoconf \
    libtool \
    libglib2.0-dev \
    make \
    gtk+-3.0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Clone the first repository into the /xnec2c folder
RUN git clone https://github.com/KJ7LNW/xnec2c.git /xnec2c

# Set the working directory to /xnec2c
WORKDIR /xnec2c

# Run the required build commands for the xnec2c repo
RUN ./autogen.sh && \
    ./configure && \
    make && make install

WORKDIR /

# Clone the second repository
RUN git clone https://github.com/avlo2000/antenna-optimizer.git /antenna-optimizer

# Set working directory (can be set to any desired location, or leave it in /xnec2c)
WORKDIR /antenna-optimizer

# Run the required build commands for the antenna-optimizer repo
RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install numpy==2.1.1 && \
    pip install -r requirements.txt &&\
    deactivate

# Optionally add any command to run during container start, like bash or an entry point
CMD ["/bin/bash"]
