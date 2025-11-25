import json
import os
import time
import requests
import dotenv
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

dotenv.load_dotenv()

gitlab_url = os.getenv("GITLAB_URL")
project_id = '9767'
token = os.getenv("GITLAB_TOKEN")
branch = 'main'
experiment_number = 1

api_trigger = f"{gitlab_url}/api/v4/projects/{project_id}/pipeline"
api_pipelines = f"{gitlab_url}/api/v4/projects/{project_id}/pipelines"

run_id_file = Path(__file__).parent / f"run_ids_{experiment_number}.json"

headers = {
    "PRIVATE-TOKEN": token
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
    response = requests.post(api_trigger, headers=headers, data={"ref": branch})
    print(response.json())
    print("Triggered run", run_number, response.status_code)
    return response.json()['id']


def wait(pipeline_id, run_number):
    while True:
        r = requests.get(f"{api_pipelines}/{pipeline_id}", headers=headers).json()
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
        add_run_id(run_id)
        start, end = wait(run_id, run_number)
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        durations.append((end_dt - start_dt).total_seconds())
    plt.plot(durations)
    plt.xlabel("Run")
    plt.ylabel("Duration (s)")
    plt.title("Pipeline Durations")
    workflow_durations = Path(__file__).parent / f"workflow_durations_{experiment_number}.png"
    plt.savefig(workflow_durations)


if __name__ == "__main__":
    experiment()
