import json
from datetime import datetime
from pathlib import Path

from experiments.commons import (JobDuration, plot_job_gantt)

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

            pipeline_id = pipeline['id']
            durations = []
            jobs = pipeline['jobs']
            stages = pipeline.get('stages', [])
            job_stage_map = {}
            for stage in stages:
                stage_name = stage.get('name')
                for job_id in stage.get('jobs', []):
                    job_stage_map[job_id] = stage_name

            for job in jobs:
                print('Getting job information for job', job['id'])
                started = datetime.fromisoformat(job.get('started_at').replace("Z", "+00:00"))
                finished = datetime.fromisoformat(job.get('finished_at').replace("Z", "+00:00"))
                runner = job.get('runner')
                stage_name = job_stage_map.get(job.get('id'))
                durations.append(
                    JobDuration(
                        job.get('id').replace(pipeline_id, ''),
                        started,
                        finished,
                        runner=runner,
                        stage=stage_name,
                    )
                )
                all_jobs.append(
                    JobDuration(
                        job.get('id').replace(pipeline_id, ''),
                        started,
                        finished,
                        runner=runner,
                        stage=stage_name,
                    )
                )
            #plot_job_gantt(durations,f"Step/job durations for run {run_id}", directory / f"gantt_run{run_id}", sort=False)
        if not all_jobs:
            continue
        plot_job_gantt(all_jobs,f"Step/job durations for all jobs", directory / f"gantt_run_all_jobs", sort=True)
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
