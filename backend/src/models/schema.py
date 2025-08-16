from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class NodeType(str, Enum):
    CODEBASE = "Codebase"
    COMMIT = "Commit"
    DEVELOPER = "Developer"
    BRANCH = "Branch"
    BUSINESS_MILESTONE = "BusinessMilestone"
    FILE = "File"


class Codebase(BaseModel):
    id: str
    git_url: HttpUrl
    name: str
    description: Optional[str] = None
    created_at: datetime
    last_analyzed: Optional[datetime] = None
    total_commits: int = 0
    total_developers: int = 0
    primary_language: Optional[str] = None


class Developer(BaseModel):
    id: str
    name: str
    email: str
    total_commits: int = 0
    expertise_areas: List[str] = []
    contribution_score: float = 0.0
    first_commit_date: Optional[datetime] = None
    last_commit_date: Optional[datetime] = None
    lines_added: int = 0
    lines_removed: int = 0


class Branch(BaseModel):
    id: str
    name: str
    codebase_id: str
    created_at: datetime
    last_commit_sha: Optional[str] = None
    is_main_branch: bool = False
    total_commits: int = 0


class CommitHistory(BaseModel):
    id: str
    sha: str
    message: str
    author_name: str
    author_email: str
    committer_name: str
    committer_email: str
    timestamp: datetime
    branch: str
    files_changed: List[str] = []
    insertions: int = 0
    deletions: int = 0
    parent_shas: List[str] = []
    feature_summary: Optional[str] = None  # LLM generated
    business_impact: Optional[str] = None  # LLM generated
    complexity_score: float = 0.0


class BusinessMilestone(BaseModel):
    id: str
    name: str
    description: str
    date: datetime
    codebase_id: str
    related_commits: List[str] = []
    milestone_type: str  # e.g., "release", "feature", "bugfix"
    version: Optional[str] = None


class FileChange(BaseModel):
    id: str
    commit_sha: str
    file_path: str
    change_type: str  # "added", "modified", "deleted", "renamed"
    lines_added: int = 0
    lines_removed: int = 0
    complexity_delta: float = 0.0


class Neo4jNode(BaseModel):
    id: str
    type: NodeType
    properties: Dict[str, Any]


class Neo4jRelationship(BaseModel):
    start_node_id: str
    end_node_id: str
    relationship_type: str
    properties: Dict[str, Any] = {}


class AnalysisRequest(BaseModel):
    git_url: HttpUrl
    branch_filter: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    include_llm_analysis: bool = True
    max_commits: Optional[int] = 100  # Default limit to 100 commits


class ChatQuery(BaseModel):
    codebase_id: str
    question: str
    context: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []


class ChatResponse(BaseModel):
    response: str
    context: Optional[Dict[str, Any]] = None
    relevant_nodes: Optional[List[Dict[str, Any]]] = []
    cypher_queries_used: Optional[List[str]] = []