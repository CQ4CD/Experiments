import json

import requests

from experiments.commons import (get_latest_experiment_number, get_run_id_file,
                                 gitlab_url, gitlab_headers, gitlab_project_id, get_experiment_folder)

experiment_number = get_latest_experiment_number('gitlab')
run_id_file = get_run_id_file(experiment_number, 'gitlab')
run_ids = json.loads(run_id_file.read_text())
output_root = get_experiment_folder(experiment_number, 'gitlab')
output_root.mkdir(exist_ok=True)

indices_120 = []
durations = []

for run_id in run_ids:
    jobs_url = f"{gitlab_url}/api/v4/projects/{gitlab_project_id}/pipelines/{run_id}/jobs"
    jobs = requests.get(jobs_url, headers=gitlab_headers).json()

    run_folder = output_root / str(run_id)
    run_folder.mkdir(exist_ok=True)

    enriched = []
    for job in jobs:
        job_id = job["id"]
        trace = requests.get(f"{gitlab_url}/api/v4/projects/{gitlab_project_id}/jobs/{job_id}/trace", headers=gitlab_headers).text
        (run_folder / f"{job_id}.log").write_text(trace)
