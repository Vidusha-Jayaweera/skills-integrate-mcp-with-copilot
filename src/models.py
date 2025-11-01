from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class Activity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str
    schedule: str
    max_participants: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    signups: List["Signup"] = Relationship(back_populates="activity")


class Signup(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    activity_id: int = Field(foreign_key="activity.id")
    email: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    activity: Optional[Activity] = Relationship(back_populates="signups")
