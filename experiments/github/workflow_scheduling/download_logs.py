import json
import os
import time
import requests
import zipfile
import dotenv

from pathlib import Path

dotenv.load_dotenv()

owner = 'CQ4CD'
repo = 'Experiments'
workflow_name = 'unfair-test-workflow-limited'
workflow = f"{workflow_name}.yml"
token = os.getenv("GH_TOKEN")
experiment_number = 0

run_id_file = Path(__file__).parent / workflow_name / f"run_ids_{experiment_number}.json"

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {token}",
    "X-GitHub-Api-Version": "2022-11-28"
}

def download_and_unpack_logs():
    run_ids = json.loads(run_id_file.read_text())

    for run_id in run_ids:
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/logs"
        response = requests.get(url, headers=headers, allow_redirects=False)

        if response.status_code == 302:
            out_dir = Path(__file__).parent / workflow_name / f"experiment_{experiment_number}" / f"logs_{run_id}"
            out_dir.mkdir(parents=True, exist_ok=True)
            zip_path = out_dir / "logs.zip"

            download_url = response.headers.get('Location')
            print(f"Downloading logs for run {run_id}...")
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                with open(zip_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            print(f"Saved zip to {zip_path}")

            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(out_dir)
                print(f"Unpacked logs to {out_dir}")
            except zipfile.BadZipFile:
                print(f"Failed to unpack {zip_path} (bad zip file)")

            zip_path.unlink()
        else:
            print(f"Failed to get logs for run {run_id}: status {response.status_code} ({response.text})")
        time.sleep(1)

if __name__ == '__main__':
    download_and_unpack_logs()
