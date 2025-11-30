import json
import os
from datetime import datetime
from pathlib import Path

import dotenv
import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
from matplotlib import pyplot as plt

dotenv.load_dotenv()

owner = os.getenv('REPO_OWNER', 'CQ4CD')
repo = os.getenv('REPO', 'Experiments')
workflow_name = os.getenv('GH_WORKFLOW_NAME', 'unfair-test-workflow-limited')
workflow = os.getenv('WORKFLOW', f"{workflow_name}.yml")
gh_token = os.getenv("GH_TOKEN")
gh_actions_url = f"https://api.github.com/repos/{owner}/{repo}/actions"
gh_runs_url = f"{gh_actions_url}/runs"
gh_headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {gh_token}",
    "X-GitHub-Api-Version": "2022-11-28"
}


gitlab_url = os.getenv('GITLAB_URL')
gitlab_project_id = os.getenv('GITLAB_PROJECT_ID', '9767')
gitlab_token = os.getenv('GITLAB_TOKEN')
gitlab_branch = os.getenv('GITLAB_BRANCH', 'main')
gitlab_headers = {'PRIVATE-TOKEN': gitlab_token}


def add_run_id(run_id_file: Path, run_id):
    if run_id_file.exists():
        run_ids = json.loads(run_id_file.read_text())
    else:
        run_id_file.parent.mkdir(parents=True, exist_ok=True)
        run_ids = []
    run_ids.append(run_id)
    run_id_file.write_text(json.dumps(run_ids, indent='\t'))


def get_run_id_file(experiment_number: int, platform='github') -> Path:
    return get_experiment_folder(experiment_number, platform) / 'run_ids.json'


def get_experiment_folder(experiment_number: int, platform='github') -> Path:
    return Path(__file__).parent / platform / 'workflow_scheduling' / workflow_name / f"experiment_{experiment_number}"


def get_latest_experiment_number(platform='github') -> int:
    return get_fresh_experiment_number(platform) - 1


def get_fresh_experiment_number(platform='github') -> int:
    result = 0
    while (Path(__file__).parent / platform / 'workflow_scheduling' / workflow_name / f"experiment_{result}").exists():
        result += 1
    return result


class JobDuration:
    def __init__(self, label: str, start: datetime, end: datetime):
        self.label = label
        self.start = start
        self.end = end
        self.duration = end - start


def plot_job_gantt(jobs: list[JobDuration], title: str, file_path: object | None = None):
    if not jobs:
        return

    steps_sorted = sorted(jobs, reverse=True, key=lambda x: x.start)
    step_names = [step.label for step in steps_sorted]
    start_times = [step.start for step in steps_sorted]
    end_times = [step.end for step in steps_sorted]
    durations_days = [(et - st).total_seconds() / 86400 for st, et in zip(start_times, end_times)]

    fig, ax = plt.subplots(figsize=(10, max(4, len(steps_sorted))))
    yticks = list(range(len(steps_sorted)))

    ax.barh(
        yticks,
        durations_days,
        left=mdates.date2num(start_times),
        height=0.8,
        align='center'
    )

    ax.set_yticks(yticks)
    ax.set_yticklabels(step_names)
    ax.set_xlabel('Time (HH:MM:SS)')
    ax.set_ylabel('Step/Job')
    ax.set_title(title)
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    ax.grid(axis='x')

    plt.tight_layout()
    if file_path:
        plt.savefig(file_path)
    plt.close(fig)
    plt.close('all')

