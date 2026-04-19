import time
from typing import Optional

from sqlalchemy.orm import Session
from open_webui.internal.db import Base, get_db, get_db_context

from pydantic import BaseModel, ConfigDict
from sqlalchemy import (
    BigInteger,
    Column,
    Integer,
    String,
    JSON,
    ForeignKey,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB

import logging

log = logging.getLogger(__name__)

####################
# UserLearningProgress DB Schema
####################


class UserLearningProgress(Base):
    __tablename__ = "user_learning_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("user.id"), unique=True, nullable=False, index=True)
    current_step = Column(Integer, nullable=False, default=1)
    step_data = Column(JSONB, nullable=True)
    last_step_at = Column(BigInteger, nullable=True)
    completed_at = Column(BigInteger, nullable=True)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


class UserLearningProgressModel(BaseModel):
    id: Optional[int] = None
    user_id: str
    current_step: int = 1
    step_data: Optional[dict] = None
    last_step_at: Optional[int] = None
    completed_at: Optional[int] = None
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


####################
# CRUD Operations
####################


class UserLearningProgressCRUD:
    @staticmethod
    def get_or_create(user_id: str, db: Session) -> UserLearningProgress:
        """Get user progress or create with default step 1"""
        progress = (
            db.query(UserLearningProgress)
            .filter(UserLearningProgress.user_id == user_id)
            .first()
        )

        if not progress:
            current_time = int(time.time() * 1000)
            progress = UserLearningProgress(
                user_id=user_id,
                current_step=1,
                step_data={},
                created_at=current_time,
                updated_at=current_time,
            )
            db.add(progress)
            db.commit()
            db.refresh(progress)
            log.info(f"Created learning progress for user {user_id} at step 1")

        return progress

    @staticmethod
    def get_by_user_id(user_id: str, db: Session) -> Optional[UserLearningProgress]:
        """Get user progress"""
        return (
            db.query(UserLearningProgress)
            .filter(UserLearningProgress.user_id == user_id)
            .first()
        )

    @staticmethod
    def update_step(
        user_id: str, new_step: int, step_data: Optional[dict] = None, db: Session = None
    ) -> UserLearningProgress:
        """Update current step and step data"""
        if db is None:
            db = get_db_context()

        progress = UserLearningProgressCRUD.get_or_create(user_id, db)

        # Validate step range
        if new_step < 1 or new_step > 6:
            raise ValueError(f"Invalid step: {new_step}. Must be between 1 and 6.")

        progress.current_step = new_step
        progress.updated_at = int(time.time() * 1000)

        if step_data is not None:
            progress.step_data = {
                **(progress.step_data or {}),
                **step_data,
            }

        progress.last_step_at = int(time.time() * 1000)
        db.add(progress)
        db.commit()
        db.refresh(progress)

        log.info(f"Updated user {user_id} to step {new_step}")
        return progress

    @staticmethod
    def mark_completed(user_id: str, db: Session = None) -> UserLearningProgress:
        """Mark all steps as completed"""
        if db is None:
            db = get_db_context()

        progress = UserLearningProgressCRUD.get_or_create(user_id, db)
        progress.current_step = 6
        progress.completed_at = int(time.time() * 1000)
        progress.updated_at = int(time.time() * 1000)

        db.add(progress)
        db.commit()
        db.refresh(progress)

        log.info(f"Marked user {user_id} as completed")
        return progress

    @staticmethod
    def reset_progress(user_id: str, db: Session = None) -> UserLearningProgress:
        """Reset user back to step 1 (admin operation)"""
        if db is None:
            db = get_db_context()

        progress = UserLearningProgressCRUD.get_or_create(user_id, db)
        progress.current_step = 1
        progress.step_data = {}
        progress.updated_at = int(time.time() * 1000)

        db.add(progress)
        db.commit()
        db.refresh(progress)

        log.info(f"Reset user {user_id} progress to step 1")
        return progress
