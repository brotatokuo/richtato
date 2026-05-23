cd ~/richtato && conda activate richtato
python scripts/statement_downloader.py bofa \
  --storage-state local_data/automation/storage_states/bofa_b.json

  docker compose exec automation python -m scripts.automation.runner --account bofa_a_checking --headed
