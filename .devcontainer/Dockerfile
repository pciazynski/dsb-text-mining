FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# Install Python, PHP, Node.js, and utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg \
    python3 python3-pip python3-venv \
    php php-cli php-mbstring php-xml php-curl php-zip php-intl php8.3-sqlite3 \
    composer \
    nodejs npm \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Composer (official installer, in case apt version is outdated)
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

RUN mkdir -p /commandhistory && chown vscode:vscode /commandhistory

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

USER vscode
WORKDIR /workspace
