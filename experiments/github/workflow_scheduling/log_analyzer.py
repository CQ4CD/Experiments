import re
import os
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import dotenv

from experiments.github.workflow_scheduling.commons import get_latest_experiment_number

dotenv.load_dotenv()

workflow_name = os.getenv('GH_WORKFLOW_NAME', 'unfair-test-workflow-limited')
experiment_number = get_latest_experiment_number()

BASE_PATH = Path(__file__).parent / workflow_name / f"experiment_{experiment_number}"
ts_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)")


def parse_github_timestamp(ts_str):
    if ts_str.endswith('Z'):
        ts_str = ts_str[:-1]
    date_part, time_part = ts_str.split('T')
    if '.' in time_part:
        time_main, micro_part = time_part.split('.')
        micro_part = (micro_part + "000000")[:6]
        norm_time = f"{date_part}T{time_main}.{micro_part}"
        return datetime.strptime(norm_time, "%Y-%m-%dT%H:%M:%S.%f")
    else:
        norm_time = f"{date_part}T{time_part}"
        return datetime.strptime(norm_time, "%Y-%m-%dT%H:%M:%S")


def parse_file_timestamps(filepath):
    first_ts = None
    last_ts = None
    with open(filepath, encoding='utf-8') as f:
        for line in f:
            match = ts_pattern.match(line)
            if match:
                ts = parse_github_timestamp(match.group(1))
                if first_ts is None:
                    first_ts = ts
                last_ts = ts
    return first_ts, last_ts


def main():
    wait_idxs = []
    run_durations = []
    for run_i, log_dir in enumerate(sorted(BASE_PATH.glob("logs_*"))):
        if not log_dir.is_dir():
            continue
        file_ts_list = []
        all_first_ts = []
        all_last_ts = []
        for txt_file in log_dir.glob("*.txt"):
            first_ts, last_ts = parse_file_timestamps(txt_file)
            if first_ts:
                file_ts_list.append((txt_file.name, first_ts))
                all_first_ts.append(first_ts)
            if last_ts:
                all_last_ts.append(last_ts)
        if not file_ts_list or not all_first_ts or not all_last_ts:
            wait_idxs.append(None)
            run_durations.append(None)
            continue
        file_ts_list.sort(key=lambda t: t[1])
        file_names_sorted = [t[0] for t in file_ts_list]
        target_idx = None
        for i, fname in enumerate(file_names_sorted):
            if 'wait (120)' in fname:
                target_idx = i
                break
        print(file_names_sorted)
        print(target_idx)
        wait_idxs.append(target_idx)
        run_start = min(all_first_ts)
        run_end = max(all_last_ts)
        run_duration = (run_end - run_start).total_seconds()
        run_durations.append(run_duration)

    xs, idxs = zip(*[(i, idx) for i, idx in enumerate(wait_idxs) if idx is not None])
    _, durs = zip(*[(i, dur) for i, dur in enumerate(run_durations) if dur is not None])
    fig, ax1 = plt.subplots()
    color1 = 'tab:blue'
    ax1.set_xlabel("Run index")
    ax1.set_ylabel("Index of 'wait (120)' file", color=color1)
    ax1.plot(xs, idxs, 'o-', color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)
    ax2 = ax1.twinx()
    color2 = 'tab:orange'
    ax2.set_ylabel("Run duration (seconds)", color=color2)
    ax2.plot(xs, durs, 's--', color=color2)
    ax2.tick_params(axis='y', labelcolor=color2)
    plt.title("Location of 'wait (120)' and run duration per run")
    plt.grid(True)
    plt.tight_layout()
    workflow_durations = BASE_PATH / f"step-index-and-durations.png"
    plt.savefig(workflow_durations)
    plt.show()


if __name__ == "__main__":
    main()
