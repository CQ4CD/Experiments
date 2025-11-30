import re
from datetime import datetime

from experiments.commons import get_latest_experiment_number, get_experiment_folder, JobDuration, plot_job_gantt

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


def parse_logs_in_run(log_dir):
    jobs = []
    for txt_file in log_dir.glob("*.txt"):
        first_ts, last_ts = parse_file_timestamps(txt_file)
        if first_ts and last_ts:
            jobs.append(JobDuration(txt_file.stem, first_ts, last_ts))
    return jobs


def main():
    run_dirs = sorted(experiments_folder.glob("logs_*"))
    if not run_dirs:
        print(f"No log directories found in {experiments_folder}")
        return

    for run_i, log_dir in enumerate(run_dirs):
        if not log_dir.is_dir():
            continue
        print(f"Processing {log_dir} ...")
        steps = parse_logs_in_run(log_dir)
        if not steps:
            print(f"No valid step data found in {log_dir}")
            continue
        plot_job_gantt(
            steps,
            title=f"Step/job durations for run {run_i}",
            file_path=experiments_folder / f"gantt_run{run_i}.png"
        )


if __name__ == "__main__":
    main()
