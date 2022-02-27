"""base test1

Revision ID: c14cd10a3527
Revises: 
Create Date: 2022-02-27 17:16:31.539860

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c14cd10a3527'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('badgecategory',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('detainedusers',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('role_ids', sa.JSON(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('start', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end', sa.DateTime(timezone=True), nullable=False),
    sa.Column('hosts', sa.JSON(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('officers',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('started_monitoring', sa.DateTime(timezone=True), nullable=False),
    sa.Column('vrchat_name', sa.String(length=255), nullable=False),
    sa.Column('vrchat_id', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('savedvoicechannels',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('guild_id', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('trainingcategories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('team', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('badges',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('category', sa.Integer(), nullable=True),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(length=65536), nullable=False),
    sa.ForeignKeyConstraint(['category'], ['badgecategory.id'], name='fk_badges_badgecategory_id_category'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('calls',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event', sa.Integer(), nullable=True),
    sa.Column('squad', sa.BigInteger(), nullable=True),
    sa.Column('type', sa.String(length=10), nullable=False),
    sa.ForeignKeyConstraint(['event'], ['events.id'], name='fk_calls_events_id_event'),
    sa.ForeignKeyConstraint(['squad'], ['savedvoicechannels.id'], name='fk_calls_savedvoicechannels_id_squad'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('loaentries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('officer', sa.BigInteger(), nullable=True),
    sa.Column('start', sa.Date(), nullable=False),
    sa.Column('end', sa.Date(), nullable=False),
    sa.Column('message_id', sa.BigInteger(), nullable=False),
    sa.Column('channel_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['officer'], ['officers.id'], name='fk_loaentries_officers_id_officer'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('patrols',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('officer', sa.BigInteger(), nullable=True),
    sa.Column('start', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end', sa.DateTime(timezone=True), nullable=False),
    sa.Column('event', sa.Integer(), nullable=True),
    sa.Column('main_channel', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['event'], ['events.id'], name='fk_patrols_events_id_event'),
    sa.ForeignKeyConstraint(['main_channel'], ['savedvoicechannels.id'], name='fk_patrols_savedvoicechannels_id_main_channel'),
    sa.ForeignKeyConstraint(['officer'], ['officers.id'], name='fk_patrols_officers_id_officer'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('strikeentries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('member_id', sa.BigInteger(), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.Column('reason', sa.String(length=65536), nullable=False),
    sa.Column('submitter', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['submitter'], ['officers.id'], name='fk_strikeentries_officers_id_submitter'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('timerenewals',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('officer', sa.BigInteger(), nullable=True),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.Column('renewer', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['officer'], ['officers.id'], name='fk_timerenewals_officers_id_officer'),
    sa.ForeignKeyConstraint(['renewer'], ['officers.id'], name='fk_timerenewals_officers_id_renewer'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('trainings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('category', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.ForeignKeyConstraint(['category'], ['trainingcategories.id'], name='fk_trainings_trainingcategories_id_category'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('calls_officers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('officer', sa.BigInteger(), nullable=True),
    sa.Column('call', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['call'], ['calls.id'], name='fk_calls_officers_calls_call_id', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['officer'], ['officers.id'], name='fk_calls_officers_officers_officer_id', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('officers_badges_owned',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('badge_id_owned', sa.Integer(), nullable=True),
    sa.Column('officer_id_owned', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['badge_id_owned'], ['badges.id'], name='fk_officers_badges_owned_badges_badge_id_owned_id', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['officer_id_owned'], ['officers.id'], name='fk_officers_badges_owned_officers_officer_id_owned_id', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('officers_badges_pending',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('badge_id_pending', sa.Integer(), nullable=True),
    sa.Column('officer_id_pending', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['badge_id_pending'], ['badges.id'], name='fk_officers_badges_pending_badges_badge_id_pending_id', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['officer_id_pending'], ['officers.id'], name='fk_officers_badges_pending_officers_officer_id_pending_id', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('officers_trainings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('training', sa.Integer(), nullable=True),
    sa.Column('officer', sa.BigInteger(), nullable=True),
    sa.ForeignKeyConstraint(['officer'], ['officers.id'], name='fk_officers_trainings_officers_officer_id', onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['training'], ['trainings.id'], name='fk_officers_trainings_trainings_training_id', onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('patrolvoices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('patrol', sa.Integer(), nullable=True),
    sa.Column('channel', sa.BigInteger(), nullable=True),
    sa.Column('start', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['channel'], ['savedvoicechannels.id'], name='fk_patrolvoices_savedvoicechannels_id_channel'),
    sa.ForeignKeyConstraint(['patrol'], ['patrols.id'], name='fk_patrolvoices_patrols_id_patrol'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('vrclocations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('instance_id', sa.Integer(), nullable=False),
    sa.Column('vrc_world_name', sa.String(length=65536), nullable=False),
    sa.Column('vrc_world_id', sa.String(length=65536), nullable=False),
    sa.Column('invite_token', sa.String(length=65536), nullable=False),
    sa.Column('instance_access_type', sa.String(length=100), nullable=False),
    sa.Column('start', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end', sa.DateTime(timezone=True), nullable=False),
    sa.Column('patrol', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['patrol'], ['patrols.id'], name='fk_vrclocations_patrols_id_patrol'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('vrclocations')
    op.drop_table('patrolvoices')
    op.drop_table('officers_trainings')
    op.drop_table('officers_badges_pending')
    op.drop_table('officers_badges_owned')
    op.drop_table('calls_officers')
    op.drop_table('trainings')
    op.drop_table('timerenewals')
    op.drop_table('strikeentries')
    op.drop_table('patrols')
    op.drop_table('loaentries')
    op.drop_table('calls')
    op.drop_table('badges')
    op.drop_table('trainingcategories')
    op.drop_table('savedvoicechannels')
    op.drop_table('officers')
    op.drop_table('events')
    op.drop_table('detainedusers')
    op.drop_table('badgecategory')
    # ### end Alembic commands ###
