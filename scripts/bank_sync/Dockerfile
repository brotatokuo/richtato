# Bank-sync Playwright agent.
#
# Image ships with Chromium + the Playwright Python bindings preinstalled
# (via the mcr.microsoft.com/playwright/python base image) so we do not
# have to download Chromium at runtime. The container can run both
# headless (scheduled_download) and headed (interactive_login) by passing
# DISPLAY + mounting /tmp/.X11-unix from the host.

FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        tini \
    && rm -rf /var/lib/apt/lists/*

COPY scripts/bank_sync/requirements.txt /app/scripts/bank_sync/requirements.txt
RUN pip install --no-cache-dir -r /app/scripts/bank_sync/requirements.txt

COPY scripts/bank_sync /app/scripts/bank_sync

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "-m", "scripts.bank_sync.agent"]
