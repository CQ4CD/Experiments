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
workflow_name = 'unfair-test-workflow-limited'
workflow = f"{workflow_name}.yml"
token = os.getenv("GH_TOKEN")
experiment_number = 0

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


def get_run_duration(run_id):
    run = requests.get(f"{url_runs}/{run_id}", headers=headers).json()
    print(run['name'], run['id'], run['status'])
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
    workflow_durations = Path(__file__).parent / workflow_name / f"workflow_durations_{experiment_number}.png"
    plt.savefig(workflow_durations)


if __name__ == '__main__':
    analyze()
