# AI Arr Control


Autonomous AI-agent platform to manage, monitor, and heal Radarr, Sonarr, and Prowlarr indexers.


## Features
- Indexer discovery
- Health checks
- Automated testing
- Extendable agent architecture


## Run


```bash
python -m venv venv
source venv/bin/activate
pip install -e .
uvicorn main:app --reload