/* eslint-disable camelcase */

exports.shorthands = undefined;

exports.up = (pgm) => {
  pgm.createTable('user_sessions', {
    id: { type: 'serial', primaryKey: true },
    user_id: { type: 'text', notNull: true },
    session_token: { type: 'text', notNull: true, unique: true },
    expires_at: { type: 'timestamptz', notNull: true },
    created_at: { type: 'timestamptz', notNull: true, default: pgm.func('NOW()') },
  });
  pgm.createIndex('user_sessions', 'user_id');
  pgm.createIndex('user_sessions', 'expires_at');

  pgm.createTable('password_reset_tokens', {
    id: { type: 'serial', primaryKey: true },
    user_id: { type: 'text', notNull: true },
    token_hash: { type: 'text', notNull: true, unique: true },
    expires_at: { type: 'timestamptz', notNull: true },
    created_at: { type: 'timestamptz', notNull: true, default: pgm.func('NOW()') },
  });
  pgm.createIndex('password_reset_tokens', 'user_id');
  pgm.createIndex('password_reset_tokens', 'expires_at');

  // This table is part of the application schema but was missing from the
  // initial migration. Keep existing installations intact while allowing a
  // fresh database to apply the migration chain.
  pgm.sql(`CREATE TABLE IF NOT EXISTS notification_jobs (
    id serial PRIMARY KEY,
    bettor_address text NOT NULL,
    market_id text NOT NULL REFERENCES markets(market_id),
    job_type text NOT NULL,
    status text DEFAULT 'pending',
    created_at timestamptz DEFAULT NOW(),
    processed_at timestamptz
  )`);
  pgm.createIndex('notification_jobs', 'market_id', { name: 'notification_jobs_market_id_idx', ifNotExists: true });
  pgm.createIndex('notification_jobs', 'status', { name: 'notification_jobs_status_idx', ifNotExists: true });

  pgm.addColumn('notification_jobs', {
    deleted_at: { type: 'timestamptz' },
  });

  pgm.createTable('distributions', {
    id: { type: 'serial', primaryKey: true },
    market_id: { type: 'text', notNull: true, references: 'markets(market_id)' },
    bettor_address: { type: 'text', notNull: true },
    amount: { type: 'numeric', notNull: true },
    status: { type: 'text', notNull: true, default: 'pending' },
    tx_hash: { type: 'text' },
    archived_at: { type: 'timestamptz' },
    created_at: { type: 'timestamptz', notNull: true, default: pgm.func('NOW()') },
    updated_at: { type: 'timestamptz', notNull: true, default: pgm.func('NOW()') },
  });
  pgm.createIndex('distributions', 'market_id');
  pgm.createIndex('distributions', 'status');
  pgm.createIndex('distributions', 'created_at');
};

exports.down = (pgm) => {
  pgm.dropTable('distributions');
  pgm.dropColumn('notification_jobs', 'deleted_at');
  pgm.dropTable('user_sessions');
};
