"""Runtime smoke-check script.

Starts the FastAPI app in-process using TestClient, queries key endpoints,
inspects scheduler/job state, and reports results. This avoids needing uvicorn
on PATH and is safe to run in CI or developer environments.
"""
from pprint import pprint
from time import sleep
import sys
from pathlib import Path

# Ensure repo root is on sys.path so we can import top-level modules when
# running this script directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from main import app


def main() -> None:
    print("Starting in-process test client for app...")
    with TestClient(app) as client:
        print("Client started. Querying /health")
        r = client.get("/health")
        print("/health ->", r.status_code)
        pprint(r.json())

        print("Querying /agents/status")
        r2 = client.get("/agents/status")
        print("/agents/status ->", r2.status_code)
        try:
            data = r2.json()
        except Exception:
            data = r2.text
        pprint(data)

        print("Querying /indexers (may contact external services)")
        r3 = client.get("/indexers")
        print("/indexers ->", r3.status_code)
        try:
            pprint(r3.json())
        except Exception:
            print(r3.text[:400])

        # Allow scheduler jobs to be visible (they run in background threads)
        print("Sleeping 1s to allow scheduler/state stabilization...")
        sleep(1)

        scheduler = getattr(app.state, "scheduler", None)
        if scheduler is None:
            print("No scheduler attached to app.state")
        else:
            print("Scheduler running:", scheduler.running)
            jobs = scheduler.get_jobs()
            print("Jobs count:", len(jobs))
            for j in jobs:
                print("-", j.id, j.name, "next_run:", j.next_run_time)

    print("TestClient exited; app shutdown should be complete.")


if __name__ == "__main__":
    main()
