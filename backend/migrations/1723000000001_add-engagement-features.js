/* eslint-disable camelcase */

exports.shorthands = undefined;

// The later engagement migration (1750000000000) owns the streak, achievement,
// and referral tables. This migration creates the separate notification table.
exports.up = (pgm) => {
  pgm.createTable('user_notifications', {
    id: { type: 'serial', primaryKey: true },
    address: { type: 'text', notNull: true },
    type: { type: 'text', notNull: true },
    title: { type: 'text', notNull: true },
    body: { type: 'text', notNull: true },
    payload: { type: 'jsonb', notNull: true, default: '{}' },
    read: { type: 'boolean', notNull: true, default: false },
    created_at: { type: 'timestamptz', notNull: true, default: pgm.func('NOW()') },
  });
  pgm.createIndex('user_notifications', 'address');
  pgm.createIndex('user_notifications', 'read');
};

exports.down = (pgm) => {
  pgm.dropTable('user_notifications');
};
