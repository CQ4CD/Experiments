print('Loading run_workflows', flush=True)

import time

import matplotlib.pyplot as plt
import requests

from experiments.commons import (get_fresh_experiment_number, owner, repo, workflow,
                                 gh_headers, get_run_id_file, add_run_id, get_experiment_folder)

experiment_number = get_fresh_experiment_number()
url_dispatch = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches"
url_runs = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
run_id_file = get_run_id_file(experiment_number)


def trigger(run_number):
    print("Triggering run")
    response = requests.post(url_dispatch, headers=gh_headers, json={"ref": "main"})
    print(response)
    print('Triggered run', run_number, response.status_code)
    if not response.ok:
        raise Exception(f"Failed to trigger run! {response.status_code} {response.reason}")


def get_latest_run(run_number):
    """
    Because of GitHub API design, the POST dispatch does of course not return the run id...
    We instead need to poll the API to get the latest run.
    """
    print(run_number, "Getting latest run")
    data = requests.get(url_runs, headers=gh_headers).json()
    for run in data.get("workflow_runs", []):
        print(run['name'])
        if run.get("name") == workflow:
            print(run_number, "Found latest run", run.get("id"))
            return run
    print(run_number, "Failed to find latest run")
    return None


def wait(run_id, run_number):
    while True:
        run = requests.get(f"{url_runs}/{run_id}", headers=gh_headers).json()
        print("Getting run status!")
        print(run_number, run['name'], run['id'], run['status'])
        if run.get("status") == "completed":
            return run.get("run_started_at"), run.get("updated_at")
        time.sleep(10)


def experiment():
    durations = []
    for run_number in range(15):
        trigger(run_number)
        time.sleep(3)
        latest = None
        while latest is None:
            latest = get_latest_run(run_number)
            time.sleep(10)
        add_run_id(run_id_file, latest['id'])
        start, end = wait(latest.get("id"), run_number)
        # TODO: This seems inaccurate! Poll webpage to get actual durations?
        t1 = time.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
        t2 = time.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
        durations.append(time.mktime(t2) - time.mktime(t1))


    plt.plot(durations)
    plt.xlabel("Run")
    plt.ylabel("Duration (s)")
    plt.title("Workflow Durations")
    workflow_durations = get_experiment_folder(experiment_number) / f"workflow_durations.png"
    plt.savefig(workflow_durations)


if __name__ == '__main__':
    print('Starting Experiment', flush=True)
    experiment()
