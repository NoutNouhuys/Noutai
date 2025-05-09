"""
Migration script to rename the 'metadata' column to 'message_metadata' in the messages table.

This migration should be run using Flask-Migrate:
flask db migrate -m "Rename metadata column to message_metadata"
flask db upgrade
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Perform the upgrade migration."""
    # Rename metadata column to message_metadata in messages table
    with op.batch_alter_table('messages') as batch_op:
        batch_op.alter_column('metadata', new_column_name='message_metadata')


def downgrade():
    """Perform the downgrade migration."""
    # Rename message_metadata column back to metadata in messages table
    with op.batch_alter_table('messages') as batch_op:
        batch_op.alter_column('message_metadata', new_column_name='metadata')
