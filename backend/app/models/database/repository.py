from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.models.database.base import Base

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=False)
    description = Column(Text)
    url = Column(String(500), nullable=False)
    clone_url = Column(String(500), nullable=False)
    default_branch = Column(String(100), default="main")
    language = Column(String(50))
    size = Column(Integer, default=0)
    
    # Repository flags
    is_private = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)
    
    # Provider information
    provider = Column(String(20), nullable=False)  # github, gitlab, bitbucket
    external_id = Column(String(100), nullable=False)
    webhook_id = Column(String(100))
    
    # Configuration
    analysis_enabled = Column(Boolean, default=True)
    auto_review = Column(Boolean, default=False)
    review_rules = Column(JSON, default=dict)
    notification_settings = Column(JSON, default=dict)
    
    # Statistics
    total_reviews = Column(Integer, default=0)
    total_issues = Column(Integer, default=0)
    avg_review_time = Column(Integer, default=0)  # in minutes
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_analysis = Column(DateTime)
    
    # Foreign Key
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="repositories")
    reviews = relationship("Review", back_populates="repository", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Repository(id={self.id}, name='{self.name}', provider='{self.provider}')>"
