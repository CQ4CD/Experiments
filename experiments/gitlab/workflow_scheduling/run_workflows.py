import time
from datetime import datetime

import matplotlib.pyplot as plt
import requests

from experiments.commons import (get_fresh_experiment_number, gitlab_url, gitlab_project_id, get_run_id_file,
                                 gitlab_headers, gitlab_branch, add_run_id, get_experiment_folder)

experiment_number = get_fresh_experiment_number('gitlab')
api_trigger = f"{gitlab_url}/api/v4/projects/{gitlab_project_id}/pipeline"
api_pipelines = f"{gitlab_url}/api/v4/projects/{gitlab_project_id}/pipelines"
run_id_file = get_run_id_file(experiment_number, 'gitlab')


def trigger(run_number):
    response = requests.post(api_trigger, headers=gitlab_headers, data={"ref": gitlab_branch})
    print(response.json())
    print("Triggered run", run_number, response.status_code)
    return response.json()['id']


def wait(pipeline_id, run_number):
    while True:
        r = requests.get(f"{api_pipelines}/{pipeline_id}", headers=gitlab_headers).json()
        status = r.get("status")
        print("Getting pipeline status!", run_number, pipeline_id, status)
        if status in ["success", "failed", "canceled", "skipped"]:
            print(r)
            return r.get("created_at"), r.get("updated_at")
        time.sleep(10)


def experiment():
    durations = []
    for run_number in range(10):
        run_id = trigger(run_number)
        time.sleep(3)
        add_run_id(run_id_file, run_id)
        start, end = wait(run_id, run_number)
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        durations.append((end_dt - start_dt).total_seconds())
    plt.plot(durations)
    plt.xlabel("Run")
    plt.ylabel("Duration (s)")
    plt.title("Pipeline Durations")
    workflow_durations = get_experiment_folder(experiment_number, 'gitlab') / f"workflow_durations.png"
    plt.savefig(workflow_durations)


if __name__ == "__main__":
    experiment()
