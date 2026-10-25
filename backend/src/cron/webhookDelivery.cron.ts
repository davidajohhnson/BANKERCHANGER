import cron from 'node-cron';
import { pool } from '../config/db';
import { computeWebhookSignature } from '../services/webhookDelivery.service';
import { logger } from '../utils/logger';

const RETRY_DELAYS_MS = [60_000, 5 * 60_000, 15 * 60_000, 60 * 60_000, 6 * 60 * 60_000];
const DELIVERY_BATCH_SIZE = 25;
const DELIVERY_TIMEOUT_MS = 10_000;

interface WebhookDelivery {
  id: string;
  webhook_id: string;
  target_url: string;
  signing_secret: string;
  event_type: string;
  payload: Record<string, unknown>;
  attempt_count: number;
  retry_count: number;
}

async function claimDueDeliveries(): Promise<WebhookDelivery[]> {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const { rows: due } = await client.query<{ id: string }>(
      `SELECT id
         FROM webhook_deliveries
        WHERE status IN ('pending', 'retrying')
          AND next_attempt_at <= NOW()
          AND (locked_at IS NULL OR locked_at < NOW() - INTERVAL '1 minute')
        ORDER BY next_attempt_at, id
        FOR UPDATE SKIP LOCKED
        LIMIT $1`,
      [DELIVERY_BATCH_SIZE]
    );
    if (due.length === 0) {
      await client.query('COMMIT');
      return [];
    }

    const ids = due.map((delivery) => delivery.id);
    const { rows } = await client.query<WebhookDelivery>(
      `UPDATE webhook_deliveries
          SET status = 'retrying', locked_at = NOW(), updated_at = NOW()
        WHERE id = ANY($1::bigint[])
        RETURNING id, webhook_id, target_url, signing_secret, event_type, payload, attempt_count, retry_count`,
      [ids]
    );
    await client.query('COMMIT');
    return rows;
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }
}

async function deliver(delivery: WebhookDelivery): Promise<void> {
  let responseCode: number | null = null;
  let errorMessage: string | null = null;
  try {
    const body = JSON.stringify(delivery.payload);
    const response = await fetch(delivery.target_url, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-webhook-id': delivery.webhook_id,
        'x-webhook-event': delivery.event_type,
        'x-signature': `sha256=${computeWebhookSignature(body, delivery.signing_secret)}`,
      },
      body,
      signal: AbortSignal.timeout(DELIVERY_TIMEOUT_MS),
    });
    responseCode = response.status;
    if (!response.ok) {
      const responseText = (await response.text()).slice(0, 2_000);
      errorMessage = `HTTP ${response.status}${responseText ? `: ${responseText}` : ''}`;
    }
  } catch (err) {
    errorMessage = err instanceof Error ? err.message : String(err);
  }

  if (!errorMessage) {
    await pool.query(
      `UPDATE webhook_deliveries
          SET status = 'success', attempt_count = attempt_count + 1,
              locked_at = NULL, delivered_at = NOW(), updated_at = NOW()
        WHERE id = $1`,
      [delivery.id]
    );
    return;
  }

  const retriesUsed = delivery.retry_count;
  const hasRetriesRemaining = retriesUsed < RETRY_DELAYS_MS.length;
  const delayMs = hasRetriesRemaining ? RETRY_DELAYS_MS[retriesUsed] : null;
  const status = hasRetriesRemaining ? 'retrying' : 'failed';

  await pool.query(
    `UPDATE webhook_deliveries
        SET status = $2,
            attempt_count = attempt_count + 1,
            retry_count = retry_count + CASE WHEN $2 = 'retrying' THEN 1 ELSE 0 END,
            next_attempt_at = CASE
              WHEN $2 = 'retrying' THEN NOW() + ($3::double precision * INTERVAL '1 millisecond')
              ELSE next_attempt_at
            END,
            last_error_response_code = $4,
            last_error = $5,
            locked_at = NULL,
            updated_at = NOW()
      WHERE id = $1`,
    [delivery.id, status, delayMs, responseCode, errorMessage]
  );
  logger.warn(
    {
      deliveryId: delivery.id,
      webhookId: delivery.webhook_id,
      responseCode,
      retrying: hasRetriesRemaining,
      err: errorMessage,
    },
    'Webhook delivery failed'
  );
}

export async function processDueWebhookDeliveries(): Promise<void> {
  const deliveries = await claimDueDeliveries();
  await Promise.all(
    deliveries.map(async (delivery) => {
      try {
        await deliver(delivery);
      } catch (err) {
        logger.error({ err, deliveryId: delivery.id }, 'Failed to persist webhook delivery result');
      }
    })
  );
}

export function startWebhookDeliveryCron(): void {
  cron.schedule('*/10 * * * * *', () => {
    void processDueWebhookDeliveries().catch((err) => {
      logger.error({ err }, 'Webhook delivery worker failed');
    });
  });
  void processDueWebhookDeliveries().catch((err) => {
    logger.error({ err }, 'Initial webhook delivery worker run failed');
  });
  logger.info('Webhook delivery worker scheduled (every 10 seconds)');
}
