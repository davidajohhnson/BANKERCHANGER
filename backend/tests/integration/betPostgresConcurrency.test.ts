import express from 'express';
import request from 'supertest';
import { Pool } from 'pg';
import { pool } from '../../src/config/db';
import { placeBet } from '../../src/api/controllers/BetController';
import { validateBody } from '../../src/api/middleware/validate';
import { placeBetGroup4BodySchema } from '../../src/schemas/betGroup4.schemas';
import { errorMiddleware } from '../../src/middleware/error.middleware';

jest.mock('../../src/config/db', () => ({
  pool: new (jest.requireActual('pg').Pool)({
    connectionString: process.env.BET_LOAD_DATABASE_URL,
    max: 10,
    options: `-c search_path=bet_load_${process.pid}`,
  }),
}));
jest.mock('../../src/utils/distributedLock', () => ({
  acquireLock: jest.fn().mockResolvedValue(null),
}));
jest.mock('../../src/services/cache.service', () => ({}));
jest.mock('../../src/services/StellarService', () => ({}));

// Dedicated disposable DB only: no production tables are touched.
const databaseTests = process.env.BET_LOAD_DATABASE_URL ? describe : describe.skip;
databaseTests('PostgreSQL serializable betting load', () => {
  const schema = `bet_load_${process.pid}`;
  const admin = new Pool({ connectionString: process.env.BET_LOAD_DATABASE_URL });
  const app = express();
  app.use(express.json());
  app.post('/trading/bet', validateBody(placeBetGroup4BodySchema), placeBet);
  app.use(errorMiddleware);
  const body = {
    market_id: 'load-market',
    bettor_address: 'GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWHF',
    side: 'fighter_a',
    amount: '1000',
    max_slippage_bps: 5000,
  };

  beforeAll(async () => {
    await admin.query(`CREATE SCHEMA ${schema}`);
    await pool.query(`
      CREATE TABLE markets (market_id text PRIMARY KEY, status text, total_pool numeric DEFAULT 0,
        pool_a numeric DEFAULT 0, pool_b numeric DEFAULT 0, pool_draw numeric DEFAULT 0, updated_at timestamptz);
      CREATE TABLE bets (id serial PRIMARY KEY, market_id text REFERENCES markets, bettor_address text,
        side text, amount numeric, amount_xlm numeric, tx_hash text UNIQUE, ledger_sequence integer,
        placed_at timestamptz, claimed boolean);
      INSERT INTO markets (market_id, status) VALUES ('load-market', 'open');
      CREATE FUNCTION fail_pool_update() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
        IF NEW.total_pool - OLD.total_pool = 666 THEN RAISE EXCEPTION 'forced pool update failure'; END IF;
        RETURN NEW;
      END $$;
      CREATE TRIGGER rollback_probe BEFORE UPDATE ON markets FOR EACH ROW EXECUTE FUNCTION fail_pool_update();
    `);
  });
  afterAll(async () => {
    await pool.end();
    await admin.query(`DROP SCHEMA ${schema} CASCADE`);
    await admin.end();
  });

  it('rolls back inserted bets on pool failure, then commits 50 simultaneous bets with exact pool totals', async () => {
    const failed = await request(app)
      .post('/trading/bet')
      .send({ ...body, amount: '666' });
    expect(failed.status).toBe(500);
    expect((await pool.query('SELECT COUNT(*) AS count FROM bets')).rows[0].count).toBe('0');
    expect((await pool.query('SELECT total_pool FROM markets')).rows[0].total_pool).toBe('0');

    const responses = await Promise.all(
      Array.from({ length: 50 }, (_, index) =>
        request(app)
          .post('/trading/bet')
          .send({ ...body, idempotency_key: `postgres-bet-${index}` })
      )
    );
    expect(responses.map((response) => response.status)).toEqual(Array(50).fill(201));
    expect(
      (await pool.query('SELECT COUNT(*) AS count, SUM(amount) AS amount FROM bets')).rows[0]
    ).toEqual({ count: '50', amount: '50000' });
    expect(
      (await pool.query('SELECT total_pool, pool_a, pool_b, pool_draw FROM markets')).rows[0]
    ).toEqual({ total_pool: '50000', pool_a: '50000', pool_b: '0', pool_draw: '0' });
  }, 60000);
});
