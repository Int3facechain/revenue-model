export interface SettlementSeries {
  payments: number[];
}

/**
 * Base step funding payment:
 * P_t = N * f_t
 */
export function baseStepPayment(
  fundingRate: number,
  notional: number
): number {
  return notional * fundingRate;
}

/**
 * Aggregated K-step funding payment for a given window:
 * P^(K) = N * sum(f_t over window)
 */
export function aggregatedPayment(
  windowFundingRates: number[],
  notional: number
): number {
  const sum = windowFundingRates.reduce((acc, x) => acc + x, 0);
  return notional * sum;
}

/**
 * Aggregated K-step rate series:
 *
 * F^(K)(tau) = sum_{t = tau-K+1 .. tau} f_t
 *
 * For early indices where a full window is not available
 * we use a prefix sum convention:
 * F^(K)(tau) = sum_{t = 0 .. tau} f_t  if tau < K-1
 *
 * fundingRates[i] corresponds to f_(i+1).
 */
export function aggregatedRateSeries(
  fundingRates: number[],
  windowSize: number
): number[] {
  const result: number[] = [];

  for (let i = 0; i < fundingRates.length; i++) {
    const start = Math.max(0, i - (windowSize - 1));
    let sum = 0;
    for (let j = start; j <= i; j++) {
      sum += fundingRates[j];
    }
    result.push(sum);
  }

  return result;
}

/**
 * Piecewise K-step settlement:
 *
 * P_adj(tau) = 0                        if tau mod K != 0
 * P_adj(tau) = N * sum_{t=tau-K+1..tau} f_t  if tau mod K == 0
 *
 * In code: fundingRates[i] is f_(i+1), stepIndex = i + 1.
 */
export function piecewiseLumpSettlement(
  fundingRates: number[],
  notional: number,
  windowSize: number
): SettlementSeries {
  const payments: number[] = [];

  for (let i = 0; i < fundingRates.length; i++) {
    const stepIndex = i + 1;

    if (stepIndex % windowSize !== 0) {
      payments.push(0);
      continue;
    }

    const start = Math.max(0, i - (windowSize - 1));
    let windowSum = 0;
    for (let j = start; j <= i; j++) {
      windowSum += fundingRates[j];
    }

    const payment = notional * windowSum;
    payments.push(payment);
  }

  return { payments };
}

/**
 * Buffer-style settlement (equivalent to the piecewise formula):
 *
 * a_t = N * f_t
 * B <- B + a_t each step
 * If stepIndex % windowSize == 0: pay B, then reset B = 0
 */
export function bufferLumpSettlement(
  fundingRates: number[],
  notional: number,
  windowSize: number
): SettlementSeries {
  const payments: number[] = [];
  let buffer = 0;

  for (let i = 0; i < fundingRates.length; i++) {
    const stepIndex = i + 1;

    const accrual = notional * fundingRates[i];
    buffer += accrual;

    if (stepIndex % windowSize === 0) {
      payments.push(buffer);
      buffer = 0;
    } else {
      payments.push(0);
    }
  }

  return { payments };
}

/**
 * Smoothed settlement with non-overlapping blocks:
 *
 * For each block of length L (normally L = windowSize):
 *   F_block = sum f_t over the block
 *   f_t_adj = F_block / L
 *   P_t_adj = N * f_t_adj
 *
 * The last block may be shorter than windowSize.
 */
export function smoothedBlockSettlement(
  fundingRates: number[],
  notional: number,
  windowSize: number
): SettlementSeries {
  const payments: number[] = new Array(fundingRates.length).fill(0);

  for (
    let blockStart = 0;
    blockStart < fundingRates.length;
    blockStart += windowSize
  ) {
    const blockEnd = Math.min(
      blockStart + windowSize,
      fundingRates.length
    );
    const blockLength = blockEnd - blockStart;

    let sum = 0;
    for (let i = blockStart; i < blockEnd; i++) {
      sum += fundingRates[i];
    }

    const perStepRate =
      blockLength > 0 ? sum / blockLength : 0;
    const perStepPayment = notional * perStepRate;

    for (let i = blockStart; i < blockEnd; i++) {
      payments[i] = perStepPayment;
    }
  }

  return { payments };
}

/**
 * Convenience function to compute all views at once.
 */
export interface FundingViews {
  baseStepPayments: number[];
  aggregatedRates: number[];
  lumpSettlement: number[];
  bufferSettlement: number[];
  smoothedSettlement: number[];
}

export function computeFundingViews(
  fundingRates: number[],
  notional: number,
  windowSize: number
): FundingViews {
  const baseStepPayments = fundingRates.map((f) =>
    baseStepPayment(f, notional)
  );
  const aggregatedRates = aggregatedRateSeries(
    fundingRates,
    windowSize
  );
  const lumpSettlement = piecewiseLumpSettlement(
    fundingRates,
    notional,
    windowSize
  ).payments;
  const bufferSettlement = bufferLumpSettlement(
    fundingRates,
    notional,
    windowSize
  ).payments;
  const smoothedSettlement = smoothedBlockSettlement(
    fundingRates,
    notional,
    windowSize
  ).payments;

  return {
    baseStepPayments,
    aggregatedRates,
    lumpSettlement,
    bufferSettlement,
    smoothedSettlement,
  };
}
