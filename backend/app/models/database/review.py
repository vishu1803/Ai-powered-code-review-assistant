from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.models.database.base import Base

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
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Status and Progress
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    progress = Column(Float, default=0.0)
    
    # Pull Request Information
    pr_number = Column(Integer)
    pr_title = Column(String(500))
    pr_url = Column(String(500))
    source_branch = Column(String(100))
    target_branch = Column(String(100))
    
    # File Analysis
    total_files = Column(Integer, default=0)
    analyzed_files = Column(Integer, default=0)
    
    # Issue Counts
    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)
    
    # Quality Scores
    code_quality_score = Column(Float)
    security_score = Column(Float)
    maintainability_score = Column(Float)
    test_coverage = Column(Float)
    
    # AI Analysis
    ai_summary = Column(Text)
    ai_recommendations = Column(JSON, default=list)
    analysis_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime)
    
    # Foreign Keys
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    repository = relationship("Repository", back_populates="reviews")
    author = relationship("User", back_populates="reviews")
    issues = relationship("Issue", back_populates="review", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="review", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Review(id={self.id}, title='{self.title}', status='{self.status}')>"

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    severity = Column(Enum(IssueSeverity), nullable=False)
    
    # Rule Information
    rule_id = Column(String(100))
    
    # File Location
    file_path = Column(String(500), nullable=False)
    line_start = Column(Integer, nullable=False)
    line_end = Column(Integer)
    column_start = Column(Integer)
    column_end = Column(Integer)
    
    # Code Context
    code_snippet = Column(Text)
    suggested_fix = Column(Text)
    ai_explanation = Column(Text)
    confidence_score = Column(Float)
    
    # Status
    is_resolved = Column(Boolean, default=False)
    is_false_positive = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime)
    
    # Foreign Key
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    
    # Relationships
    review = relationship("Review", back_populates="issues")
    comments = relationship("Comment", back_populates="issue", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Issue(id={self.id}, title='{self.title}', severity='{self.severity}')>"

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    comment_type = Column(String(50), default="general")
    
    # File Context (optional)
    file_path = Column(String(500))
    line_number = Column(Integer)
    
    # Status
    is_resolved = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Foreign Keys
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    review_id = Column(Integer, ForeignKey("reviews.id"))
    issue_id = Column(Integer, ForeignKey("issues.id"))
    parent_id = Column(Integer, ForeignKey("comments.id"))  # For threaded comments
    
    # Relationships
    author = relationship("User", back_populates="comments")
    review = relationship("Review", back_populates="comments")
    issue = relationship("Issue", back_populates="comments")
    parent = relationship("Comment", remote_side=[id])
    replies = relationship("Comment", back_populates="parent")

    def __repr__(self):
        return f"<Comment(id={self.id}, author_id={self.author_id})>"
