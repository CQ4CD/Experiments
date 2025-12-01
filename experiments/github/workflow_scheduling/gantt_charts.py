import json
from datetime import datetime

import requests

from experiments.commons import get_latest_experiment_number, get_experiment_folder, plot_job_gantt, \
    get_run_id_file, gh_runs_url, gh_headers, JobDuration

experiment_number = 0
experiments_folder = get_experiment_folder(experiment_number)
run_id_file = get_run_id_file(experiment_number)


def main():
    run_ids = json.loads(run_id_file.read_text())
    for run_id in run_ids:
        print('Creating Gantt chart for run', run_id)
        jobs = requests.get(f"{gh_runs_url}/{run_id}/jobs", headers=gh_headers).json()
        durations = []
        for job in jobs['jobs']:
            name = job['name']
            started = datetime.fromisoformat(job['started_at'].replace("Z", "+00:00"))
            finished = datetime.fromisoformat(job['completed_at'].replace("Z", "+00:00"))
            durations.append(JobDuration(name, started, finished))
        plot_job_gantt(
            durations,
            title=f"Job durations for run {run_id}",
            file_path=experiments_folder / f"gantt_run{run_id}.png"
        )


if __name__ == "__main__":
    main()
