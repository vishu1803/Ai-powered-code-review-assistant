from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    website: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    website: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None

class UserInDB(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    is_superuser: bool
    github_id: Optional[str] = None
    gitlab_id: Optional[str] = None
    bitbucket_id: Optional[str] = None
    preferences: Dict[str, Any]
    notification_settings: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class User(UserInDB):
    pass

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None

# ADD THESE MISSING SCHEMAS:

class LoginRequest(BaseModel):
    """Schema for login requests."""
    email_or_username: str = Field(..., description="Email or username")
    password: str = Field(..., min_length=1, description="User password")

class RefreshTokenRequest(BaseModel):
    """Schema for refresh token requests."""
    refresh_token: str = Field(..., description="Refresh token")

class PasswordChangeRequest(BaseModel):
    """Schema for password change requests."""
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., min_length=8, description="Confirm new password")
    
    def validate_passwords_match(self):
        """Validate that new password and confirm password match."""
        if self.new_password != self.confirm_password:
            raise ValueError("New password and confirm password do not match")
        return self
