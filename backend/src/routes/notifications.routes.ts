import { Router, Request, Response, NextFunction } from 'express';
import { validate } from '../middleware/validation.middleware';
import { requireAuth } from '../middleware/auth.middleware';
import { AppError } from '../utils/AppError';
import { pool } from '../config/db';
import { redis } from '../config/redis';
import {
  getNotificationSettingsParam,
  updateNotificationSettingsBody,
  testNotificationBody,
} from '../schemas/endpointGroups.schemas';

const router = Router();

/**
 * @swagger
 * tags:
 *   name: Notifications
 *   description: Notification and alert preference management
 */

const SETTINGS_CACHE_TTL_SECONDS = 60 * 60;
const settingsCacheKey = (userId: string) => `notifications:settings:${userId}`;

async function getSettings(userId: string): Promise<Record<string, unknown>> {
  try {
    const cached = await redis.get(settingsCacheKey(userId));
    if (cached) return JSON.parse(cached);
  } catch { /* PostgreSQL remains the source of truth when Redis is unavailable. */ }

  const { rows } = await pool.query(
    `SELECT email_enabled, push_enabled, settings FROM user_notification_settings WHERE user_id = $1`,
    [userId],
  );
  const row = rows[0] ?? { email_enabled: true, push_enabled: true };
  const settings = {
    betPlaced: true, betResolved: true, betWon: true, claimProcessed: true,
    marketCreated: false, marketLocked: true, disputeFiled: true,
    disputeResolved: true, securityAlert: true, systemMaintenance: true,
    quietHoursStart: null, quietHoursEnd: null,
    ...(row.settings ?? {}),
    emailEnabled: row.email_enabled,
    pushEnabled: row.push_enabled,
    channel: row.email_enabled && row.push_enabled ? 'both' : row.email_enabled ? 'email' : row.push_enabled ? 'push' : 'none',
  };
  try { await redis.set(settingsCacheKey(userId), JSON.stringify(settings), 'EX', SETTINGS_CACHE_TTL_SECONDS); } catch { /* Cache is optional. */ }
  return settings;
}

/**
 * @swagger
 * /api/v1/notifications/{userId}/settings:
 *   get:
 *     summary: Get notification settings for a user
 *     tags: [Notifications]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: userId
 *         required: true
 *         schema:
 *           type: string
 *           format: uuid
 *     responses:
 *       200:
 *         description: Notification settings
 *       403:
 *         description: Cannot view another user's settings
 */
router.get(
  '/:userId/settings',
  requireAuth,
  validate(getNotificationSettingsParam, 'params'),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { userId } = req.params;
      const authUser = (req as any).user;

      if (authUser.id !== userId && authUser.role !== 'admin') {
        throw new AppError(403, 'Cannot view another user\'s notification settings');
      }

      const settings = await getSettings(userId);

      res.json({ userId, settings });
    } catch (err) {
      next(err);
    }
  },
);

/**
 * @swagger
 * /api/v1/notifications/{userId}/settings:
 *   put:
 *     summary: Update notification settings
 *     tags: [Notifications]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: userId
 *         required: true
 *         schema:
 *           type: string
 *           format: uuid
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               betPlaced:
 *                 type: boolean
 *               betResolved:
 *                 type: boolean
 *               channel:
 *                 type: string
 *                 enum: [email, push, both, none]
 *               quietHoursStart:
 *                 type: string
 *                 pattern: '^\\d{2}:\\d{2}$'
 *               quietHoursEnd:
 *                 type: string
 *                 pattern: '^\\d{2}:\\d{2}$'
 *     responses:
 *       200:
 *         description: Settings updated
 *       403:
 *         description: Cannot modify another user's settings
 *       422:
 *         description: Validation error
 */
router.put(
  '/:userId/settings',
  requireAuth,
  validate(getNotificationSettingsParam, 'params'),
  validate(updateNotificationSettingsBody, 'body'),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { userId } = req.params;
      const authUser = (req as any).user;

      if (authUser.id !== userId && authUser.role !== 'admin') {
        throw new AppError(403, 'Cannot modify another user\'s notification settings');
      }

      const existing = await getSettings(userId);
      const update = req.body as Record<string, unknown>;
      const channel = update.channel as string | undefined;
      const emailEnabled = channel === undefined ? existing.emailEnabled !== false : ['email', 'both'].includes(channel);
      const pushEnabled = channel === undefined ? existing.pushEnabled !== false : ['push', 'both'].includes(channel);
      const updatedSettings = { ...existing, ...update, emailEnabled, pushEnabled, channel: channel ?? existing.channel };
      const { rows } = await pool.query(
        `INSERT INTO user_notification_settings (user_id, email_enabled, push_enabled, settings)
         VALUES ($1, $2, $3, $4)
         ON CONFLICT (user_id) DO UPDATE SET email_enabled = EXCLUDED.email_enabled,
           push_enabled = EXCLUDED.push_enabled, settings = EXCLUDED.settings, updated_at = NOW()
         RETURNING email_enabled, push_enabled, updated_at`,
        [userId, emailEnabled, pushEnabled, JSON.stringify(updatedSettings)],
      );
      const updated = { ...updatedSettings, emailEnabled: rows[0].email_enabled, pushEnabled: rows[0].push_enabled };
      try { await redis.del(settingsCacheKey(userId)); } catch { /* Cache is optional. */ }

      res.json({
        message: 'Notification settings updated',
        userId,
        settings: updated,
        updatedAt: new Date().toISOString(),
      });
    } catch (err) {
      next(err);
    }
  },
);

/**
 * @swagger
 * /api/v1/notifications/test:
 *   post:
 *     summary: Send a test notification
 *     tags: [Notifications]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [type, userId, template]
 *             properties:
 *               type:
 *                 type: string
 *                 enum: [email, push]
 *               userId:
 *                 type: string
 *                 format: uuid
 *               template:
 *                 type: string
 *                 enum: [bet_placed, bet_resolved, security_alert, system_maintenance]
 *     responses:
 *       200:
 *         description: Test notification sent
 *       422:
 *         description: Validation error
 */
router.post(
  '/test',
  requireAuth,
  validate(testNotificationBody, 'body'),
  async (req: Request, res: Response, next: NextFunction) => {
    try {
      const { type, userId, template } = req.body;

      // Placeholder: In production, actually send the notification
      res.json({
        message: `Test ${type} notification sent`,
        userId,
        template,
        sentAt: new Date().toISOString(),
        deliveryId: `dlv_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      });
    } catch (err) {
      next(err);
    }
  },
);

export default router;
