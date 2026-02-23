import uuid
from sqlalchemy import Column, String, DateTime, Integer, Numeric, Date, ForeignKey, Text, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.shared.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    name = Column(String(255))
    avatar_url = Column(String(512))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Business(Base):
    __tablename__ = "businesses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    legal_entity = Column(String(255))
    industry = Column(String(100))
    revenue_estimate = Column(Numeric(15, 2))
    founded_at = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UserBusinessMembership(Base):
    __tablename__ = "user_business_memberships"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), primary_key=True)
    role = Column(String(20), nullable=False, default="owner")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class IntegrationAccount(Base):
    __tablename__ = "integration_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    provider = Column(String(50), nullable=False)
    external_id = Column(String(255), nullable=False)
    access_token_encrypted = Column(Text)
    metadata_ = Column("metadata", JSONB)
    status = Column(String(20), default="active")
    last_synced_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("business_id", "provider", name="uq_integration_business_provider"),)


class StripeEvent(Base):
    __tablename__ = "stripe_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integration_accounts.id"))
    stripe_event_id = Column(String(255), nullable=False, unique=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSONB)
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FinancialMetricSnapshot(Base):
    __tablename__ = "financial_metric_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    revenue_total = Column(Numeric(15, 2))
    revenue_volatility = Column(Numeric(10, 4))
    chargeback_count = Column(Integer, default=0)
    chargeback_ratio = Column(Numeric(5, 4))
    refund_count = Column(Integer, default=0)
    refund_ratio = Column(Numeric(5, 4))
    payout_reliability = Column(Numeric(5, 4))
    transaction_count = Column(Integer, default=0)
    average_transaction_size = Column(Numeric(15, 2))
    mrr = Column(Numeric(15, 2))
    metrics_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("business_id", "period_start", "period_end", name="uq_metrics_period"),)


class ReadinessScore(Base):
    __tablename__ = "readiness_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    score = Column(Integer, nullable=False)
    tier = Column(String(30), nullable=False)
    components = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (CheckConstraint("score >= 0 AND score <= 100", name="ck_score_range"),)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    priority = Column(String(20), default="medium")
    category = Column(String(50))
    status = Column(String(20), default="pending")
    metric_refs = Column(JSONB)
    estimated_impact = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AgentConversation(Base):
    __tablename__ = "agent_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("agent_conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
