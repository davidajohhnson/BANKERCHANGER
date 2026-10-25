import crypto from 'crypto';
import type { PoolClient } from 'pg';

export interface WebhookEventPayload {
  [key: string]: unknown;
}

export function computeWebhookSignature(payload: string | Buffer | object, secret: string): string {
  const data =
    typeof payload === 'string' || Buffer.isBuffer(payload) ? payload : JSON.stringify(payload);
  return crypto.createHmac('sha256', secret).update(data).digest('hex');
}

export async function enqueueWebhookEvent(
  client: Pick<PoolClient, 'query'>,
  eventType: string,
  eventKey: string,
  payload: WebhookEventPayload
): Promise<void> {
  await client.query(
    `INSERT INTO webhook_deliveries
       (webhook_id, target_url, signing_secret, event_type, event_key, payload)
     SELECT id, url, secret, $1, $2, $3::jsonb
       FROM webhook_subscriptions
      WHERE status = 'active' AND topics @> ARRAY[$1]::text[]
     ON CONFLICT (webhook_id, event_type, event_key) DO NOTHING`,
    [eventType, eventKey, JSON.stringify(payload)]
  );
}
