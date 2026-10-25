import express from 'express';
import request from 'supertest';
import notificationsRouter from '../../src/routes/notifications.routes';
import { pool } from '../../src/config/db';
import { redis } from '../../src/config/redis';

jest.mock('../../src/config/db', () => ({ pool: { query: jest.fn() } }));
jest.mock('../../src/config/redis', () => ({ redis: { get: jest.fn(), set: jest.fn(), del: jest.fn() } }));
jest.mock('../../src/middleware/auth.middleware', () => ({
  requireAuth: (req: any, _res: any, next: any) => { req.user = { id: req.params.userId, role: 'user' }; next(); },
}));

describe('notification settings persistence', () => {
  const app = express();
  const userId = '04da0c63-a184-40dc-a65f-6f12c375509b';
  app.use(express.json());
  app.use('/notifications', notificationsRouter);

  beforeEach(() => jest.clearAllMocks());

  it('loads persisted settings and caches them for one hour', async () => {
    (redis.get as jest.Mock).mockResolvedValue(null);
    (pool.query as jest.Mock).mockResolvedValue({ rows: [{ email_enabled: false, push_enabled: true }] });
    const response = await request(app).get(`/notifications/${userId}/settings`);
    expect(response.status).toBe(200);
    expect(response.body.settings.channel).toBe('push');
    expect(pool.query).toHaveBeenCalledWith(expect.stringContaining('FROM user_notification_settings'), [userId]);
    expect(redis.set).toHaveBeenCalledWith(expect.stringContaining(userId), expect.any(String), 'EX', 3600);
  });

  it('persists updates and invalidates the Redis cache', async () => {
    (redis.get as jest.Mock).mockResolvedValue(null);
    (pool.query as jest.Mock)
      .mockResolvedValueOnce({ rows: [{ email_enabled: true, push_enabled: true }] })
      .mockResolvedValueOnce({ rows: [{ email_enabled: true, push_enabled: false, updated_at: new Date() }] });
    const response = await request(app).put(`/notifications/${userId}/settings`).send({ channel: 'email' });
    expect(response.status).toBe(200);
    expect(pool.query).toHaveBeenLastCalledWith(expect.stringContaining('ON CONFLICT (user_id)'), [userId, true, false, expect.any(String)]);
    expect(redis.del).toHaveBeenCalledWith(expect.stringContaining(userId));
  });
});
