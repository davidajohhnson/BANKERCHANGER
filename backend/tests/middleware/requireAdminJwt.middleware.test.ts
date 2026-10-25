import type { Request, Response, NextFunction } from 'express';
import { beforeEach, describe, it, expect, jest } from '@jest/globals';
import jwt from 'jsonwebtoken';
import { AppError } from '../../src/utils/AppError';

const SECRET = 'test-secret-with-at-least-32-bytes';
const mockIsSessionRevoked = jest.fn<(userId: string, sessionVersion: number) => Promise<boolean>>();

jest.mock('../../src/config/env', () => ({
  getEnv: jest.fn(() => ({ JWT_SECRET: SECRET, JWT_ACCESS_SECRET: SECRET })),
}));
jest.mock('../../src/services/auth.service', () => ({ isSessionRevoked: mockIsSessionRevoked }));

import { requireAdmin } from '../../src/middleware/admin.middleware';
import { requireAdminJwt } from '../../src/middleware/requireAdminJwt.middleware';

function makeReqRes(authHeader?: string) {
  const req = { headers: authHeader ? { authorization: authHeader } : {} } as unknown as Request;
  const res = {} as Response;
  const next = jest.fn() as unknown as NextFunction;
  return { req, res, next };
}

function token(claims: object = { sub: 'admin-1', type: 'access', sv: 2, role: 'admin' }, secret = SECRET) {
  return jwt.sign(claims, secret, { expiresIn: '1h' });
}

describe('requireAdmin and deprecated requireAdminJwt alias', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockIsSessionRevoked.mockResolvedValue(false);
  });

  it('allows a valid admin access token and checks its Redis revocation state', async () => {
    const { req, res, next } = makeReqRes(`Bearer ${token()}`);
    await requireAdmin(req, res, next);
    expect(mockIsSessionRevoked).toHaveBeenCalledWith('admin-1', 2);
    expect((req as unknown as Record<string, unknown>).userId).toBe('admin-1');
    expect(next).toHaveBeenCalledWith();
  });

  it('keeps the deprecated export as an alias of the canonical middleware', async () => {
    const { req, res, next } = makeReqRes(`Bearer ${token()}`);
    await requireAdminJwt(req, res, next);
    expect(next).toHaveBeenCalledWith();
    expect(mockIsSessionRevoked).toHaveBeenCalledWith('admin-1', 2);
  });

  it.each([
    ['expired', jwt.sign({ sub: 'admin-1', type: 'access', role: 'admin' }, SECRET, { expiresIn: -1 })],
    ['tampered', `${token()}.tampered`],
  ])('rejects an %s token', async (_label, signedToken) => {
    const { req, res, next } = makeReqRes(`Bearer ${signedToken}`);
    await requireAdmin(req, res, next);
    expect((next as jest.Mock).mock.calls[0][0]).toMatchObject({ statusCode: 401 });
  });

  it('rejects a valid token without the admin role', async () => {
    const { req, res, next } = makeReqRes(`Bearer ${token({ sub: 'user-1', type: 'access', role: 'user' })}`);
    await requireAdmin(req, res, next);
    expect((next as jest.Mock).mock.calls[0][0]).toMatchObject({
      statusCode: 403,
      message: 'Forbidden: admin role required',
    });
    expect(mockIsSessionRevoked).not.toHaveBeenCalled();
  });

  it('rejects a revoked admin session', async () => {
    mockIsSessionRevoked.mockResolvedValue(true);
    const { req, res, next } = makeReqRes(`Bearer ${token()}`);
    await requireAdmin(req, res, next);
    const error = (next as jest.Mock).mock.calls[0][0];
    expect(error).toBeInstanceOf(AppError);
    expect(error).toMatchObject({ statusCode: 401, message: 'Session has been invalidated' });
  });
});
