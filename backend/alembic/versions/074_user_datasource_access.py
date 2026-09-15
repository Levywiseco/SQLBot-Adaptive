'''Add user-level datasource access assignments.

Revision ID: c91f40a73b02
Revises: b82d1e7a3001
Create Date: 2026-09-15
'''

from alembic import op
import sqlalchemy as sa


revision = 'c91f40a73b02'
down_revision = 'b82d1e7a3001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'sys_user_datasource',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('uid', sa.BigInteger(), nullable=False),
        sa.Column('datasource_id', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['uid'], ['sys_user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['datasource_id'], ['core_datasource.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uid', 'datasource_id', name='uq_sys_user_datasource_uid_ds'),
    )
    op.create_index('ix_sys_user_datasource_uid', 'sys_user_datasource', ['uid'])
    op.create_index(
        'ix_sys_user_datasource_datasource_id',
        'sys_user_datasource',
        ['datasource_id'],
    )

    # Preserve current behavior for existing users. New users are assigned explicitly.
    op.execute(
        '''
        INSERT INTO sys_user_datasource (id, uid, datasource_id)
        WITH access AS (
            SELECT uw.uid, ds.id AS datasource_id
            FROM sys_user_ws uw
            JOIN core_datasource ds ON ds.oid = uw.oid
            WHERE uw.uid <> 1
            UNION
            SELECT usr.id AS uid, ds.id AS datasource_id
            FROM sys_user usr
            JOIN core_datasource ds ON ds.oid = usr.oid
            WHERE usr.id <> 1
        )
        SELECT
            (EXTRACT(EPOCH FROM clock_timestamp()) * 1000000)::bigint
              + ROW_NUMBER() OVER (ORDER BY uid, datasource_id),
            uid,
            datasource_id
        FROM access
        ON CONFLICT (uid, datasource_id) DO NOTHING
        '''
    )


def downgrade():
    op.drop_index('ix_sys_user_datasource_datasource_id', table_name='sys_user_datasource')
    op.drop_index('ix_sys_user_datasource_uid', table_name='sys_user_datasource')
    op.drop_table('sys_user_datasource')
