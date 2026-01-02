import type { NEVDISVehicle } from './nevdis';

type Priority = 'critical' | 'high' | 'medium' | 'low';

interface WatchlistHit {
  type: string;
  source: string;
  priority: Priority;
  reason: string;
  details?: Record<string, unknown>;
}

export async function checkWatchlists(
  db: D1Database,
  plate: string,
  vehicleData: NEVDISVehicle | Record<string, unknown> | null,
): Promise<WatchlistHit | null> {
  const normalizePriority = (value: unknown): Priority => {
    const allowed: Priority[] = ['critical', 'high', 'medium', 'low'];
    return allowed.includes(value as Priority) ? (value as Priority) : 'medium';
  };

  const customHit = await db
    .prepare(`
    SELECT reason, priority, notes FROM plate_watchlist WHERE plate_number = ?
  `)
    .bind(plate)
    .first();

  if (customHit) {
    return {
      type: 'custom',
      source: 'custom_watchlist',
      priority: normalizePriority(customHit.priority),
      reason: customHit.reason as string,
      details: { notes: customHit.notes },
    };
  }

  if (vehicleData?.stolen) {
    return {
      type: 'stolen',
      source: 'nevdis',
      priority: 'critical',
      reason: 'STOLEN_VEHICLE',
      details: {
        jurisdiction: vehicleData.stolen_jurisdiction,
        date: vehicleData.stolen_date,
      },
    };
  }

  if (vehicleData?.wovr_status && vehicleData.wovr_status !== 'NOT_LISTED') {
    const isStatutory = vehicleData.wovr_type === 'STATUTORY';
    return {
      type: isStatutory ? 'wovr_statutory' : 'wovr_repairable',
      source: 'nevdis',
      priority: isStatutory ? 'high' : 'medium',
      reason: `WOVR_${vehicleData.wovr_type}`,
      details: { wovr_type: vehicleData.wovr_type },
    };
  }

  if (vehicleData?.rego_status === 'EXPIRED' || vehicleData?.rego_status === 'CANCELLED') {
    return {
      type: 'expired_rego',
      source: 'nevdis',
      priority: 'medium',
      reason: 'EXPIRED_REGISTRATION',
      details: { expiry: vehicleData.rego_expiry },
    };
  }

  if (vehicleData?.ppsr_encumbered) {
    return {
      type: 'ppsr',
      source: 'nevdis',
      priority: 'medium',
      reason: 'PPSR_ENCUMBERED',
      details: {},
    };
  }

  return null;
}
