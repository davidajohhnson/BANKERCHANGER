import express from 'express';
import request from 'supertest';
import { createTestHelpersRouter } from './routes/test-helpers.routes';
import { errorMiddleware } from '../src/middleware/error.middleware';

it.each(['production', 'development', 'test'])(
  'exposes fixtures only in test (%s)',
  async (environment) => {
    const previous = process.env.NODE_ENV;
    try {
      process.env.NODE_ENV = environment;
      const app = express();
      app.use(express.json(), createTestHelpersRouter(), errorMiddleware);
      const response = await request(app).get('/test-error');
      expect(response.status).toBe(404);
      if (environment === 'test') expect(response.body.error.details).toEqual({ resource: 'user' });
      else expect(response.body.error).toBeUndefined();
      const user = await request(app).post('/api/users').send({ email: 'fixture@example.com' });
      expect(user.status).toBe(environment === 'test' ? 200 : 404);
    } finally {
      process.env.NODE_ENV = previous;
    }
  }
);
