import { Request, Response, NextFunction } from "express";
import { z, ZodSchema } from "zod";
import { AppError } from "../utils/AppError";

// ─── Schema Definitions ──────────────────────────────────────────────────────

export const PaginationSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(200).default(20),
  sortBy: z.string().optional(),
  sortOrder: z.enum(["asc", "desc"]).default("asc"),
});

export const MarketIdSchema = z.object({
  market_id: z.string().min(1).max(128),
});

export const CreateMarketSchema = z.object({
  title: z.string().min(1).max(500),
  description: z.string().min(1).max(5000),
  fighter_a: z.string().min(1).max(200),
  fighter_b: z.string().min(1).max(200),
  event_date: z.string().datetime(),
  weight_class: z.string().min(1).max(100),
  tier: z.number().int().min(1).max(100),
});

export const PlaceBetSchema = z.object({
  market_id: z.string().min(1).max(128),
  outcome: z.enum(["fighter_a", "fighter_b", "draw"]),
  amount: z.number().positive().max(1000000),
  slippage_tolerance: z.number().min(0).max(0.5).default(0.05),
});

export const ResolveMarketSchema = z.object({
  market_id: z.string().min(1).max(128),
  outcome: z.enum(["fighter_a", "fighter_b", "draw", "no_contest"]),
});

export const SubmitOracleReportSchema = z.object({
  market_id: z.string().min(1).max(128),
  outcome: z.enum(["fighter_a", "fighter_b", "draw", "no_contest"]),
  confidence: z.number().min(0).max(1),
  signature: z.string().min(1),
});

export const UserRegistrationSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).max(128),
  displayName: z.string().min(1).max(100),
});

export const UserLoginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

export const DisputeSchema = z.object({
  market_id: z.string().min(1).max(128),
  reason: z.string().min(10).max(5000),
  evidence: z.array(z.string().url()).max(10).optional(),
});

// ─── Validation Middleware Factory ────────────────────────────────────────────

export function validateBody(schema: ZodSchema) {
  return validate(schema, 'body');
}

export function validateQuery(schema: ZodSchema) {
  return validate(schema, 'query');
}

export function validateParams(schema: ZodSchema) {
  return validate(schema, 'params');
}

type ValidationTarget = 'body' | 'query' | 'params';

/** Canonical request validation middleware. Invalid input always has one API shape. */
export function validate(schemaOrSchemas: ZodSchema | Partial<Record<ValidationTarget, ZodSchema>>, target: ValidationTarget = 'body') {
  const schemas = typeof (schemaOrSchemas as ZodSchema).safeParse === 'function'
    ? { [target]: schemaOrSchemas }
    : schemaOrSchemas;
  return (req: Request, res: Response, next: NextFunction): void => {
    for (const [requestTarget, schema] of Object.entries(schemas) as [ValidationTarget, ZodSchema][]) {
      const parsed = schema.safeParse(req[requestTarget]);
      if (!parsed.success) {
        const details = parsed.error.issues.map((issue) => ({
          field: issue.path.join('.'), message: issue.message, code: issue.code,
        }));
        res.status(422).json({
          success: false,
          error: { message: 'Request validation failed', code: 'VALIDATION_ERROR', details },
        });
        return;
      }
      (req as any)[requestTarget] = parsed.data;
    }
    next();
  };
}

// ─── Authorization Middleware ─────────────────────────────────────────────────

export function requireRole(...roles: string[]) {
  return (req: Request, _res: Response, next: NextFunction): void => {
    const user = (req as any).user;
    if (!user) {
      return next(new AppError(401, "Authentication required"));
    }

    if (roles.length > 0 && !roles.includes(user.role)) {
      return next(new AppError(403, `Insufficient permissions. Required: ${roles.join(" or ")}`));
    }

    next();
  };
}

// ─── Request Size Limiter ────────────────────────────────────────────────────

export function maxBodySize(maxBytes: number) {
  return (req: Request, _res: Response, next: NextFunction): void => {
    const contentLength = parseInt(req.headers["content-length"] || "0", 10);
    if (contentLength > maxBytes) {
      return next(
        new AppError(413, `Request body too large. Maximum size: ${maxBytes} bytes`),
      );
    }
    next();
  };
}

// ─── Idempotency Check ──────────────────────────────────────────────────────

export function requireIdempotencyKey() {
  return (req: Request, _res: Response, next: NextFunction): void => {
    const idempotencyKey = req.headers["idempotency-key"] as string;
    if (!idempotencyKey) {
      return next(new AppError(400, "Idempotency-Key header is required"));
    }

    if (idempotencyKey.length < 16 || idempotencyKey.length > 128) {
      return next(new AppError(400, "Idempotency-Key must be between 16 and 128 characters"));
    }

    next();
  };
}
