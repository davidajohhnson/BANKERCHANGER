import { Router } from 'express';
import { AppError } from '../../src/utils/AppError';

export function createTestHelpersRouter() {
  const app = Router();
  if (process.env.NODE_ENV !== 'test') return app;
  // Example route that throws AppError
  app.get('/test-error', (_req, _res, next) => {
    const error = AppError.notFound('Resource not found', undefined, { resource: 'user' });
    next(error);
  });

  // Example route with unhandled error
  app.get('/test-unhandled', (_req, _res) => {
    throw new Error('Unexpected error occurred');
  });

  // Example route with validation error
  app.post('/api/users', (req, res, next) => {
    if (!req.body.email) {
      const error = AppError.badRequest('Validation error', undefined, {
        field: 'email',
        reason: 'Email is required',
      });
      return next(error);
    }
    res.json({ success: true });
  });

  return app;
}
