/**
 * Integration tests for auto-lock ledger-time gating.
 *
 * Requires a running PostgreSQL test database at DATABASE_URL.
 */

import { randomUUID } from 'crypto';
import { Pool } from 'pg';
import * as fs from 'fs';
import * as path from 'path';

jest.mock('../../src/indexer/StellarIndexer', () => ({
  getLatestLedgerCloseTime: jest.fn(),
}));

process.env.DATABASE_URL =
  process.env.DATABASE_URL ?? 'postgresql://bankerchanger:bankerchanger@localhost:5433/bankerchanger_test';

// eslint-disable-next-line @typescript-eslint/no-var-requires
const { pool } = require('../../src/config/db') as { pool: Pool };
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { runAutoLockMarketsJob } = require('../../src/oracle/OracleService') as {
  runAutoLockMarketsJob: () => Promise<{ locked: number; failed: number }>;
};
import { getLatestLedgerCloseTime } from '../../src/indexer/StellarIndexer';

const SCHEMA = fs.readFileSync(path.join(__dirname, '../../db/schema.sql'), 'utf8');
const marketIds = [randomUUID(), randomUUID()];

beforeAll(async () => {
  await pool.query(SCHEMA);
  await pool.query(
    'ALTER TABLE markets ADD COLUMN IF NOT EXISTS lock_before_secs INTEGER NOT NULL DEFAULT 3600',
  );
});

beforeEach(async () => {
  await pool.query('DELETE FROM markets WHERE market_id = ANY($1)', [marketIds]);
});

afterAll(async () => {
  await pool.query('DELETE FROM markets WHERE market_id = ANY($1)', [marketIds]);
  await pool.end();
});

it('locks only after the ledger timestamp passes the threshold and 60-second grace period', async () => {
  const ledgerCloseTime = new Date('2026-10-20T12:00:00.000Z');
  (getLatestLedgerCloseTime as jest.Mock).mockResolvedValue(ledgerCloseTime);

  await pool.query(
    `INSERT INTO markets
       (market_id, contract_address, match_id, fighter_a, fighter_b, scheduled_at, lock_before_secs)
     VALUES
       ($1, 'contract-a', 'match-a', 'A', 'B', $3, 3600),
       ($2, 'contract-b', 'match-b', 'A', 'B', $4, 3600)`,
    [
      ...marketIds,
      new Date(ledgerCloseTime.getTime() + 3570 * 1000),
      new Date(ledgerCloseTime.getTime() + 3510 * 1000),
    ],
  );

  const result = await runAutoLockMarketsJob();
  const { rows } = await pool.query<{ market_id: string; status: string }>(
    'SELECT market_id, status FROM markets WHERE market_id = ANY($1) ORDER BY market_id',
    [marketIds],
  );

  expect(result).toEqual({ locked: 1, failed: 0 });
  expect(rows.map(({ status }) => status).sort()).toEqual(['locked', 'open']);
  expect(getLatestLedgerCloseTime).toHaveBeenCalledTimes(1);
});