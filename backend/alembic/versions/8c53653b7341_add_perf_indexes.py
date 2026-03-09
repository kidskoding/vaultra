"""add performance indexes

Revision ID: 8c53653b7341
Revises: 4dc12d5ee3d4
Create Date: 2026-02-23 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = '8c53653b7341'
down_revision: Union[str, None] = '4dc12d5ee3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fastest path for GET /readiness?business_id=...
    op.create_index('ix_readiness_scores_business_created',
                    'readiness_scores', ['business_id', 'created_at'],
                    postgresql_ops={'created_at': 'DESC'})

    # Fastest path for GET /metrics?business_id=...
    op.create_index('ix_metric_snapshots_business_period_end',
                    'financial_metric_snapshots', ['business_id', 'period_end'],
                    postgresql_ops={'period_end': 'DESC'})

    # Fastest path for GET /recommendations?business_id=...
    op.create_index('ix_recommendations_business_id',
                    'recommendations', ['business_id'])

    # Faster membership check used by assert_member on every request
    op.create_index('ix_user_business_memberships_business_id',
                    'user_business_memberships', ['business_id'])

    # Faster conversation and message lookups for agent
    op.create_index('ix_agent_conversations_business_id',
                    'agent_conversations', ['business_id'])
    op.create_index('ix_agent_messages_conversation_id',
                    'agent_messages', ['conversation_id'])


def downgrade() -> None:
    op.drop_index('ix_agent_messages_conversation_id', table_name='agent_messages')
    op.drop_index('ix_agent_conversations_business_id', table_name='agent_conversations')
    op.drop_index('ix_user_business_memberships_business_id', table_name='user_business_memberships')
    op.drop_index('ix_recommendations_business_id', table_name='recommendations')
    op.drop_index('ix_metric_snapshots_business_period_end', table_name='financial_metric_snapshots')
    op.drop_index('ix_readiness_scores_business_created', table_name='readiness_scores')
