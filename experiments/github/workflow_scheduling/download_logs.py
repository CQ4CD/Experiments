import json
import time
import zipfile

import requests

from experiments.commons import (get_latest_experiment_number, owner, repo, gh_headers,
                                 get_run_id_file, get_experiment_folder)

experiment_number = get_latest_experiment_number()
run_id_file = get_run_id_file(experiment_number)


def download_and_unpack_logs():
    run_ids = json.loads(run_id_file.read_text())

    for run_id in run_ids:
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/logs"
        response = requests.get(url, headers=gh_headers, allow_redirects=False)

        if response.status_code == 302:
            out_dir = get_experiment_folder(experiment_number) / f"logs_{run_id}"
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
