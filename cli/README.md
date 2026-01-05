# Richtato CLI

Interactive development and deployment tool for the Richtato project.

## Installation

```bash
# From the cli/ directory
pip install -e .
```

## Usage

```bash
# Interactive menu
richtato

# Direct commands
richtato dev        # Start/stop dev containers
richtato logs       # View container logs
richtato shell      # Open container shell
richtato migrate    # Run Django migrations
richtato build      # Build Docker image locally
richtato publish    # Build & push to Docker Hub
```

## Requirements

- Python 3.10+
- Docker & Docker Compose
- Must be run from within the richtato project directory (or set `RICHTATO_ROOT` env var)
