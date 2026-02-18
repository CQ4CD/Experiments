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
    def __init__(
        self,
        label: str,
        start: datetime,
        end: datetime,
        runner: str | None = None,
        stage: str | None = None,
    ):
        self.label = label
        self.start = start
        self.end = end
        self.duration = end - start
        self.runner = runner
        self.stage = stage


def plot_job_gantt(jobs, title, file_path=None, sort=True, limit=False):
    if not jobs:
        return

    # Sort jobs (latest start first)
    if sort:
        steps_sorted = sorted(jobs, reverse=True, key=lambda x: x.start)
    else:
        steps_sorted = jobs.copy()
        steps_sorted.reverse()

    step_names = [s.label for s in steps_sorted]
    start_times = [s.start for s in steps_sorted]
    end_times = [s.end for s in steps_sorted]

    # Normalize start times so axis begins at 0
    t0 = min(start_times)
    start_offsets = [(s - t0).total_seconds() for s in start_times]
    durations = [(e - s).total_seconds() for s, e in zip(start_times, end_times)]

    fig, ax = plt.subplots(figsize=(10, max(4, len(steps_sorted))))
    yticks = list(range(len(steps_sorted)))

    # Convert seconds → days for matplotlib
    start_offsets_days = [so / 86400 for so in start_offsets]
    durations_days = [d / 86400 for d in durations]

    colors = None
    legend_handles = None
    runner_names = [s.runner for s in steps_sorted if getattr(s, "runner", None)]
    if runner_names:
        unique_runners = list(dict.fromkeys(runner_names))
        cmap = plt.get_cmap('tab20')
        runner_colors = {runner: cmap(i % cmap.N) for i, runner in enumerate(unique_runners)}
        colors = [runner_colors.get(s.runner, 'tab:blue') for s in steps_sorted]
        legend_handles = [
            matplotlib.patches.Patch(color=runner_colors[runner], label=runner)
            for runner in unique_runners
        ]

    stage_handles = None
    stage_names = [s.stage for s in steps_sorted if getattr(s, "stage", None)]
    stage_colors = {}
    if stage_names:
        unique_stages = list(dict.fromkeys(stage_names))
        stage_cmap = plt.get_cmap('Pastel1')
        stage_colors = {stage: stage_cmap(i % stage_cmap.N) for i, stage in enumerate(unique_stages)}
        stage_handles = [
            matplotlib.patches.Patch(color=stage_colors[stage], label=stage, alpha=0.4)
            for stage in unique_stages
        ]

        stage_indices = {stage: [] for stage in unique_stages}
        stage_time_ranges = {stage: [] for stage in unique_stages}
        for index, step in enumerate(steps_sorted):
            if step.stage in stage_indices:
                stage_indices[step.stage].append(index)
                start_offset = start_offsets_days[index]
                end_offset = start_offsets_days[index] + durations_days[index]
                stage_time_ranges[step.stage].append((start_offset, end_offset))

        for stage, indices in stage_indices.items():
            if not indices:
                continue
            stage_times = stage_time_ranges.get(stage, [])
            if not stage_times:
                continue
            stage_start = min(start for start, _ in stage_times)
            stage_end = max(end for _, end in stage_times)
            stage_span = max(stage_end - stage_start, 1 / 86400)
            margin_days = max(stage_span * 0.01, 1 / 86400)
            stage_left = max(stage_start - margin_days, 0)
            stage_width = (stage_end - stage_start) + (2 * margin_days)

            sorted_indices = sorted(indices)
            runs = []
            run_start = sorted_indices[0]
            run_end = sorted_indices[0]
            for idx in sorted_indices[1:]:
                if idx == run_end + 1:
                    run_end = idx
                else:
                    runs.append((run_start, run_end))
                    run_start = idx
                    run_end = idx
            runs.append((run_start, run_end))

            for run_start, run_end in runs:
                run_length = run_end - run_start + 1
                run_center = (run_start + run_end) / 2
                ax.barh(
                    run_center,
                    stage_width,
                    left=stage_left,
                    height=run_length,
                    align='center',
                    color=stage_colors.get(stage, '#dddddd'),
                    alpha=0.25,
                    zorder=0,
                )

    # Draw bars
    ax.barh(
        yticks,
        durations_days,
        left=start_offsets_days,
        height=0.8,
        align='center',
        color=colors,
        zorder=2,
    )

    ax.set_yticks(yticks)
    ax.set_yticklabels(step_names)
    ax.set_xlabel("Time (HH:MM:SS)")
    ax.set_ylabel("Step/Job")
    ax.set_title(title)

    if limit:
        # Fixed axis: 100 seconds (1:40)
        total_span_seconds = 100
        total_span_days = total_span_seconds / 86400
        # Apply axis limits
        ax.set_xlim(0, total_span_days)

        # Tick every 15 seconds
        tick_interval_seconds = 15
        tick_interval_days = tick_interval_seconds / 86400


        # Generate ticks
        ticks = []
        t = 0
        while t <= total_span_days + 1e-9:
            ticks.append(t)
            t += tick_interval_days
        ax.set_xticks(ticks)

    # Formatter for HH:MM:SS
    def format_seconds(x, pos):
        seconds = int(x * 86400)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02}:{m:02}:{s:02}"

    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(format_seconds))

    ax.grid(axis="x")

    legend_rows = 0
    legend_y = 0.02
    if stage_handles:
        stage_columns = min(len(stage_handles), 3)
        stage_rows = (len(stage_handles) + stage_columns - 1) // stage_columns
        fig.legend(
            handles=stage_handles,
            title="Stage",
            loc="lower center",
            bbox_to_anchor=(0.5, legend_y),
            ncol=stage_columns,
            frameon=False
        )
        legend_rows += stage_rows
        legend_y += 0.06 * stage_rows

    if legend_handles:
        legend_columns = min(len(legend_handles), 3)
        runner_rows = (len(legend_handles) + legend_columns - 1) // legend_columns
        fig.legend(
            handles=legend_handles,
            title="Runner",
            loc="lower center",
            bbox_to_anchor=(0.5, legend_y),
            ncol=legend_columns,
            frameon=False
        )
        legend_rows += runner_rows

    legend_padding = 0.12 + (0.06 * legend_rows)
    plt.tight_layout(rect=(0, legend_padding, 1, 1))
    if file_path:
        plt.savefig(file_path, bbox_inches="tight", pad_inches=0.4)
    plt.close(fig)
    plt.close("all")
