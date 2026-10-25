import request from 'supertest';
import app from '../../src/index';
import { pool } from '../../src/config/db';
import { redis } from '../../src/config/redis';

describe('health endpoints', () => {
  beforeAll(async () => {
    await pool.query('SELECT 1');
    await redis.ping();
  });

  afterAll(async () => {
    await pool.end();
    await redis.quit();
  });

  it('returns only status and timestamp from the public health endpoint', async () => {
    const response = await request(app).get('/health');

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      status: 'healthy',
      timestamp: expect.any(String),
    });
    expect(Number.isNaN(Date.parse(response.body.timestamp))).toBe(false);
  });

  it('rejects unauthenticated requests to detailed health with 401', async () => {
    const response = await request(app).get('/health/detailed');

    expect(response.status).toBe(401);
  });
});
