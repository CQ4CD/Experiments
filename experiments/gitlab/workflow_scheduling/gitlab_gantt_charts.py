import json
from datetime import datetime

import requests

from experiments.commons import (get_latest_experiment_number, get_run_id_file,
                                 gitlab_url, gitlab_headers, gitlab_project_id, get_experiment_folder, JobDuration,
                                 plot_job_gantt)

experiment_number = get_latest_experiment_number('gitlab')
experiments_folder = get_experiment_folder(experiment_number, 'gitlab')
run_id_file = get_run_id_file(experiment_number, 'gitlab')
run_ids = json.loads(run_id_file.read_text())


def main():
    output_root = get_experiment_folder(experiment_number, 'gitlab')
    output_root.mkdir(exist_ok=True)

    for run_id in run_ids:
        print()
        print('Creating Gantt chart for run', run_id)
        durations = []
        jobs_url = f"{gitlab_url}/api/v4/projects/{gitlab_project_id}/pipelines/{run_id}/jobs"
        response = requests.get(jobs_url, headers=gitlab_headers)
        if not response.ok:
            raise Exception(response.reason)
        jobs = response.json()
        (experiments_folder / f"run{run_id}.json").write_text(json.dumps(jobs, indent='\t'))
        for job in jobs:
            print('Getting job information for job', job['id'])
            job_id = job['id']
            detail_response = requests.get(f"{gitlab_url}/api/v4/projects/{gitlab_project_id}/jobs/{job_id}", headers=gitlab_headers)
            (experiments_folder / f"run{run_id}-{job_id}.json").write_text(json.dumps(jobs, indent='\t'))
            detail = detail_response.json()
            started = datetime.fromisoformat(detail.get('started_at').replace("Z", "+00:00"))
            finished = datetime.fromisoformat(detail.get('finished_at').replace("Z", "+00:00"))
            durations.append(JobDuration(detail.get('name'), started, finished))
        plot_job_gantt(durations,f"Step/job durations for run {run_id}", experiments_folder / f"gantt_run{run_id}")


if __name__ == "__main__":
    main()
