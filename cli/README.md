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
richtato bank       # Bank sync setup and operations
richtato build      # Build Docker image locally
richtato publish    # Build & push to Docker Hub
```

## Bank Sync

Download `richtato-bank-agent-setup.yml` from Richtato, keep it in the repo
root, then run:

```bash
richtato bank setup
```

The guided setup creates or reuses `scripts/bank_sync/.venv`, installs the
Playwright bank-agent requirements, applies the setup YAML to the encrypted
local vault, shows status, and lets you sign in or run a sync.

Common direct commands:

```bash
richtato bank status
richtato bank signin <login_id>
richtato bank sync <login_id>
richtato bank daemon
richtato bank logs --follow
```

## Requirements

- Python 3.10+
- Docker & Docker Compose
- Must be run from within the richtato project directory (or set `RICHTATO_ROOT` env var)
