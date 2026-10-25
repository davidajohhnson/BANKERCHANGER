/* eslint-disable camelcase */

exports.shorthands = undefined;

exports.up = (pgm) => {
  pgm.createTable('user_notification_settings', {
    user_id: { type: 'text', primaryKey: true, references: 'users(id)', onDelete: 'CASCADE' },
    email_enabled: { type: 'boolean', notNull: true, default: true },
    push_enabled: { type: 'boolean', notNull: true, default: true },
    settings: { type: 'jsonb', notNull: true, default: pgm.func("'{}'::jsonb") },
    created_at: { type: 'timestamptz', notNull: true, default: pgm.func('NOW()') },
    updated_at: { type: 'timestamptz', notNull: true, default: pgm.func('NOW()') },
  });
};

exports.down = (pgm) => {
  pgm.dropTable('user_notification_settings');
};
