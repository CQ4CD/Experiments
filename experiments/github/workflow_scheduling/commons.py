from pathlib import Path
import dotenv
import os


def get_latest_experiment_number():
    return get_fresh_experiment_number() - 1


def get_fresh_experiment_number():
    dotenv.load_dotenv()
    workflow_name = os.getenv('GH_WORKFLOW_NAME', 'unfair-test-workflow-limited')
    result = 0
    while (Path(__file__).parent / workflow_name / f"run_ids_{result}.json").exists():
        result += 1
    return result
