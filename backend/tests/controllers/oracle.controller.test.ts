import { getOracleReports } from '../../src/api/controllers/OracleController';
import { pool } from '../../src/config/db';
import { Request, Response, NextFunction } from 'express';

jest.mock('../../src/config/db', () => ({ pool: { query: jest.fn() } }));
jest.mock('../../src/config/redis', () => ({ redis: { set: jest.fn() } }));
jest.mock('../../src/oracle/OracleService', () => ({ submitFightResult: jest.fn() }));

describe('getOracleReports', () => {
  const req = { params: { match_id: 'match-1' } } as unknown as Request;
  let res: Partial<Response>;
  let next: NextFunction;

  beforeEach(() => {
    jest.clearAllMocks();
    res = { status: jest.fn().mockReturnThis(), json: jest.fn() };
    next = jest.fn();
  });

  it('returns reports for a match', async () => {
    const reports = [{ timestamp: new Date(), oracle_address: 'GABC', outcome: 'fighter_a', signature: 'abc' }];
    (pool.query as jest.Mock).mockResolvedValue({ rows: reports });
    await getOracleReports(req, res as Response, next);
    expect(pool.query).toHaveBeenCalledWith(expect.stringContaining('FROM oracle_reports WHERE match_id = $1'), ['match-1']);
    expect(res.status).toHaveBeenCalledWith(200);
    expect(res.json).toHaveBeenCalledWith({ match_id: 'match-1', reports });
  });

  it('returns 404 when no reports exist', async () => {
    (pool.query as jest.Mock).mockResolvedValue({ rows: [] });
    await getOracleReports(req, res as Response, next);
    expect(res.status).toHaveBeenCalledWith(404);
    expect(res.json).toHaveBeenCalledWith(expect.objectContaining({ success: false }));
  });
});
