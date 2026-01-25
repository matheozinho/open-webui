"""
User Profiles Model for User Identity & Memory Architecture (UIMA)
Stores user-specific preferences and context for personalized AI responses
"""

import time
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Text, BigInteger, JSON, ForeignKey, Index
from open_webui.internal.db import Base, get_db

from pydantic import BaseModel, ConfigDict


####################
# UserProfile DB Schema
####################


class UserProfile(Base):
    """Database model for user profiles with memory and preferences"""
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True, unique=True)
    user_id = Column(String, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    job = Column(String(255), nullable=True)
    tone_preference = Column(String(100), nullable=True)
    project_context = Column(Text, nullable=True)
    preferences = Column(JSON, nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)

    __table_args__ = (
        Index("ix_user_profiles_user_id", "user_id"),
    )


####################
# Pydantic Models
####################


class UserProfileForm(BaseModel):
    """Form model for creating/updating user profiles"""
    job: Optional[str] = None
    tone_preference: Optional[str] = None
    project_context: Optional[str] = None
    preferences: Optional[dict] = None

    model_config = ConfigDict(extra="allow")


class UserProfileModel(BaseModel):
    """Response model for user profiles"""
    id: str
    user_id: str
    job: Optional[str] = None
    tone_preference: Optional[str] = None
    project_context: Optional[str] = None
    preferences: Optional[dict] = None
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


####################
# Database Operations
####################


class UserProfiles:
    """Database operations for user profiles"""

    @staticmethod
    def get_profile_by_user_id(user_id: str) -> Optional[UserProfileModel]:
        """Get user profile by user ID"""
        try:
            with get_db() as db:
                profile = db.query(UserProfile).filter(
                    UserProfile.user_id == user_id
                ).first()
                return UserProfileModel.model_validate(profile) if profile else None
        except Exception as e:
            print(f"Error fetching user profile: {e}")
            return None

    @staticmethod
    def get_profile(profile_id: str) -> Optional[UserProfileModel]:
        """Get user profile by profile ID"""
        try:
            with get_db() as db:
                profile = db.query(UserProfile).filter(
                    UserProfile.id == profile_id
                ).first()
                return UserProfileModel.model_validate(profile) if profile else None
        except Exception as e:
            print(f"Error fetching user profile: {e}")
            return None

    @staticmethod
    def create_profile(user_id: str, profile: UserProfileForm) -> Optional[UserProfileModel]:
        """Create a new user profile"""
        try:
            with get_db() as db:
                new_profile = UserProfile(
                    id=f"{user_id}_{int(time.time())}",
                    user_id=user_id,
                    job=profile.job,
                    tone_preference=profile.tone_preference,
                    project_context=profile.project_context,
                    preferences=profile.preferences or {},
                    created_at=int(time.time() * 1000),
                    updated_at=int(time.time() * 1000),
                )
                db.add(new_profile)
                db.commit()
                return UserProfileModel.model_validate(new_profile)
        except Exception as e:
            print(f"Error creating user profile: {e}")
            return None

    @staticmethod
    def update_profile(user_id: str, profile: UserProfileForm) -> Optional[UserProfileModel]:
        """Update an existing user profile"""
        try:
            with get_db() as db:
                existing_profile = db.query(UserProfile).filter(
                    UserProfile.user_id == user_id
                ).first()

                if not existing_profile:
                    # Create new profile if it doesn't exist
                    return UserProfiles.create_profile(user_id, profile)

                existing_profile.job = profile.job or existing_profile.job
                existing_profile.tone_preference = profile.tone_preference or existing_profile.tone_preference
                existing_profile.project_context = profile.project_context or existing_profile.project_context
                if profile.preferences:
                    existing_profile.preferences = profile.preferences
                existing_profile.updated_at = int(time.time() * 1000)

                db.add(existing_profile)
                db.commit()
                return UserProfileModel.model_validate(existing_profile)
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return None

    @staticmethod
    def delete_profile(user_id: str) -> bool:
        """Delete user profile"""
        try:
            with get_db() as db:
                db.query(UserProfile).filter(
                    UserProfile.user_id == user_id
                ).delete()
                db.commit()
                return True
        except Exception as e:
            print(f"Error deleting user profile: {e}")
            return False
