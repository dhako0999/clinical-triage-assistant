
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SiteQuery(Base):
    __tablename__ = "site_queries"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )

    site_id: Mapped[str] = mapped_column(String(50))
    query_text: Mapped[str] = mapped_column(Text)

    category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    requires_escalation: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True
    )

    assigned_team: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    ai_draft_response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending_review"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )


class ReviewAction(Base):
    __tablename__ = "review_actions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )

    query_id: Mapped[str] = mapped_column(
        ForeignKey("site_queries.id"),
        nullable=False
    )

    reviewer_name: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(30))

    edited_response: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )