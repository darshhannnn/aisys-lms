"""Initial schema creation

Revision ID: 001
Revises:
Create Date: 2024-10-04

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create branches table
    op.create_table(
        'branches',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=16), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_branches_code'), 'branches', ['code'], unique=True)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('smart_card_id', sa.String(length=128), nullable=True),
        sa.Column('smart_card_provider', sa.String(length=64), nullable=True),
        sa.Column('role', sa.Enum('super_admin', 'librarian', 'circulation_staff', 'cataloguer', 'reports_viewer', 'opac_user', name='user_role'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('branch_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('smart_card_id'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_smart_card_id'), 'users', ['smart_card_id'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create bibliographic_records table
    op.create_table(
        'bibliographic_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=False),
        sa.Column('isbn', sa.String(length=20), nullable=True),
        sa.Column('issn', sa.String(length=20), nullable=True),
        sa.Column('publisher', sa.String(length=255), nullable=True),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('edition', sa.String(length=100), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('call_number', sa.String(length=100), nullable=True),
        sa.Column('material_type', sa.String(length=50), nullable=False, server_default='book'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.PrimaryKeyConstraint('id')
    )

    # Create items table
    op.create_table(
        'items',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('barcode', sa.String(length=64), nullable=False),
        sa.Column('bibliographic_record_id', sa.String(length=36), nullable=False),
        sa.Column('call_number', sa.String(length=100), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=False, server_default='stacks'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='available'),
        sa.Column('item_type', sa.String(length=50), nullable=False, server_default='circulating'),
        sa.Column('condition', sa.String(length=50), nullable=False, server_default='good'),
        sa.Column('rfid_tag_id', sa.String(length=36), nullable=True),
        sa.Column('encoded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.ForeignKeyConstraint(['bibliographic_record_id'], ['bibliographic_records.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('barcode')
    )
    op.create_index(op.f('ix_items_barcode'), 'items', ['barcode'], unique=True)

    # Create members table
    op.create_table(
        'members',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('member_number', sa.String(length=32), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=32), nullable=True),
        sa.Column('national_id', sa.String(length=64), nullable=True),
        sa.Column('photo_url', sa.String(length=512), nullable=True),
        sa.Column('patron_card_barcode', sa.String(length=64), nullable=True),
        sa.Column('category', sa.Enum('student', 'faculty', 'staff', 'external', 'honorary', name='member_category'), nullable=False, server_default='student'),
        sa.Column('status', sa.Enum('active', 'blocked', 'suspended', 'expired', 'cancelled', name='member_status'), nullable=False, server_default='active'),
        sa.Column('membership_start', sa.Date(), nullable=True),
        sa.Column('membership_end', sa.Date(), nullable=True),
        sa.Column('block_reason', sa.Text(), nullable=True),
        sa.Column('blocked_by_id', sa.String(length=36), nullable=True),
        sa.Column('outstanding_fine', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('notify_email', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('notify_sms', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('notify_print', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('source_system', sa.String(length=64), nullable=True),
        sa.Column('source_id', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.ForeignKeyConstraint(['blocked_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('member_number'),
        sa.UniqueConstraint('patron_card_barcode')
    )
    op.create_index(op.f('ix_members_member_number'), 'members', ['member_number'], unique=True)
    op.create_index(op.f('ix_members_patron_card_barcode'), 'members', ['patron_card_barcode'], unique=True)
    op.create_index(op.f('ix_members_source_id'), 'members', ['source_id'])

    # Create loans table
    op.create_table(
        'loans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('member_id', sa.String(length=36), nullable=False),
        sa.Column('item_id', sa.String(length=36), nullable=False),
        sa.Column('checkout_date', sa.Date(), nullable=False, server_default=sa.text("(date('now'))")),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('return_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('renewal_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.ForeignKeyConstraint(['item_id'], ['items.id']),
        sa.ForeignKeyConstraint(['member_id'], ['members.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create renewals table
    op.create_table(
        'renewals',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('loan_id', sa.String(length=36), nullable=False),
        sa.Column('previous_due_date', sa.Date(), nullable=False),
        sa.Column('new_due_date', sa.Date(), nullable=False),
        sa.Column('renewed_by_id', sa.String(length=36), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.ForeignKeyConstraint(['loan_id'], ['loans.id']),
        sa.ForeignKeyConstraint(['renewed_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create fines table
    op.create_table(
        'fines',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('member_id', sa.String(length=36), nullable=False),
        sa.Column('loan_id', sa.String(length=36), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=False),
        sa.Column('fine_type', sa.String(length=50), nullable=False, server_default='overdue'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='unpaid'),
        sa.Column('paid_amount', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
        sa.Column('paid_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.ForeignKeyConstraint(['loan_id'], ['loans.id']),
        sa.ForeignKeyConstraint(['member_id'], ['members.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create rfid_tags table
    op.create_table(
        'rfid_tags',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tag_uid', sa.String(length=128), nullable=False),
        sa.Column('tag_type', sa.String(length=50), nullable=False, server_default='item'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('item_id', sa.String(length=36), nullable=True),
        sa.Column('encoded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.ForeignKeyConstraint(['item_id'], ['items.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tag_uid')
    )
    op.create_index(op.f('ix_rfid_tags_tag_uid'), 'rfid_tags', ['tag_uid'], unique=True)

    # Create gate_events table
    op.create_table(
        'gate_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('gate_id', sa.String(length=64), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('tag_uids', sa.JSON(), nullable=True),
        sa.Column('member_id', sa.String(length=36), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.Column('cctv_image_url', sa.String(length=512), nullable=True),
        sa.Column('is_alert', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('alert_reason', sa.Text(), nullable=True),
        sa.Column('notification_queued', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.ForeignKeyConstraint(['member_id'], ['members.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('member_id', sa.String(length=36), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=True),
        sa.Column('recipient_phone', sa.String(length=32), nullable=True),
        sa.Column('channel', sa.Enum('email', 'sms', 'print', 'system', name='notification_channel'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'queued', 'sent', 'failed', 'cancelled', name='notification_status'), nullable=False, server_default='pending'),
        sa.Column('notification_type', sa.Enum('loan_due_reminder', 'overdue_notice', 'fine_payment_required', 'item_available', 'gate_alert', 'circulation_blocked', 'account_notice', name='notification_type'), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('related_loan_id', sa.String(length=36), nullable=True),
        sa.Column('related_item_id', sa.String(length=36), nullable=True),
        sa.Column('related_gate_event_id', sa.String(length=36), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivery_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('is_system_generated', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_related_gate_event_id'), 'notifications', ['related_gate_event_id'])
    op.create_index(op.f('ix_notifications_related_item_id'), 'notifications', ['related_item_id'])
    op.create_index(op.f('ix_notifications_related_loan_id'), 'notifications', ['related_loan_id'])
    op.create_index(op.f('ix_notifications_status'), 'notifications', ['status'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('actor_id', sa.String(length=36), nullable=True),
        sa.Column('actor_username', sa.String(length=64), nullable=True),
        sa.Column('action', sa.String(length=128), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=128), nullable=True),
        sa.Column('detail', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'])
    op.create_index(op.f('ix_audit_logs_actor_id'), 'audit_logs', ['actor_id'])
    op.create_index(op.f('ix_audit_logs_resource_id'), 'audit_logs', ['resource_id'])
    op.create_index(op.f('ix_audit_logs_resource_type'), 'audit_logs', ['resource_type'])


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_logs_resource_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_resource_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_actor_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_notifications_status'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_related_loan_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_related_item_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_related_gate_event_id'), table_name='notifications')
    op.drop_table('notifications')
    op.drop_table('gate_events')
    op.drop_index(op.f('ix_rfid_tags_tag_uid'), table_name='rfid_tags')
    op.drop_table('rfid_tags')
    op.drop_table('fines')
    op.drop_table('renewals')
    op.drop_table('loans')
    op.drop_index(op.f('ix_members_source_id'), table_name='members')
    op.drop_index(op.f('ix_members_patron_card_barcode'), table_name='members')
    op.drop_index(op.f('ix_members_member_number'), table_name='members')
    op.drop_table('members')
    op.drop_index(op.f('ix_items_barcode'), table_name='items')
    op.drop_table('items')
    op.drop_table('bibliographic_records')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_smart_card_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_branches_code'), table_name='branches')
    op.drop_table('branches')
