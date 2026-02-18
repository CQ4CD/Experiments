import json
from datetime import datetime
from pathlib import Path

from fontTools.feaLib.lexer import NonIncludingLexer

from experiments.commons import (get_latest_experiment_number, get_experiment_folder, JobDuration,
                                 plot_job_gantt)

def main():
    project_root = Path(__file__).parent.parent.parent.parent
    #output_root = project_root.parent / 'ci-simulation' / 'out'
    output_root = Path(__file__).parent
    print(output_root)
    print()
    output_root.mkdir(exist_ok=True)
    total_durations = {}
    for directory in [ x for x in output_root.iterdir() if x.is_dir() ]:
        all_jobs = []
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
                all_jobs.append(JobDuration(job.get('name'), started, finished))
            #plot_job_gantt(durations,f"Step/job durations for run {run_id}", directory / f"gantt_run{run_id}", sort=False)
        if not all_jobs:
            continue
        plot_job_gantt(all_jobs,f"Step/job durations for all jobs", directory / f"gantt_run_all_jobs", sort=False)
        jobs_sorted = sorted(all_jobs, reverse=False, key=lambda x: x.start)
        first = jobs_sorted[0]
        jobs_sorted = sorted(all_jobs, reverse=True, key=lambda x: x.end)
        last = jobs_sorted[0]
        duration = last.end - first.start
        total_durations[directory.name] = duration

    total_durations = dict(sorted(total_durations.items()))
    print("---------------------------------")
    print()
    for key, value in total_durations.items():
        print(key, value)


if __name__ == "__main__":
    main()
