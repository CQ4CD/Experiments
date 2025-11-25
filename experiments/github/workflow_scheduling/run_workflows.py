import json
import os
import time
import requests
import dotenv
import matplotlib.pyplot as plt

from pathlib import Path

dotenv.load_dotenv()

owner = 'CQ4CD'
repo = 'Experiments'
workflow_name = 'unfair-test-workflow'
workflow = f"{workflow_name}.yml"
token = os.getenv("GH_TOKEN")
experiment_number = 0

url_dispatch = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches"
url_runs = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"

run_id_file = Path(__file__).parent / workflow_name / f"run_ids_{experiment_number}.json"

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}",
    "X-GitHub-Api-Version": "2022-11-28"
}


def add_run_id(run_id):
    if run_id_file.exists():
        run_ids = json.loads(run_id_file.read_text())
    else:
        run_id_file.parent.mkdir(parents=True, exist_ok=True)
        run_ids = []
    run_ids.append(run_id)
    run_id_file.write_text(json.dumps(run_ids, indent='\t'))


def trigger(run_number):
    print("Triggering run")
    response = requests.post(url_dispatch, headers=headers, json={"ref": "main"})
    print(response)
    print('Triggered run', run_number, response.status_code)


def get_latest_run(run_number):
    """
    Because of GitHub API design, the POST dispatch does of course not return the run id...
    We instead need to poll the API to get the latest run.
    """
    print(run_number, "Getting latest run")
    data = requests.get(url_runs, headers=headers).json()
    for run in data.get("workflow_runs", []):
        print(run['name'])
        if run.get("name") == workflow:
            print(run_number, "Found latest run", run.get("id"))
            return run
    print(run_number, "Failed to find latest run")
    return None


def wait(run_id, run_number):
    while True:
        run = requests.get(f"{url_runs}/{run_id}", headers=headers).json()
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
        add_run_id(latest['id'])
        start, end = wait(latest.get("id"), run_number)
        # TODO: This seems inaccurate! Poll webpage to get actual durations?
        t1 = time.strptime(start, "%Y-%m-%dT%H:%M:%SZ")
        t2 = time.strptime(end, "%Y-%m-%dT%H:%M:%SZ")
        durations.append(time.mktime(t2) - time.mktime(t1))


    plt.plot(durations)
    plt.xlabel("Run")
    plt.ylabel("Duration (s)")
    plt.title("Workflow Durations")
    plt.savefig("workflow_durations.png")


if __name__ == '__main__':
    experiment()
