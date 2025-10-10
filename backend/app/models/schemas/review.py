from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from app.models.database.review import ReviewStatus, IssueSeverity


class ReviewBase(BaseModel):
    title: str
    description: Optional[str] = None
    pr_number: Optional[int] = None
    pr_title: Optional[str] = None
    pr_url: Optional[str] = None
    source_branch: Optional[str] = None
    target_branch: Optional[str] = None


class ReviewCreate(ReviewBase):
    repository_id: int


class ReviewUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ReviewStatus] = None


class IssueBase(BaseModel):
    title: str
    description: str
    category: str
    severity: IssueSeverity
    rule_id: Optional[str] = None
    file_path: str
    line_start: int
    line_end: Optional[int] = None
    column_start: Optional[int] = None
    column_end: Optional[int] = None
    code_snippet: Optional[str] = None
    suggested_fix: Optional[str] = None


class IssueCreate(IssueBase):
    review_id: int
    ai_explanation: Optional[str] = None
    confidence_score: Optional[float] = None


class IssueUpdate(BaseModel):
    is_resolved: Optional[bool] = None
    is_false_positive: Optional[bool] = None


class Issue(IssueBase):
    id: int
    review_id: int
    ai_explanation: Optional[str] = None
    confidence_score: Optional[float] = None
    is_resolved: bool = False
    is_false_positive: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CommentBase(BaseModel):
    content: str
    comment_type: str = "general"
    file_path: Optional[str] = None
    line_number: Optional[int] = None


class CommentCreate(CommentBase):
    review_id: Optional[int] = None
    issue_id: Optional[int] = None
    parent_id: Optional[int] = None


class Comment(CommentBase):
    id: int
    author_id: int
    review_id: Optional[int] = None
    issue_id: Optional[int] = None
    parent_id: Optional[int] = None
    is_resolved: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ReviewInDBBase(ReviewBase):
    id: int
    status: ReviewStatus
    progress: float = 0.0
    total_files: int = 0
    analyzed_files: int = 0
    total_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    code_quality_score: Optional[float] = None
    security_score: Optional[float] = None
    maintainability_score: Optional[float] = None
    test_coverage: Optional[float] = None
    ai_summary: Optional[str] = None
    ai_recommendations: List[Dict[str, Any]] = []
    analysis_metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    repository_id: int
    author_id: int
    
    class Config:
        from_attributes = True


class Review(ReviewInDBBase):
    issues: List[Issue] = []
    comments: List[Comment] = []


class ReviewSummary(BaseModel):
    id: int
    title: str
    status: ReviewStatus
    progress: float
    total_issues: int
    critical_issues: int
    code_quality_score: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    repository_id: int
    
    class Config:
        from_attributes = True


# Analysis Request/Response
class AnalysisRequest(BaseModel):
    repository_id: int
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    files: Optional[List[str]] = None  # Specific files to analyze
    rules: Optional[List[str]] = None  # Specific rules to apply


class AnalysisProgress(BaseModel):
    review_id: int
    status: ReviewStatus
    progress: float
    current_file: Optional[str] = None
    total_files: int
    analyzed_files: int
    estimated_time_remaining: Optional[int] = None  # in seconds
