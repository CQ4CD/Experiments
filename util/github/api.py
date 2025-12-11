import os
import requests
import dotenv
from datetime import datetime

from util.github.models import GitHubWorkflow, GitHubWorkflowRun, GitHubCommit 

dotenv.load_dotenv()

gh_token = os.getenv("GH_TOKEN")
if not gh_token:
    raise ValueError("GitHub token (GH_TOKEN) not found in environment variables.")

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {gh_token}",
    "X-GitHub-Api-Version": "2022-11-28"
}

def get_workflows(owner: str, repository: str) -> list[GitHubWorkflow]:
    """
    Calls all workflows of a GitHub repository.
    
    Args:
        owner: GitHub Owner (User or Organization)
        repository: The name of the repository
        
    Returns:
        A list of workflow dictionaries with all workflow information
    """
    url = f"https://api.github.com/repos/{owner}/{repository}/actions/workflows"

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    return [GitHubWorkflow.from_api_response(w) for w in data.get('workflows', [])]

def get_workflow_runs(owner: str, repository: str, workflow_id: int | str, 
                     as_dataclass: bool = True, fetch_all: bool = False, **params) -> list[GitHubWorkflowRun] | list[dict]:
    """
    Retrieves runs of a specific workflow.
    
    Args:
        owner: The GitHub owner (user or organization)
        repository: The name of the repository
        workflow_id: The ID or filename of the workflow (e.g., 123456 or "ci.yml")
        as_dataclass: If True, returns GitHubWorkflowRun objects, otherwise raw dicts
        fetch_all: If True, fetches all pages (can be slow for repos with many runs)
        **params: Optional query parameters such as:
            - per_page: Number of results per page (max 100, default 30)
            - page: Page number (ignored if fetch_all=True)
            - branch: Filters by branch
            - event: Filters by event type (e.g., "push", "pull_request")
            - status: Filters by status ("completed", "action_required", "cancelled", 
                     "failure", "neutral", "skipped", "stale", "success", "timed_out", 
                     "in_progress", "queued", "requested", "waiting", "pending")
            - created: Filters by creation date (ISO 8601 format)
            - actor: Filters by user who triggered the run
            - exclude_pull_requests: Boolean, excludes pull request runs
        
    Returns:
        A list of GitHubWorkflowRun objects or workflow run dictionaries
    """
    url = f"https://api.github.com/repos/{owner}/{repository}/actions/workflows/{workflow_id}/runs"
    
    if not fetch_all:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        runs = data.get('workflow_runs', [])
        
        if as_dataclass:
            return [GitHubWorkflowRun.from_api_response(run) for run in runs]
        return runs
    
    # Fetch all pages
    all_runs = []
    page = 1
    params['per_page'] = params.get('per_page', 100)  # Max per page
    
    while True:
        params['page'] = page
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        runs = data.get('workflow_runs', [])
        
        if not runs:
            break
        
        all_runs.extend(runs)
        page += 1
        
        # GitHub API returns total_count
        total_count = data.get('total_count', 0)
        if len(all_runs) >= total_count:
            break
    
    if as_dataclass:
        return [GitHubWorkflowRun.from_api_response(run) for run in all_runs]
    return all_runs


def get_commit(owner: str, repository: str, sha: str, as_dataclass: bool = True) -> GitHubCommit | dict:
    """
    Retrieves detailed information about a commit.
    
    Args:
        owner: The GitHub owner (user or organization)
        repository: The name of the repository
        sha: The SHA hash of the commit
        as_dataclass: If True, returns GitHubCommit object, otherwise raw dict
        
    Returns:
        A GitHubCommit object or dictionary with commit information
    """
    url = f"https://api.github.com/repos/{owner}/{repository}/commits/{sha}"
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    data = response.json()
    
    if as_dataclass:
        return GitHubCommit.from_api_response(data)
    return data


def get_rate_limit() -> dict:
    """
    Retrieves the current API rate limit status.
    
    Returns:
        A dictionary with rate limit information including:
        - core.limit: Maximum requests per hour
        - core.remaining: Remaining requests
        - core.reset: Unix timestamp when limit resets
        - core.used: Number of requests used
    """
    url = "https://api.github.com/rate_limit"
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json()