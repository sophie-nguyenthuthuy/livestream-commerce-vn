"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-14

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # TimescaleDB is recommended but optional — wrap so vanilla Postgres still boots.
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    platform = sa.Enum("TIKTOK_SHOP", "SHOPEE_LIVE", "LAZADA_LIVE", name="platform")
    stream_status = sa.Enum("SCHEDULED", "LIVE", "ENDED", name="streamstatus")
    dialect = sa.Enum("NORTH", "SOUTH", "NEUTRAL", name="dialect")
    intent = sa.Enum(
        "HOOK", "PITCH", "SOCIAL_PROOF", "OBJECTION", "URGENCY", "CLOSE", name="scriptintent"
    )
    ab_status = sa.Enum(
        "DRAFT", "RUNNING", "PAUSED", "DECIDED", "ARCHIVED", name="abteststatus"
    )
    ab_event_type = sa.Enum("IMPRESSION", "CLICK", name="abtesteventtype")

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("sku", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("name_normalized", sa.String(255), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("price_vnd", sa.Numeric(14, 2), nullable=False),
        sa.Column("cost_vnd", sa.Numeric(14, 2)),
        sa.Column("description", sa.Text),
        sa.Column("image_url", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_products_name_normalized", "products", ["name_normalized"])
    op.create_index("ix_products_category", "products", ["category"])
    op.create_index("ix_products_category_price", "products", ["category", "price_vnd"])

    op.create_table(
        "streams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("platform", platform, nullable=False),
        sa.Column("platform_stream_id", sa.String(64), nullable=False),
        sa.Column("host_handle", sa.String(128), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", stream_status, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("total_viewers", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("peak_concurrent_viewers", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_orders", sa.Integer, nullable=False, server_default="0"),
        sa.Column("gmv_vnd", sa.Numeric(16, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("platform", "platform_stream_id", name="uq_streams_platform_id"),
    )
    op.create_index("ix_streams_platform_stream_id", "streams", ["platform_stream_id"])
    op.create_index("ix_streams_host_handle", "streams", ["host_handle"])
    op.create_index("ix_streams_host_started", "streams", ["host_handle", "started_at"])

    op.create_table(
        "stream_minutes",
        sa.Column("stream_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("streams.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("bucket_ts", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("concurrent_viewers", sa.Integer, nullable=False, server_default="0"),
        sa.Column("new_viewers", sa.Integer, nullable=False, server_default="0"),
        sa.Column("comments", sa.Integer, nullable=False, server_default="0"),
        sa.Column("likes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("shares", sa.Integer, nullable=False, server_default="0"),
        sa.Column("product_clicks", sa.Integer, nullable=False, server_default="0"),
        sa.Column("add_to_carts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("orders", sa.Integer, nullable=False, server_default="0"),
        sa.Column("gmv_vnd", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("featured_product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="SET NULL")),
    )
    op.create_index("ix_stream_minutes_bucket", "stream_minutes", ["bucket_ts"])

    # Convert to hypertable when TimescaleDB is present
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
                PERFORM create_hypertable('stream_minutes', 'bucket_ts',
                    chunk_time_interval => INTERVAL '7 days',
                    if_not_exists => TRUE,
                    migrate_data => TRUE);
            END IF;
        END$$;
        """
    )

    op.create_table(
        "stream_products",
        sa.Column("stream_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("streams.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("featured_from", sa.DateTime(timezone=True)),
        sa.Column("featured_to", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "script_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="SET NULL")),
        sa.Column("dialect", dialect, nullable=False),
        sa.Column("intent", intent, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("speech_duration_sec", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tags", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("model", sa.String(64)),
        sa.Column("prompt_hash", sa.String(64)),
        sa.Column("use_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("upvotes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_script_templates_filter", "script_templates", ["dialect", "intent"])
    op.create_index("ix_script_templates_product", "script_templates", ["product_id", "intent"])

    op.create_table(
        "ab_tests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("hypothesis", sa.Text),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="SET NULL")),
        sa.Column("status", ab_status, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("min_impressions_per_variant", sa.Integer, nullable=False, server_default="1000"),
        sa.Column("confidence_target", sa.Float, nullable=False, server_default="0.95"),
        sa.Column("winner_variant_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "ab_test_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("test_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ab_tests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(64), nullable=False),
        sa.Column("thumbnail_url", sa.String(512), nullable=False),
        sa.Column("weight", sa.Integer, nullable=False, server_default="50"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("test_id", "label", name="uq_ab_variant_label"),
        sa.CheckConstraint("weight >= 0 AND weight <= 100", name="ck_ab_variant_weight"),
    )
    op.create_index("ix_ab_test_variants_test_id", "ab_test_variants", ["test_id"])
    op.create_foreign_key(
        "fk_ab_tests_winner_variant",
        "ab_tests",
        "ab_test_variants",
        ["winner_variant_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "ab_test_events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ab_test_variants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", ab_event_type, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session_hash", sa.String(64), nullable=False),
    )
    op.create_index("ix_ab_test_events_variant_id", "ab_test_events", ["variant_id"])
    op.create_index("ix_ab_test_events_event_type", "ab_test_events", ["event_type"])
    op.create_index(
        "ix_ab_events_variant_type_time",
        "ab_test_events",
        ["variant_id", "event_type", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_table("ab_test_events")
    op.drop_constraint("fk_ab_tests_winner_variant", "ab_tests", type_="foreignkey")
    op.drop_table("ab_test_variants")
    op.drop_table("ab_tests")
    op.drop_table("script_templates")
    op.drop_table("stream_products")
    op.drop_table("stream_minutes")
    op.drop_table("streams")
    op.drop_table("products")
    for name in ("abtesteventtype", "abteststatus", "scriptintent", "dialect", "streamstatus", "platform"):
        op.execute(f"DROP TYPE IF EXISTS {name}")
