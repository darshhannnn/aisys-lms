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

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'branches',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=16), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_branches_code'), 'branches', ['code'], unique=True)
    op.create_index(op.f('ix_branches_id'), 'branches', ['id'], unique=False)

    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('smart_card_id', sa.String(length=128), nullable=True),
        sa.Column('smart_card_provider', sa.String(length=64), nullable=True),
        sa.Column('role', sa.Enum('SUPER_ADMIN', 'LIBRARIAN', 'CIRCULATION_STAFF', 'CATALOGUER', 'REPORTS_VIEWER', 'OPAC_USER', name='user_role'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('branch_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('smart_card_id'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_smart_card_id'), 'users', ['smart_card_id'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    op.create_table(
        'bibliographic_records',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=1024), nullable=False),
        sa.Column('subtitle', sa.String(length=512), nullable=True),
        sa.Column('author', sa.String(length=512), nullable=True),
        sa.Column('isbn', sa.String(length=32), nullable=True),
        sa.Column('issn', sa.String(length=32), nullable=True),
        sa.Column('publisher', sa.String(length=255), nullable=True),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('edition', sa.String(length=64), nullable=True),
        sa.Column('language', sa.String(length=8), nullable=False),
        sa.Column('subject', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('dewey_class', sa.String(length=64), nullable=True),
        sa.Column('lcc_class', sa.String(length=64), nullable=True),
        sa.Column('item_type', sa.Enum('BOOK', 'JOURNAL', 'SERIAL', 'THESIS', 'MAP', 'AV', 'DIGITAL', 'OTHER', name='item_type'), nullable=False),
        sa.Column('search_vector', sa.Text(), nullable=True),
        sa.Column('source_system', sa.String(length=64), nullable=True),
        sa.Column('source_id', sa.String(length=128), nullable=True),
        sa.Column('shelf_location', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_bib_author', 'bibliographic_records', ['author'], unique=False)
    op.create_index('ix_bib_title', 'bibliographic_records', ['title'], unique=False)
    op.create_index(op.f('ix_bibliographic_records_id'), 'bibliographic_records', ['id'], unique=False)
    op.create_index(op.f('ix_bibliographic_records_isbn'), 'bibliographic_records', ['isbn'], unique=False)
    op.create_index(op.f('ix_bibliographic_records_issn'), 'bibliographic_records', ['issn'], unique=False)
    op.create_index(op.f('ix_bibliographic_records_source_id'), 'bibliographic_records', ['source_id'], unique=False)

    op.create_table(
        'members',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('member_number', sa.String(length=32), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=32), nullable=True),
        sa.Column('national_id', sa.String(length=64), nullable=True),
        sa.Column('photo_url', sa.String(length=512), nullable=True),
        sa.Column('patron_card_barcode', sa.String(length=64), nullable=True),
        sa.Column('category', sa.Enum('STUDENT', 'FACULTY', 'STAFF', 'EXTERNAL', 'HONORARY', name='member_category'), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'BLOCKED', 'SUSPENDED', 'EXPIRED', 'CANCELLED', name='member_status'), nullable=False),
        sa.Column('membership_start', sa.Date(), nullable=True),
        sa.Column('membership_end', sa.Date(), nullable=True),
        sa.Column('block_reason', sa.Text(), nullable=True),
        sa.Column('blocked_by_id', sa.Uuid(), nullable=True),
        sa.Column('outstanding_fine', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('notify_email', sa.Boolean(), nullable=False),
        sa.Column('notify_sms', sa.Boolean(), nullable=False),
        sa.Column('notify_print', sa.Boolean(), nullable=False),
        sa.Column('source_system', sa.String(length=64), nullable=True),
        sa.Column('source_id', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['blocked_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('member_number'),
        sa.UniqueConstraint('patron_card_barcode')
    )
    op.create_index(op.f('ix_members_id'), 'members', ['id'], unique=False)
    op.create_index(op.f('ix_members_member_number'), 'members', ['member_number'], unique=True)
    op.create_index(op.f('ix_members_patron_card_barcode'), 'members', ['patron_card_barcode'], unique=True)
    op.create_index(op.f('ix_members_source_id'), 'members', ['source_id'], unique=False)

    op.create_table(
        'items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('bibliographic_record_id', sa.Uuid(), nullable=False),
        sa.Column('accession_number', sa.String(length=64), nullable=False),
        sa.Column('barcode', sa.String(length=64), nullable=True),
        sa.Column('spine_label', sa.String(length=64), nullable=True),
        sa.Column('location', sa.String(length=128), nullable=True),
        sa.Column('status', sa.Enum('AVAILABLE', 'CHECKED_OUT', 'RESERVED', 'LOST', 'DAMAGED', 'IN_TRANSIT', 'REFERENCE_ONLY', 'WITHDRAWN', name='item_status'), nullable=False),
        sa.Column('is_reference', sa.Boolean(), nullable=False),
        sa.Column('branch_id', sa.Uuid(), nullable=True),
        sa.Column('acquisition_status', sa.Enum('ORDERED', 'RECEIVED', 'CATALOGUED', 'PROCESSED', name='acquisition_status'), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('vendor', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['bibliographic_record_id'], ['bibliographic_records.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('accession_number'),
        sa.UniqueConstraint('barcode')
    )
    op.create_index(op.f('ix_items_accession_number'), 'items', ['accession_number'], unique=True)
    op.create_index(op.f('ix_items_barcode'), 'items', ['barcode'], unique=True)
    op.create_index(op.f('ix_items_bibliographic_record_id'), 'items', ['bibliographic_record_id'], unique=False)
    op.create_index(op.f('ix_items_branch_id'), 'items', ['branch_id'], unique=False)
    op.create_index(op.f('ix_items_id'), 'items', ['id'], unique=False)

    op.create_table(
        'inventory_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('operator_id', sa.Uuid(), nullable=True),
        sa.Column('shelf_range', sa.String(length=255), nullable=False),
        sa.Column('device_id', sa.String(length=64), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_expected', sa.Integer(), nullable=True),
        sa.Column('total_scanned', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['operator_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_sessions_id'), 'inventory_sessions', ['id'], unique=False)

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('actor_id', sa.Uuid(), nullable=True),
        sa.Column('actor_username', sa.String(length=64), nullable=True),
        sa.Column('action', sa.String(length=128), nullable=False),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('resource_id', sa.String(length=128), nullable=True),
        sa.Column('detail', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_actor_id'), 'audit_logs', ['actor_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_id'), 'audit_logs', ['resource_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_type'), 'audit_logs', ['resource_type'], unique=False)

    op.create_table(
        'loans',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('member_id', sa.Uuid(), nullable=False),
        sa.Column('item_id', sa.Uuid(), nullable=False),
        sa.Column('issued_by_id', sa.Uuid(), nullable=True),
        sa.Column('returned_by_id', sa.Uuid(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'RETURNED', 'OVERDUE', 'LOST', 'RENEWED', name='loan_status'), nullable=False),
        sa.Column('issued_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('returned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('renewals_count', sa.Integer(), nullable=False),
        sa.Column('protocol', sa.String(length=16), nullable=True),
        sa.Column('protocol_transaction_id', sa.String(length=128), nullable=True),
        sa.Column('block_reason', sa.Enum('MEMBER_BLOCKED', 'REFERENCE_ITEM', 'FINE_LIMIT_EXCEEDED', 'MEMBERSHIP_EXPIRED', 'ITEM_NOT_AVAILABLE', 'MAX_LOANS_REACHED', name='circ_block_reason'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['issued_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['returned_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_loans_id'), 'loans', ['id'], unique=False)
    op.create_index(op.f('ix_loans_item_id'), 'loans', ['item_id'], unique=False)
    op.create_index(op.f('ix_loans_member_id'), 'loans', ['member_id'], unique=False)

    op.create_table(
        'rfid_tags',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tag_uid', sa.String(length=128), nullable=False),
        sa.Column('item_id', sa.Uuid(), nullable=True),
        sa.Column('member_id', sa.Uuid(), nullable=True),
        sa.Column('tag_type', sa.String(length=16), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'DEACTIVATED', 'LOST', 'DAMAGED', name='tag_status'), nullable=False),
        sa.Column('security_bit', sa.Boolean(), nullable=False),
        sa.Column('last_seen_reader', sa.String(length=64), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tagged_by_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tagged_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tag_uid')
    )
    op.create_index(op.f('ix_rfid_tags_id'), 'rfid_tags', ['id'], unique=False)
    op.create_index(op.f('ix_rfid_tags_item_id'), 'rfid_tags', ['item_id'], unique=False)
    op.create_index(op.f('ix_rfid_tags_member_id'), 'rfid_tags', ['member_id'], unique=False)
    op.create_index(op.f('ix_rfid_tags_tag_uid'), 'rfid_tags', ['tag_uid'], unique=True)

    op.create_table(
        'gate_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('event_type', sa.Enum('AUTHORISED_EXIT', 'UNAUTHORISED_EXIT', 'UNISSUED_ITEM', 'ALARM_TRIGGERED', 'FOOTFALL_ENTRY', 'FOOTFALL_EXIT', name='gate_event_type'), nullable=False),
        sa.Column('gate_id', sa.String(length=64), nullable=False),
        sa.Column('tag_uid', sa.String(length=128), nullable=True),
        sa.Column('accession_number', sa.String(length=64), nullable=True),
        sa.Column('member_id', sa.Uuid(), nullable=True),
        sa.Column('is_alert', sa.Boolean(), nullable=False),
        sa.Column('alert_reason', sa.Text(), nullable=True),
        sa.Column('cctv_image_path', sa.String(length=512), nullable=True),
        sa.Column('notification_queued', sa.Boolean(), nullable=False),
        sa.Column('notification_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('raw_payload', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gate_events_accession_number'), 'gate_events', ['accession_number'], unique=False)
    op.create_index(op.f('ix_gate_events_id'), 'gate_events', ['id'], unique=False)
    op.create_index(op.f('ix_gate_events_is_alert'), 'gate_events', ['is_alert'], unique=False)
    op.create_index(op.f('ix_gate_events_member_id'), 'gate_events', ['member_id'], unique=False)
    op.create_index(op.f('ix_gate_events_tag_uid'), 'gate_events', ['tag_uid'], unique=False)

    op.create_table(
        'notifications',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('member_id', sa.Uuid(), nullable=True),
        sa.Column('recipient_email', sa.String(length=255), nullable=True),
        sa.Column('recipient_phone', sa.String(length=32), nullable=True),
        sa.Column('channel', sa.Enum('EMAIL', 'SMS', 'PRINT', 'SYSTEM', name='notification_channel'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'QUEUED', 'SENT', 'FAILED', 'CANCELLED', name='notification_status'), nullable=False),
        sa.Column('notification_type', sa.Enum('LOAN_DUE_REMINDER', 'OVERDUE_NOTICE', 'FINE_PAYMENT_REQUIRED', 'ITEM_AVAILABLE', 'GATE_ALERT', 'CIRCULATION_BLOCKED', 'ACCOUNT_NOTICE', name='notification_type'), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('related_loan_id', sa.Uuid(), nullable=True),
        sa.Column('related_item_id', sa.Uuid(), nullable=True),
        sa.Column('related_gate_event_id', sa.Uuid(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivery_attempts', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('is_system_generated', sa.Boolean(), nullable=False),
        sa.Column('notification_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_member_id'), 'notifications', ['member_id'], unique=False)
    op.create_index(op.f('ix_notifications_notification_type'), 'notifications', ['notification_type'], unique=False)
    op.create_index(op.f('ix_notifications_related_gate_event_id'), 'notifications', ['related_gate_event_id'], unique=False)
    op.create_index(op.f('ix_notifications_related_item_id'), 'notifications', ['related_item_id'], unique=False)
    op.create_index(op.f('ix_notifications_related_loan_id'), 'notifications', ['related_loan_id'], unique=False)
    op.create_index(op.f('ix_notifications_status'), 'notifications', ['status'], unique=False)

    op.create_table(
        'renewals',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('loan_id', sa.Uuid(), nullable=False),
        sa.Column('renewed_by_id', sa.Uuid(), nullable=True),
        sa.Column('renewed_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('previous_due_date', sa.Date(), nullable=False),
        sa.Column('new_due_date', sa.Date(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['loan_id'], ['loans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['renewed_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_renewals_id'), 'renewals', ['id'], unique=False)
    op.create_index(op.f('ix_renewals_loan_id'), 'renewals', ['loan_id'], unique=False)

    op.create_table(
        'fines',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('member_id', sa.Uuid(), nullable=False),
        sa.Column('loan_id', sa.Uuid(), nullable=True),
        sa.Column('levied_by_id', sa.Uuid(), nullable=True),
        sa.Column('waived_by_id', sa.Uuid(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('UNPAID', 'PARTIAL', 'PAID', 'WAIVED', name='fine_status'), nullable=False),
        sa.Column('paid_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('paid_date', sa.Date(), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('waive_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['levied_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['loan_id'], ['loans.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['waived_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fines_id'), 'fines', ['id'], unique=False)
    op.create_index(op.f('ix_fines_loan_id'), 'fines', ['loan_id'], unique=False)
    op.create_index(op.f('ix_fines_member_id'), 'fines', ['member_id'], unique=False)

    op.create_table(
        'inventory_scans',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('session_id', sa.Uuid(), nullable=False),
        sa.Column('tag_uid', sa.String(length=128), nullable=True),
        sa.Column('accession_number', sa.String(length=64), nullable=True),
        sa.Column('expected_shelf', sa.String(length=128), nullable=True),
        sa.Column('scanned_shelf', sa.String(length=128), nullable=True),
        sa.Column('result', sa.Enum('PRESENT', 'MISSING', 'MISPLACED', 'EXTRA', name='inventory_result'), nullable=False),
        sa.Column('scanned_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['inventory_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_scans_id'), 'inventory_scans', ['id'], unique=False)
    op.create_index(op.f('ix_inventory_scans_session_id'), 'inventory_scans', ['session_id'], unique=False)
    op.create_index(op.f('ix_inventory_scans_tag_uid'), 'inventory_scans', ['tag_uid'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_inventory_scans_tag_uid'), table_name='inventory_scans')
    op.drop_index(op.f('ix_inventory_scans_session_id'), table_name='inventory_scans')
    op.drop_index(op.f('ix_inventory_scans_id'), table_name='inventory_scans')
    op.drop_table('inventory_scans')

    op.drop_index(op.f('ix_fines_member_id'), table_name='fines')
    op.drop_index(op.f('ix_fines_loan_id'), table_name='fines')
    op.drop_index(op.f('ix_fines_id'), table_name='fines')
    op.drop_table('fines')

    op.drop_index(op.f('ix_renewals_loan_id'), table_name='renewals')
    op.drop_index(op.f('ix_renewals_id'), table_name='renewals')
    op.drop_table('renewals')

    op.drop_index(op.f('ix_notifications_status'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_related_loan_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_related_item_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_related_gate_event_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_notification_type'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_member_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')

    op.drop_index(op.f('ix_gate_events_tag_uid'), table_name='gate_events')
    op.drop_index(op.f('ix_gate_events_member_id'), table_name='gate_events')
    op.drop_index(op.f('ix_gate_events_is_alert'), table_name='gate_events')
    op.drop_index(op.f('ix_gate_events_id'), table_name='gate_events')
    op.drop_index(op.f('ix_gate_events_accession_number'), table_name='gate_events')
    op.drop_table('gate_events')

    op.drop_index(op.f('ix_rfid_tags_tag_uid'), table_name='rfid_tags')
    op.drop_index(op.f('ix_rfid_tags_member_id'), table_name='rfid_tags')
    op.drop_index(op.f('ix_rfid_tags_item_id'), table_name='rfid_tags')
    op.drop_index(op.f('ix_rfid_tags_id'), table_name='rfid_tags')
    op.drop_table('rfid_tags')

    op.drop_index(op.f('ix_loans_member_id'), table_name='loans')
    op.drop_index(op.f('ix_loans_item_id'), table_name='loans')
    op.drop_index(op.f('ix_loans_id'), table_name='loans')
    op.drop_table('loans')

    op.drop_index(op.f('ix_audit_logs_resource_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_resource_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_actor_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_index(op.f('ix_inventory_sessions_id'), table_name='inventory_sessions')
    op.drop_table('inventory_sessions')

    op.drop_index(op.f('ix_items_id'), table_name='items')
    op.drop_index(op.f('ix_items_branch_id'), table_name='items')
    op.drop_index(op.f('ix_items_bibliographic_record_id'), table_name='items')
    op.drop_index(op.f('ix_items_barcode'), table_name='items')
    op.drop_index(op.f('ix_items_accession_number'), table_name='items')
    op.drop_table('items')

    op.drop_index(op.f('ix_members_source_id'), table_name='members')
    op.drop_index(op.f('ix_members_patron_card_barcode'), table_name='members')
    op.drop_index(op.f('ix_members_member_number'), table_name='members')
    op.drop_index(op.f('ix_members_id'), table_name='members')
    op.drop_table('members')

    op.drop_index(op.f('ix_bibliographic_records_source_id'), table_name='bibliographic_records')
    op.drop_index(op.f('ix_bibliographic_records_issn'), table_name='bibliographic_records')
    op.drop_index(op.f('ix_bibliographic_records_isbn'), table_name='bibliographic_records')
    op.drop_index(op.f('ix_bibliographic_records_id'), table_name='bibliographic_records')
    op.drop_index('ix_bib_title', table_name='bibliographic_records')
    op.drop_index('ix_bib_author', table_name='bibliographic_records')
    op.drop_table('bibliographic_records')

    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_smart_card_id'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    op.drop_index(op.f('ix_branches_id'), table_name='branches')
    op.drop_index(op.f('ix_branches_code'), table_name='branches')
    op.drop_table('branches')
