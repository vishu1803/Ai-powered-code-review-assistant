from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Float, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base
import enum


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    # Review Status
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING)
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    
    # Pull Request Information
    pr_number = Column(Integer, nullable=True)
    pr_title = Column(String(500), nullable=True)
    pr_url = Column(String(500), nullable=True)
    source_branch = Column(String(255), nullable=True)
    target_branch = Column(String(255), nullable=True)
    
    # Analysis Results
    total_files = Column(Integer, default=0)
    analyzed_files = Column(Integer, default=0)
    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)
    
    # Quality Metrics
    code_quality_score = Column(Float, nullable=True)  # 0.0 to 10.0
    security_score = Column(Float, nullable=True)
    maintainability_score = Column(Float, nullable=True)
    test_coverage = Column(Float, nullable=True)
    
    # AI Analysis
    ai_summary = Column(Text, nullable=True)
    ai_recommendations = Column(JSON, default=list)
    analysis_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign Keys
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    repository = relationship("Repository", back_populates="reviews")
    author = relationship("User", back_populates="reviews")
    issues = relationship("Issue", back_populates="review")
    comments = relationship("Comment", back_populates="review")


class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    
    # Issue Classification
    category = Column(String(100), nullable=False)  # security, performance, style, etc.
    severity = Column(Enum(IssueSeverity), nullable=False)
    rule_id = Column(String(100), nullable=True)
    
    # File Location
    file_path = Column(String(1000), nullable=False)
    line_start = Column(Integer, nullable=False)
    line_end = Column(Integer, nullable=True)
    column_start = Column(Integer, nullable=True)
    column_end = Column(Integer, nullable=True)
    
    # Code Context
    code_snippet = Column(Text, nullable=True)
    suggested_fix = Column(Text, nullable=True)
    
    # AI Analysis
    ai_explanation = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    
    # Status
    is_resolved = Column(Boolean, default=False)
    is_false_positive = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign Keys
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    
    # Relationships
    review = relationship("Review", back_populates="issues")
    comments = relationship("Comment", back_populates="issue")


class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    
    # Comment Type
    comment_type = Column(String(50), default="general")  # suggestion, question, approval
    
    # Position (for inline comments)
    file_path = Column(String(1000), nullable=True)
    line_number = Column(Integer, nullable=True)
    
    # Status
    is_resolved = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign Keys
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=True)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)  # For replies
    
    # Relationships
    author = relationship("User", back_populates="comments")
    review = relationship("Review", back_populates="comments")
    issue = relationship("Issue", back_populates="comments")
    parent = relationship("Comment", remote_side=[id])
