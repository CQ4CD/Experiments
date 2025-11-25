import json
import os
from pathlib import Path

import dotenv
import requests

dotenv.load_dotenv()

gitlab_url = os.getenv("GITLAB_URL")
project_id = "9767"
token = os.getenv("GITLAB_TOKEN")
experiment_number = 0

headers = {"PRIVATE-TOKEN": token}

run_id_file = Path(__file__).parent / f"run_ids_{experiment_number}.json"
run_ids = json.loads(run_id_file.read_text())

output_root = Path(__file__).parent / f"experiment_{experiment_number}"
output_root.mkdir(exist_ok=True)

indices_120 = []
durations = []

for run_id in run_ids:
    jobs_url = f"{gitlab_url}/api/v4/projects/{project_id}/pipelines/{run_id}/jobs"
    jobs = requests.get(jobs_url, headers=headers).json()

    run_folder = output_root / str(run_id)
    run_folder.mkdir(exist_ok=True)

    enriched = []
    for job in jobs:
        job_id = job["id"]
        trace = requests.get(f"{gitlab_url}/api/v4/projects/{project_id}/jobs/{job_id}/trace", headers=headers).text
        (run_folder / f"{job_id}.log").write_text(trace)
