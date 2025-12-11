from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class GitHubWorkflow:
    """Represents a GitHub workflow."""
    
    id: int
    node_id: str
    name: str
    path: str
    state: str
    created_at: str
    updated_at: str
    url: str
    html_url: str
    badge_url: str
    
    @classmethod
    def from_api_response(cls, data: dict) -> 'GitHubWorkflow':
        """Creates a GitHubWorkflow object from the API response."""
        return cls(
            id=data['id'],
            node_id=data['node_id'],
            name=data['name'],
            path=data['path'],
            state=data['state'],
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            url=data['url'],
            html_url=data['html_url'],
            badge_url=data['badge_url']
        )


@dataclass
class GitHubCommitFile:
    """Represents a file changed in a commit."""
    
    filename: str
    status: str  # "added", "removed", "modified", "renamed"
    additions: int
    deletions: int
    changes: int
    patch: Optional[str] = None
    previous_filename: Optional[str] = None  # For renamed files
    
    @classmethod
    def from_api_response(cls, data: dict) -> 'GitHubCommitFile':
        """Creates a GitHubCommitFile object from the API response."""
        return cls(
            filename=data['filename'],
            status=data['status'],
            additions=data['additions'],
            deletions=data['deletions'],
            changes=data['changes'],
            patch=data.get('patch'),
            previous_filename=data.get('previous_filename')
        )


@dataclass
class GitHubCommit:
    """Represents a GitHub commit with relevant fields."""
    
    sha: str
    message: str
    author_name: str
    author_email: str
    author_date: str
    committer_name: str
    committer_email: str
    committer_date: str
    html_url: str
    
    # Stats
    total_additions: int
    total_deletions: int
    total_changes: int
    
    # Files changed
    files: list[GitHubCommitFile]
    
    @classmethod
    def from_api_response(cls, data: dict) -> 'GitHubCommit':
        """Creates a GitHubCommit object from the API response."""
        commit_data = data['commit']
        stats = data.get('stats', {})
        files_data = data.get('files', [])
        
        return cls(
            sha=data['sha'],
            message=commit_data['message'],
            author_name=commit_data['author']['name'],
            author_email=commit_data['author']['email'],
            author_date=commit_data['author']['date'],
            committer_name=commit_data['committer']['name'],
            committer_email=commit_data['committer']['email'],
            committer_date=commit_data['committer']['date'],
            html_url=data['html_url'],
            total_additions=stats.get('additions', 0),
            total_deletions=stats.get('deletions', 0),
            total_changes=stats.get('total', 0),
            files=[GitHubCommitFile.from_api_response(f) for f in files_data]
        )
    
    @property
    def short_sha(self) -> str:
        """Returns the first 7 characters of the commit SHA."""
        return self.sha[:7] if self.sha else ''
    
    @property
    def file_count(self) -> int:
        """Returns the number of files changed."""
        return len(self.files)
    
    @property
    def short_message(self) -> str:
        """Returns the first line of the commit message."""
        return self.message.split('\n')[0] if self.message else ''


@dataclass
class GitHubWorkflowRun:
    """Represents a GitHub workflow run with relevant fields."""
    
    id: int
    run_number: int
    name: str
    status: str  # "completed", "in_progress", "queued", etc.
    conclusion: Optional[str]  # "success", "failure", "cancelled", "skipped", etc.
    workflow_id: int
    workflow_name: str
    event: str  # "push", "pull_request", "schedule", etc.
    created_at: str
    updated_at: str
    run_started_at: Optional[str]
    head_branch: str
    head_sha: str
    run_attempt: int
    html_url: str
    
    # Additional computed fields
    duration_seconds: Optional[float] = None
    
    @classmethod
    def from_api_response(cls, data: dict) -> 'GitHubWorkflowRun':
        """Creates a GitHubWorkflowRun object from the API response."""
        run = cls(
            id=data['id'],
            run_number=data['run_number'],
            name=data.get('name', ''),
            status=data['status'],
            conclusion=data.get('conclusion'),
            workflow_id=data['workflow_id'],
            workflow_name=data.get('name', ''),
            event=data['event'],
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            run_started_at=data.get('run_started_at'),
            head_branch=data.get('head_branch', ''),
            head_sha=data.get('head_sha', ''),
            run_attempt=data.get('run_attempt', 1),
            html_url=data['html_url']
        )
        
        # Calculate duration if completed
        if run.status == 'completed' and run.run_started_at:
            started = datetime.fromisoformat(run.run_started_at.replace('Z', '+00:00'))
            updated = datetime.fromisoformat(run.updated_at.replace('Z', '+00:00'))
            run.duration_seconds = (updated - started).total_seconds()
        
        return run
    
    @property
    def short_sha(self) -> str:
        """Returns the first 7 characters of the commit SHA."""
        return self.head_sha[:7] if self.head_sha else ''
    
    @property
    def is_successful(self) -> bool:
        """Checks if the run was successful."""
        return self.status == 'completed' and self.conclusion == 'success'
