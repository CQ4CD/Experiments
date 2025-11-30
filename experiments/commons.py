import json
from pathlib import Path
import dotenv
import os


dotenv.load_dotenv()

owner = os.getenv('REPO_OWNER', 'CQ4CD')
repo = os.getenv('REPO', 'Experiments')
workflow_name = os.getenv('GH_WORKFLOW_NAME', 'unfair-test-workflow-limited')
workflow = os.getenv('WORKFLOW', f"{workflow_name}.yml")
gh_token = os.getenv("GH_TOKEN")
gh_url_runs = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
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
    return Path(__file__).parent / platform / workflow_name / f"experiment_{experiment_number}"


def get_latest_experiment_number(platform='github') -> int:
    return get_fresh_experiment_number(platform) - 1


def get_fresh_experiment_number(platform='github') -> int:
    result = 0
    while (Path(__file__).parent / platform / workflow_name / f"experiment_{result}").exists():
        result += 1
    return result
