/* eslint-disable camelcase */

exports.shorthands = undefined;

exports.up = (pgm) => {
  pgm.createTable('webhook_subscriptions', {
    id: { type: 'text', primaryKey: true },
    user_id: { type: 'text' },
    url: { type: 'text', notNull: true },
    secret: { type: 'text', notNull: true },
    topics: { type: 'text[]', notNull: true },
    description: { type: 'text' },
    status: { type: 'text', notNull: true, default: 'active' },
    created_at: { type: 'timestamptz', notNull: true, default: pgm.func('NOW()') },
  });
  pgm.createIndex('webhook_subscriptions', 'user_id');
  pgm.createIndex('webhook_subscriptions', 'status');

  pgm.createTable('webhook_deliveries', {
    id: { type: 'bigserial', primaryKey: true },
    webhook_id: { type: 'text', notNull: true },
    target_url: { type: 'text', notNull: true },
    signing_secret: { type: 'text', notNull: true },
    event_type: { type: 'text', notNull: true },
    event_key: { type: 'text', notNull: true },
    payload: { type: 'jsonb', notNull: true },
    status: { type: 'text', notNull: true, default: 'pending' },
    attempt_count: { type: 'integer', notNull: true, default: 0 },
    retry_count: { type: 'integer', notNull: true, default: 0 },
    next_attempt_at: { type: 'timestamptz', notNull: true, default: pgm.func('NOW()') },
    locked_at: { type: 'timestamptz' },
    last_error_response_code: { type: 'integer' },
    last_error: { type: 'text' },
    created_at: { type: 'timestamptz', notNull: true, default: pgm.func('NOW()') },
    updated_at: { type: 'timestamptz', notNull: true, default: pgm.func('NOW()') },
    delivered_at: { type: 'timestamptz' },
  });
  pgm.addConstraint('webhook_deliveries', 'webhook_deliveries_status_check', {
    check: "status IN ('pending', 'retrying', 'success', 'failed')",
  });
  pgm.addConstraint('webhook_deliveries', 'webhook_deliveries_unique_event', {
    unique: ['webhook_id', 'event_type', 'event_key'],
  });
  pgm.createIndex('webhook_deliveries', ['status', 'next_attempt_at']);
  pgm.createIndex('webhook_deliveries', 'webhook_id');
};

exports.down = (pgm) => {
  pgm.dropTable('webhook_deliveries');
  pgm.dropTable('webhook_subscriptions');
};
