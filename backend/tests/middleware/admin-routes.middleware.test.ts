import type { Request, Response, NextFunction } from 'express';
import { beforeEach, describe, it, expect, jest } from '@jest/globals';
import jwt from 'jsonwebtoken';
import { AppError } from '../../src/utils/AppError';

const SECRET = 'test-secret';

// Mock auth.service before importing middleware
const mockIsSessionRevoked = jest.fn<(userId: string, sessionVersion: number) => Promise<boolean>>();
jest.mock('../../src/services/auth.service', () => ({
  isSessionRevoked: mockIsSessionRevoked,
}));

// Mock env before importing middleware
jest.mock('../../src/config/env', () => ({
  getEnv: jest.fn(() => ({
    JWT_SECRET: SECRET,
    ADMIN_JWT_SECRET: SECRET,
  })),
}));

// Import after mocking
import { requireAdmin } from '../../src/middleware/admin.middleware';

function makeReqRes(authHeader?: string) {
  const req = {
    headers: authHeader ? { authorization: authHeader } : {},
  } as unknown as Request;
  const res = {} as Response;
  const next = jest.fn() as unknown as NextFunction;
  return { req, res, next };
}

describe('requireAdmin middleware for admin routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockIsSessionRevoked.mockResolvedValue(false);
  });

  describe('role check', () => {
    it('allows requests with admin role', async () => {
      const token = jwt.sign(
        { sub: 'user-123', type: 'access', sv: 0, role: 'admin' },
        SECRET,
        { expiresIn: '1h' },
      );
      const { req, res, next } = makeReqRes(`Bearer ${token}`);
      await requireAdmin(req, res, next);
      expect(next).toHaveBeenCalledWith();
      expect((req as unknown as Record<string, unknown>).userId).toBe('user-123');
    });

    it('rejects requests without role claim (user role)', async () => {
      const token = jwt.sign(
        { sub: 'user-456', type: 'access', sv: 0 },
        SECRET,
        { expiresIn: '1h' },
      );
      const { req, res, next } = makeReqRes(`Bearer ${token}`);
      await requireAdmin(req, res, next);
      const err = (next as jest.Mock).mock.calls[0][0] as AppError;
      expect(err).toBeInstanceOf(AppError);
      expect(err.statusCode).toBe(403);
      expect(err.message).toContain('admin role required');
    });

    it('rejects requests with user role', async () => {
      const token = jwt.sign(
        { sub: 'user-789', type: 'access', sv: 0, role: 'user' },
        SECRET,
        { expiresIn: '1h' },
      );
      const { req, res, next } = makeReqRes(`Bearer ${token}`);
      await requireAdmin(req, res, next);
      const err = (next as jest.Mock).mock.calls[0][0] as AppError;
      expect(err).toBeInstanceOf(AppError);
      expect(err.statusCode).toBe(403);
    });
  });

  describe('session revocation check', () => {
    it('allows request when session is not revoked', async () => {
      mockIsSessionRevoked.mockResolvedValue(false);
      const token = jwt.sign(
        { sub: 'admin-1', type: 'access', sv: 5, role: 'admin' },
        SECRET,
        { expiresIn: '1h' },
      );
      const { req, res, next } = makeReqRes(`Bearer ${token}`);
      await requireAdmin(req, res, next);
      expect(mockIsSessionRevoked).toHaveBeenCalledWith('admin-1', 5);
      expect(next).toHaveBeenCalledWith();
    });

    it('rejects request when session is revoked', async () => {
      mockIsSessionRevoked.mockResolvedValue(true);
      const token = jwt.sign(
        { sub: 'admin-2', type: 'access', sv: 3, role: 'admin' },
        SECRET,
        { expiresIn: '1h' },
      );
      const { req, res, next } = makeReqRes(`Bearer ${token}`);
      await requireAdmin(req, res, next);
      expect(mockIsSessionRevoked).toHaveBeenCalledWith('admin-2', 3);
      const err = (next as jest.Mock).mock.calls[0][0] as AppError;
      expect(err).toBeInstanceOf(AppError);
      expect(err.statusCode).toBe(401);
      expect(err.message).toContain('Session has been invalidated');
    });
  });

  describe('error handling', () => {
    it('returns 401 when Authorization header is missing', async () => {
      const { req, res, next } = makeReqRes();
      await requireAdmin(req, res, next);
      const err = (next as jest.Mock).mock.calls[0][0] as AppError;
      expect(err.statusCode).toBe(401);
    });

    it('returns 401 for expired token', async () => {
      const token = jwt.sign(
        { sub: 'admin-3', type: 'access', sv: 0, role: 'admin' },
        SECRET,
        { expiresIn: -1 },
      );
      const { req, res, next } = makeReqRes(`Bearer ${token}`);
      await requireAdmin(req, res, next);
      const err = (next as jest.Mock).mock.calls[0][0] as AppError;
      expect(err.statusCode).toBe(401);
    });

    it('returns 401 for token signed with wrong secret', async () => {
      const token = jwt.sign(
        { sub: 'admin-4', type: 'access', sv: 0, role: 'admin' },
        'wrong-secret',
        { expiresIn: '1h' },
      );
      const { req, res, next } = makeReqRes(`Bearer ${token}`);
      await requireAdmin(req, res, next);
      const err = (next as jest.Mock).mock.calls[0][0] as AppError;
      expect(err.statusCode).toBe(401);
    });

    it('returns 401 for wrong token type', async () => {
      const token = jwt.sign(
        { sub: 'admin-5', type: 'refresh', sv: 0, role: 'admin' },
        SECRET,
        { expiresIn: '1h' },
      );
      const { req, res, next } = makeReqRes(`Bearer ${token}`);
      await requireAdmin(req, res, next);
      const err = (next as jest.Mock).mock.calls[0][0] as AppError;
      expect(err.statusCode).toBe(401);
      expect(err.message).toContain('Invalid token type');
    });
  });
});
