import json
import os
from datetime import datetime
from pathlib import Path

from experiments.commons import (get_latest_experiment_number, get_experiment_folder, JobDuration,
                                 plot_job_gantt)

def main():
    output_root = Path(__file__).parent
    output_root.mkdir(exist_ok=True)
    for directory in [ x for x in output_root.iterdir() if x.is_dir() ]:
        for file in directory.iterdir():
            print(file)
            if not (file.name.startswith('pipeline') and file.name.endswith('.json')):
                continue
            print()
            pipeline = json.load(open(file))
            run_id = pipeline['id']
            print('Creating Gantt chart for run', file)

            durations = []
            jobs = pipeline['jobs']

            for job in jobs:
                print('Getting job information for job', job['id'])
                started = datetime.fromisoformat(job.get('started_at').replace("Z", "+00:00"))
                finished = datetime.fromisoformat(job.get('finished_at').replace("Z", "+00:00"))
                durations.append(JobDuration(job.get('name'), started, finished))
            plot_job_gantt(durations,f"Step/job durations for run {run_id}", directory / f"gantt_run{run_id}")


if __name__ == "__main__":
    main()
