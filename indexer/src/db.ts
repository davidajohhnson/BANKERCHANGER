import path from 'path';
import fs from 'fs/promises';

const dbPath = path.join(__dirname, '../data');
const cursorFilePath = path.join(dbPath, 'cursor.json');

// Lazy database instance - only created when first accessed
let dbInstance: Database.Database | null = null;
let pgPool: Pool | null = null;

export function getPgPool(): Pool | null {
  if (pgPool) return pgPool;
  const connectionString = process.env.DATABASE_URL;
  if (!connectionString) return null;

  pgPool = new Pool({
    connectionString,
    max: 10,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
  });

  pgPool.on('error', (err) => {
    console.error('[Indexer Postgres Pool Error]', err);
  });

  return pgPool;
}

export async function saveCursorPg(cursor: string, ledger?: number): Promise<void> {
  const pool = getPgPool();
  if (!pool) return;
  await pool.query(
    `INSERT INTO indexer_checkpoints (id, cursor, last_ledger, updated_at)
     VALUES ('default', $1, $2, NOW())
     ON CONFLICT (id) DO UPDATE SET
       cursor = EXCLUDED.cursor,
       last_ledger = EXCLUDED.last_ledger,
       updated_at = EXCLUDED.updated_at`,
    [cursor, ledger ?? null],
  );
}

export async function getCursorPg(): Promise<string | null> {
  const pool = getPgPool();
  if (!pool) return null;
  const res = await pool.query(`SELECT cursor FROM indexer_checkpoints WHERE id = 'default' LIMIT 1`);
  return res.rows[0]?.cursor ?? null;
}

/** Initialize database directory asynchronously */
async function initializeDataDir() {
  try {
    await fs.mkdir(dbPath, { recursive: true });
  } catch (err) {
    console.error('Failed to create data directory:', err);
    throw err;
  }
}

/**
 * Get or initialize the database instance (lazy singleton).
 * In test environments, this allows mocking/resetting the database.
 * In production, creates a single connection pool.
 *
 * To reset the database in tests: call `db.exec('DELETE FROM ...')` or
 * set `process.env.DATABASE_INSTANCE = null` to force re-initialization.
 */
function getDb(): Database.Database {
  if (dbInstance) return dbInstance;

// Async cursor persistence using file system
export async function getCursor(): Promise<string | null> {
  try {
    const database = getDb();
    const row = database.prepare('SELECT paging_token FROM indexer_cursor WHERE id = ?').get('current_cursor') as any;
    if (row?.paging_token) {
      return row.paging_token;
    }
  } catch {
    // Fall back to file if table read fails
  }

  try {
    const data = await fs.readFile(cursorFilePath, 'utf-8');
    const parsed = JSON.parse(data);
    return parsed.paging_token || null;
  } catch (err: any) {
    if (err.code === 'ENOENT') {
      return null;
    }
    console.error('Error reading cursor from file:', err);
    return null;
  }
}

export async function saveCursor(pagingToken: string, lastLedger?: number): Promise<void> {
  // Preserve lastLedger from prior save if not supplied
  let existingLedger: number | undefined;
  if (lastLedger === undefined) {
    existingLedger = (await getLastKnownLedger()) ?? undefined;
  }

  const effectiveLedger = lastLedger ?? existingLedger ?? null;

  try {
    const database = getDb();
    database.prepare(`
      INSERT INTO indexer_cursor (id, paging_token, last_ledger, updated_at)
      VALUES ('current_cursor', ?, ?, ?)
      ON CONFLICT(id) DO UPDATE SET
        paging_token = excluded.paging_token,
        last_ledger = excluded.last_ledger,
        updated_at = excluded.updated_at
    `).run(pagingToken, effectiveLedger, new Date().toISOString());
  } catch (dbErr) {
    console.error('Failed to save cursor to SQLite table:', dbErr);
  }

  try {
    const cursorData = {
      paging_token: pagingToken,
      last_ledger: effectiveLedger,
      updated_at: new Date().toISOString(),
    };
    await fs.writeFile(cursorFilePath, JSON.stringify(cursorData, null, 2), 'utf-8');
  } catch (err) {
    console.error('Error saving cursor to file:', err);
    throw err;
  }
}
