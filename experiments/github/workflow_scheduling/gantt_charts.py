import re
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from experiments.commons import get_latest_experiment_number, workflow_name, get_experiment_folder

experiment_number = get_latest_experiment_number()
experiments_folder = get_experiment_folder(experiment_number)
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

def parse_steps_in_run(log_dir):
    steps = []
    for txt_file in log_dir.glob("*.txt"):
        first_ts, last_ts = parse_file_timestamps(txt_file)
        if first_ts and last_ts:
            steps.append({
                'step': txt_file.stem,
                'start': first_ts,
                'end': last_ts,
            })
    return steps

def plot_step_durations_gantt(steps, title, savepath):
    if not steps:
        return

    steps_sorted = sorted(steps, key=lambda x: x['start'])
    step_names = [step['step'] for step in steps_sorted]
    start_times = [step['start'] for step in steps_sorted]
    end_times = [step['end'] for step in steps_sorted]
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
    plt.savefig(savepath)
    plt.close(fig)
    plt.close('all')

def main():
    run_dirs = sorted(experiments_folder.glob("logs_*"))
    if not run_dirs:
        print(f"No log directories found in {experiments_folder}")
        return

    for run_i, log_dir in enumerate(run_dirs):
        if not log_dir.is_dir():
            continue
        print(f"Processing {log_dir} ...")
        steps = parse_steps_in_run(log_dir)
        if not steps:
            print(f"No valid step data found in {log_dir}")
            continue
        plot_step_durations_gantt(
            steps,
            title=f"Step/job durations for run {run_i}",
            savepath=experiments_folder / f"gantt_run{run_i}.png"
        )

if __name__ == "__main__":
    main()
