from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Interval,
    Numeric,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from timegrip.entities.project import ProjectColor, ProjectStatus
from timegrip.entities.refresh_token import RefreshTokenRevokeReason
from timegrip.entities.user import Locale, TimeFormat


class Base(DeclarativeBase):
    pass


class UserDBModel(Base):
    __tablename__ = "app_user"
    __table_args__ = (
        CheckConstraint(
            "time_format IN ("
            + ", ".join(f"'{tf.value}'" for tf in TimeFormat)
            + ")",
            name="ck_app_user_time_format",
        ),
        CheckConstraint(
            "locale IN ("
            + ", ".join(f"'{loc.value}'" for loc in Locale)
            + ")",
            name="ck_app_user_locale",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    time_format: Mapped[str] = mapped_column(
        default=TimeFormat.TWENTY_FOUR_HOUR.value,
        server_default=text(f"'{TimeFormat.TWENTY_FOUR_HOUR.value}'"),
        nullable=False,
    )
    locale: Mapped[str] = mapped_column(
        default=Locale.EN.value,
        server_default=text(f"'{Locale.EN.value}'"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"User(id={self.id} email={self.email})"


class ActivationCodeDBModel(Base):
    __tablename__ = "app_activation_code"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    attempts: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"ActivationCode(id={self.id} user_id={self.user_id})"


class PasswordResetCodeDBModel(Base):
    __tablename__ = "app_password_reset_code"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    code: Mapped[str] = mapped_column(
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    attempts: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"PasswordResetCode(id={self.id} user_id={self.user_id})"


class RefreshTokenDBModel(Base):
    __tablename__ = "app_refresh_token"
    __table_args__ = (
        CheckConstraint(
            "revoke_reason IS NULL OR revoke_reason IN ("
            + ", ".join(f"'{r.value}'" for r in RefreshTokenRevokeReason)
            + ")",
            name="ck_app_refresh_token_revoke_reason",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    family_id: Mapped[UUID] = mapped_column(
        server_default=text("gen_random_uuid()"),
        index=True,
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        unique=True,
        index=True,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoke_reason: Mapped[str | None] = mapped_column(
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"RefreshToken(id={self.id} user_id={self.user_id})"


class OutboxEmailDBModel(Base):
    __tablename__ = "app_outbox_email"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )
    to_email: Mapped[str] = mapped_column(
        nullable=False,
    )
    subject: Mapped[str] = mapped_column(
        nullable=False,
    )
    body: Mapped[str] = mapped_column(
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        default="pending",
        nullable=False,
    )
    attempts: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self):
        return f"OutboxEmail(id={self.id} status={self.status})"


class ProjectDBModel(Base):
    __tablename__ = "app_project"
    __table_args__ = (
        CheckConstraint(
            "color IN ("
            + ", ".join(f"'{color.value}'" for color in ProjectColor)
            + ")",
            name="ck_app_project_color",
        ),
        CheckConstraint(
            "hourly_rate IS NULL OR hourly_rate >= 0",
            name="ck_app_project_hourly_rate",
        ),
        CheckConstraint(
            "status IN ("
            + ", ".join(f"'{s.value}'" for s in ProjectStatus)
            + ")",
            name="ck_app_project_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(
        nullable=False,
    )
    color: Mapped[str] = mapped_column(
        server_default=text(f"'{ProjectColor.GRAY.value}'"),
        nullable=False,
    )
    hourly_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    round_to_hour: Mapped[bool] = mapped_column(
        server_default=text("false"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        default=ProjectStatus.ACTIVE.value,
        server_default=text(f"'{ProjectStatus.ACTIVE.value}'"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"Project(id={self.id} name={self.name})"


class TimerDBModel(Base):
    __tablename__ = "app_timer"
    __table_args__ = (
        CheckConstraint(
            "end_time IS NULL OR end_time > start_time",
            name="ck_app_timer_end_after_start",
        ),
        Index(
            "uq_app_timer_running_per_user",
            "user_id",
            unique=True,
            postgresql_where=text("end_time IS NULL"),
        ),
        CheckConstraint(
            "hourly_rate IS NULL OR hourly_rate >= 0",
            name="ck_app_timer_hourly_rate",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration: Mapped[timedelta | None] = mapped_column(
        Interval(),
        Computed("end_time - start_time", persisted=True),
        nullable=True,
    )
    hourly_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    round_to_hour: Mapped[bool] = mapped_column(
        server_default=text("false"),
        nullable=False,
    )
    billable_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("app_user.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("app_project.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    def __repr__(self):
        return f"Timer(id={self.id} duration={self.duration})"
