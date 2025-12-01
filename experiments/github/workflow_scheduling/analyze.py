import json
import time

import matplotlib.pyplot as plt
import requests

from experiments.commons import (get_latest_experiment_number, gh_runs_url, gh_headers,
                                 get_run_id_file, get_experiment_folder)

experiment_number = get_latest_experiment_number()
run_id_file = get_run_id_file(experiment_number)
experiments_folder = get_experiment_folder(experiment_number)


def get_run_duration(run_id):
    run = requests.get(f"{gh_runs_url}/{run_id}", headers=gh_headers).json()
    print(run['name'], run['id'], run['status'])
    with open(experiments_folder / f"{run_id}.json", "w") as f:
        json.dump(run, f, indent='\t')
    if run.get("status") == "completed":
        return run.get("run_started_at"), run.get("updated_at")
    else:
        raise Exception(f"Run not completed {run}")


def analyze():
    durations = []
    run_ids = json.loads(run_id_file.read_text())
    for run_id in run_ids:
        start, end = get_run_duration(run_id)
        t1 = time.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
        t2 = time.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
        durations.append(time.mktime(t2) - time.mktime(t1))
        time.sleep(0.5)

    plt.plot(durations)
    plt.xlabel("Run")
    plt.ylabel("Duration (s)")
    plt.title("Workflow Durations")
    workflow_durations = get_experiment_folder(experiment_number) / f"workflow_durations.png"
    plt.savefig(workflow_durations)


if __name__ == '__main__':
    analyze()
