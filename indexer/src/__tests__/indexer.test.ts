import { describe, expect, it } from '@jest/globals';
import fs from 'fs';
import path from 'path';

describe('Soroban poller imports', () => {
  it('uses cursor persistence and only recognizes Soroban contract events', () => {
    const pollerSource = fs.readFileSync(path.join(__dirname, '../poller.ts'), 'utf-8');

    expect(pollerSource).toContain("import { getCursor, saveCursor } from './db';");
    expect(pollerSource).not.toMatch(/upsertInvoice|Invoice/);
    expect(pollerSource).toContain("'market_created'");
    expect(pollerSource).toContain("'bet_placed'");
    expect(pollerSource).not.toContain("'submitted'");
  });
});
