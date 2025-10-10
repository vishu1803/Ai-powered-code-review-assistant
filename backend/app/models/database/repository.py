from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base


class Repository(Base):
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    full_name = Column(String(500), nullable=False)  # owner/repo format
    description = Column(Text, nullable=True)
    
    # Repository Information
    url = Column(String(500), nullable=False)
    clone_url = Column(String(500), nullable=False)
    default_branch = Column(String(100), default="main")
    language = Column(String(50), nullable=True)
    size = Column(Integer, default=0)
    
    # Repository Status
    is_private = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)
    
    # VCS Integration
    provider = Column(String(50), nullable=False)  # github, gitlab, bitbucket
    external_id = Column(String(100), nullable=False, index=True)
    webhook_id = Column(String(100), nullable=True)
    
    # Analysis Configuration
    analysis_enabled = Column(Boolean, default=True)
    auto_review = Column(Boolean, default=True)
    review_rules = Column(JSON, default=dict)
    notification_settings = Column(JSON, default=dict)
    
    # Statistics
    total_reviews = Column(Integer, default=0)
    total_issues = Column(Integer, default=0)
    avg_review_time = Column(Integer, default=0)  # in minutes
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_analysis = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign Keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="repositories")
    reviews = relationship("Review", back_populates="repository")
    pull_requests = relationship("PullRequest", back_populates="repository")
