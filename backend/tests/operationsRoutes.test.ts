import express from 'express';
import request from 'supertest';
import router from '../src/routes/operations.routes';
import { placeBet } from '../src/api/controllers/BetController';
import { withdraw } from '../src/api/controllers/WalletsController';

jest.mock('../src/middleware/auth.middleware', () => ({
  requireAuth: (req: express.Request, res: express.Response, next: express.NextFunction) => {
    if (req.headers.authorization !== 'Bearer session') { res.sendStatus(401); return; }
    next();
  },
}));
jest.mock('../src/api/controllers/BetController', () => ({
  placeBet: jest.fn((_req, res) => res.status(201).json({ placed: true })),
}));
jest.mock('../src/api/controllers/WalletsController', () => ({
  withdraw: jest.fn((_req, res) => res.status(202).json({ reviewed: true })),
}));

const app = express();
app.use(express.json(), router);
beforeEach(() => jest.clearAllMocks());
it.each(['/trading/bet', '/wallet/withdraw'])('requires authentication and validates %s before dispatch', async path => {
  expect((await request(app).post(path).send({})).status).toBe(401);
  expect((await request(app).post(path).set('Authorization', 'Bearer session').send({})).status).toBe(422);
  expect(placeBet).not.toHaveBeenCalled();
  expect(withdraw).not.toHaveBeenCalled();
});
it('dispatches a validated bet to BetController.placeBet', async () => {
  const response = await request(app).post('/trading/bet').set('Authorization', 'Bearer session').send({
    market_id: 'market', bettor_address: 'GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWHF',
    side: 'fighter_a', amount: '1000',
  });
  expect(response.status).toBe(201);
  expect(placeBet).toHaveBeenCalledTimes(1);
});
it('dispatches a validated withdrawal to WalletsController.withdraw', async () => {
  const response = await request(app).post('/wallet/withdraw').set('Authorization', 'Bearer session').send({
    walletId: 'd9428888-122b-4c7b-aea4-3660aaa693f8', currency: 'XLM', amount: 1, destination: 'wallet',
  });
  expect(response.status).toBe(202);
  expect(withdraw).toHaveBeenCalledTimes(1);
});
