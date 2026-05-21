FROM mcr.microsoft.com/playwright/python:v1.50.0-jammy

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

RUN pip install --no-cache-dir \
        "playwright==1.50.0" \
        "playwright-stealth==1.0.6" \
        "python-dotenv==1.0.1" \
        "requests==2.32.3" \
        "schedule==1.2.2" \
        "loguru==0.7.2"

RUN mkdir -p /app/local_data/automation/storage_states \
             /app/local_data/automation/logs \
             /app/local_data/statements

COPY . /app/scripts/automation/

CMD ["python", "-m", "scripts.automation.scheduler"]
