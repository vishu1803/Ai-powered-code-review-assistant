from typing import Optional, Dict, Any, List
from pydantic import BaseModel, validator
from datetime import datetime

class RepositoryBase(BaseModel):
    name: str
    full_name: str
    description: Optional[str] = None
    url: str
    clone_url: str
    default_branch: str = "main"
    language: Optional[str] = None
    is_private: bool = False

class RepositoryCreate(RepositoryBase):
    provider: str  # github, gitlab, bitbucket
    external_id: str
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed_providers = ['github', 'gitlab', 'bitbucket']
        if v not in allowed_providers:
            raise ValueError(f'Provider must be one of: {allowed_providers}')
        return v

class RepositoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    default_branch: Optional[str] = None
    is_active: Optional[bool] = None
    analysis_enabled: Optional[bool] = None
    auto_review: Optional[bool] = None
    review_rules: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None

class RepositoryInDBBase(RepositoryBase):
    id: int
    size: int = 0
    is_active: bool = True
    is_archived: bool = False
    provider: str
    external_id: str
    webhook_id: Optional[str] = None
    analysis_enabled: bool = True
    auto_review: bool = True
    review_rules: Dict[str, Any] = {}
    notification_settings: Dict[str, Any] = {}
    total_reviews: int = 0
    total_issues: int = 0
    avg_review_time: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_analysis: Optional[datetime] = None
    owner_id: int
    
    class Config:
        from_attributes = True

class Repository(RepositoryInDBBase):
    pass

# Simple review summary schema to avoid forward reference
class ReviewSummary(BaseModel):
    id: int
    title: str
    status: str
    created_at: datetime
    total_issues: int = 0
    code_quality_score: Optional[float] = None

class RepositoryWithStats(Repository):
    recent_reviews: List[ReviewSummary] = []
    quality_trend: List[Dict[str, Any]] = []

# Connect Repository Schema
class ConnectRepositoryRequest(BaseModel):
    provider: str
    repository_url: str
    access_token: Optional[str] = None
    
    @validator('provider')
    def validate_provider(cls, v):
        allowed_providers = ['github', 'gitlab', 'bitbucket']
        if v not in allowed_providers:
            raise ValueError(f'Provider must be one of: {allowed_providers}')
        return v

class WebhookSetupRequest(BaseModel):
    repository_id: int
    webhook_url: str
    events: List[str] = ["push", "pull_request"]
