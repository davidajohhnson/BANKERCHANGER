/* eslint-disable camelcase */

exports.shorthands = undefined;

exports.up = (pgm) => {
  pgm.sql(`CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id serial PRIMARY KEY,
    user_id text NOT NULL,
    token_hash text UNIQUE NOT NULL,
    expires_at timestamptz NOT NULL,
    created_at timestamptz DEFAULT NOW() NOT NULL
  )`);
  pgm.sql('CREATE INDEX IF NOT EXISTS password_reset_tokens_user_id_index ON password_reset_tokens (user_id)');
  pgm.sql('CREATE INDEX IF NOT EXISTS password_reset_tokens_expires_at_index ON password_reset_tokens (expires_at)');
};

exports.down = (pgm) => {
  pgm.dropTable('password_reset_tokens');
};
