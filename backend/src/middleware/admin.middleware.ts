import type { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { AppError } from '../utils/AppError';
import { getEnv } from '../config/env';
import { isSessionRevoked } from '../services/auth.service';

/* eslint-disable @typescript-eslint/no-namespace */
export interface AdminJwtPayload extends jwt.JwtPayload {
  role: 'admin';
}

declare global {
  namespace Express {
    interface Request {
      admin?: AdminJwtPayload;
    }
  }
}

/** Verifies an access JWT, admin role, and Redis session revocation state. */
export async function requireAdmin(req: Request, _res: Response, next: NextFunction): Promise<void> {
  try {
    const authHeader = req.headers.authorization;
    if (!authHeader?.startsWith('Bearer ')) {
      throw new AppError(401, 'Missing or invalid Authorization header');
    }

    const token = authHeader.slice(7);
    const { JWT_SECRET, JWT_ACCESS_SECRET } = getEnv();
    const payload = jwt.verify(token, JWT_ACCESS_SECRET || JWT_SECRET) as jwt.JwtPayload;

    if (payload.type !== 'access') throw new AppError(401, 'Invalid token type');
    if (payload.role !== 'admin') throw new AppError(403, 'Forbidden: admin role required');
    if (typeof payload.sub !== 'string' || !payload.sub) {
      throw new AppError(401, 'Invalid token subject');
    }

    const userId = payload.sub;
    const sessionVersion = typeof payload.sv === 'number' ? payload.sv : 0;
    if (await isSessionRevoked(userId, sessionVersion)) {
      throw new AppError(401, 'Session has been invalidated');
    }

    req.admin = payload as AdminJwtPayload;
    (req as unknown as Record<string, unknown>).userId = userId;
    (req as unknown as Record<string, unknown>).sessionVersion = sessionVersion;
    next();
  } catch (err) {
    next(err instanceof AppError ? err : new AppError(401, 'Invalid or expired token'));
  }
}
