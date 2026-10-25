import express from 'express';
import request from 'supertest';
import { pool } from '../src/config/db';
import { defaultDbAdapter } from '../src/services/MarketService';
import { errorMiddleware } from '../src/middleware/error.middleware';
import { requestLogging } from '../src/middleware/request-logging.middleware';
import { logger } from '../src/utils/logger';

jest.mock('../src/config/db', () => ({ pool: { query: jest.fn() } }));
jest.mock('../src/services/cache.service', () => ({}));
jest.mock('../src/services/StellarService', () => ({}));
jest.mock('../src/utils/logger', () => ({ logger: { error: jest.fn(), info: jest.fn() } }));

it.each([
  ['42703', 500, 'DATABASE_ERROR'],
  ['23505', 409, 'DATABASE_UNIQUE_CONFLICT'],
  ['23503', 409, 'DATABASE_CONSTRAINT_CONFLICT'],
  ['23P01', 409, 'DATABASE_CONSTRAINT_CONFLICT'],
])(
  'sanitizes PostgreSQL %s while preserving request context internally',
  async (code, status, publicCode) => {
    const err = Object.assign(
      new Error('secret_column violates markets_private_constraint SELECT * FROM secret_table'),
      { code }
    );
    (pool.query as jest.Mock).mockRejectedValueOnce(err);
    const app = express();
    app.use(requestLogging);
    app.get('/', async (_req, res, next) => {
      try {
        res.json(await defaultDbAdapter.findMarkets());
      } catch (error) {
        next(error);
      }
    });
    app.use(errorMiddleware);
    const response = await request(app).get('/');
    expect(response.status).toBe(status);
    expect(response.body.error.code).toBe(publicCode);
    expect(JSON.stringify(response.body)).not.toMatch(/secret|constraint|SELECT|stack/);
    expect(logger.error).toHaveBeenCalledWith(
      expect.objectContaining({ err, requestId: expect.any(String) }),
      'Market database query failed'
    );
  }
);
