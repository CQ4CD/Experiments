import os
import json
from pathlib import Path
import requests
import matplotlib.pyplot as plt
from datetime import datetime
import dotenv

dotenv.load_dotenv()

gitlab_url = os.getenv("GITLAB_URL")
project_id = "9767"
token = os.getenv("GITLAB_TOKEN")
experiment_number = 0

headers = {"PRIVATE-TOKEN": token}

run_id_file = Path(__file__).parent / f"run_ids_{experiment_number}.json"
run_ids = json.loads(run_id_file.read_text())

def main():
    output_root = Path(__file__).parent / f"experiment_{experiment_number}"
    output_root.mkdir(exist_ok=True)

    indices_120 = []
    durations = []

    for run_id in run_ids:
        jobs_url = f"{gitlab_url}/api/v4/projects/{project_id}/pipelines/{run_id}/jobs"
        jobs = requests.get(jobs_url, headers=headers).json()

        run_folder = output_root / str(run_id)
        run_folder.mkdir(exist_ok=True)

        enriched = []
        for job in jobs:
            job_id = job["id"]
            detail = requests.get(f"{gitlab_url}/api/v4/projects/{project_id}/jobs/{job_id}", headers=headers).json()
            started = detail.get("started_at")
            created = detail.get("created_at")
            finished = detail.get("finished_at")
            enriched.append({
                "id": job_id,
                "name": detail.get("name"),
                "created_at": created,
                "started_at": started,
                "finished_at": finished
            })

        sorted_jobs = sorted(
            enriched,
            key=lambda x: datetime.fromisoformat(x["started_at"].replace("Z", "+00:00")) if x["started_at"] else datetime.max
        )

        for wait_job in sorted_jobs:
            print(wait_job)

        idx_120 = None
        for i, j in enumerate(sorted_jobs):
            if j["name"] == "wait-jobs: [120]":
                idx_120 = i
                break
        indices_120.append(idx_120)

        pipe_detail = requests.get(f"{gitlab_url}/api/v4/projects/{project_id}/pipelines/{run_id}", headers=headers).json()
        durations.append(pipe_detail.get("duration"))


    xs, idxs = zip(*[(i, idx) for i, idx in enumerate(indices_120) if idx is not None])
    _, durs = zip(*[(i, dur) for i, dur in enumerate(durations) if dur is not None])

    fig, ax1 = plt.subplots()

    color1 = 'tab:blue'
    ax1.set_xlabel("Run index")
    ax1.set_ylabel("Index of 'wait (120)' job", color=color1)
    ax1.plot(xs, idxs, 'o-', color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)

    ax2 = ax1.twinx()
    color2 = 'tab:orange'
    ax2.set_ylabel("Run duration (seconds)", color=color2)
    ax2.plot(xs, durs, 's--', color=color2)
    ax2.tick_params(axis='y', labelcolor=color2)

    plt.title("Index of 'wait (120)' job vs pipeline duration")
    plt.grid(True)
    plt.tight_layout()

    plot_path = output_root / "step-index-and-durations.png"
    plt.savefig(plot_path)
    plt.show()


if __name__ == '__main__':
    main()
