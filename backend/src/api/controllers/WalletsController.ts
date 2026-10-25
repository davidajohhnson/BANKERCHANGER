import type { Request, Response, NextFunction } from 'express';

// Shared withdrawal initiation handler; execution requires downstream review.
export const withdraw = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const body = req.body as {
      walletId: string;
      currency: string;
      amount: number;
      destination: string;
    };

    // Placeholder: In production, run KYC/balance checks and enqueue the withdrawal
    res.status(202).json({
      withdrawalId: 'wd_' + Date.now(),
      walletId: body.walletId,
      amount: body.amount,
      currency: body.currency,
      destination: body.destination,
      status: 'pending_review',
      createdAt: new Date().toISOString(),
    });
  } catch (err) {
    next(err);
  }
};
