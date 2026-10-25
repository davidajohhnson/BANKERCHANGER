/**
 * @openapi
 * /trading/bet:
 *   post:
 *     summary: Place a bet with pool locking and slippage validation
 *     tags: [Bets]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required: [market_id, bettor_address, side, amount]
 *             properties:
 *               market_id:
 *                 type: string
 *                 minLength: 1
 *               bettor_address:
 *                 type: string
 *                 description: Valid Stellar public key
 *               side:
 *                 type: string
 *                 enum: [fighter_a, fighter_b, draw]
 *               amount:
 *                 type: string
 *                 pattern: '^[1-9]\d*$'
 *                 description: Positive integer stroops
 *               max_slippage_bps:
 *                 type: integer
 *                 minimum: 0
 *                 maximum: 5000
 *                 default: 500
 *               idempotency_key:
 *                 type: string
 *                 minLength: 8
 *                 maxLength: 128
 *     responses:
 *       201:
 *         description: Bet committed
 *       400:
 *         description: Closed market or slippage exceeded
 *       401:
 *         description: Authentication required
 *       404:
 *         description: Market not found
 *       422:
 *         description: Invalid body
 */
import { Router } from 'express';
import { requireAuth } from '../middleware/auth.middleware';
import { validate, validateBody } from '../api/middleware/validate';
import { placeBetGroup4BodySchema } from '../schemas/betGroup4.schemas';
import { withdrawBody } from '../schemas/apiModuleGroups.schemas';
import { placeBet } from '../api/controllers/BetController';
import { withdraw } from '../api/controllers/WalletsController';

const router = Router();
router.post('/trading/bet', requireAuth, validateBody(placeBetGroup4BodySchema), placeBet);
router.post('/wallet/withdraw', requireAuth, validate(withdrawBody, 'body'), withdraw);
export default router;
