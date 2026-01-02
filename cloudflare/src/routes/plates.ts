import { Hono } from 'hono';
import type { Bindings } from '../index';
import { NEVDISClient } from '../services/nevdis';
import { checkWatchlists } from '../services/watchlist';

const app = new Hono<{ Bindings: Bindings }>();

interface PlateSighting {
  plate_number: string;
  plate_state?: string;
  confidence: number;
  timestamp: string;
  gps_lat: number;
  gps_lng: number;
  vehicle_id: string;
  trip_id?: string;
}

type VehicleData = Awaited<ReturnType<NEVDISClient['lookupPlate']>>;
type WatchlistHit = Awaited<ReturnType<typeof checkWatchlists>>;

// biome-ignore lint/complexity/noExcessiveCognitiveComplexity: inserts many bound parameters
async function saveSighting(
  env: Bindings,
  sighting: PlateSighting,
  sightingId: string,
  vehicleData: VehicleData,
  watchlistHit: WatchlistHit,
) {
  await env.DB.prepare(
    `
    INSERT INTO plate_sightings (
      sighting_id, vehicle_id, trip_id, plate_number, plate_state,
      confidence, timestamp, gps_lat, gps_lng,
      rego_status, rego_expiry, vehicle_make, vehicle_model,
      vehicle_year, vehicle_colour, vin,
      stolen_flag, stolen_jurisdiction, stolen_date,
      wovr_status, wovr_type, ppsr_encumbered,
      watchlist_hit, watchlist_priority
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `,
  )
    .bind(
      sightingId,
      sighting.vehicle_id,
      sighting.trip_id || null,
      sighting.plate_number,
      sighting.plate_state || vehicleData?.state || null,
      sighting.confidence,
      sighting.timestamp,
      sighting.gps_lat,
      sighting.gps_lng,
      vehicleData?.rego_status || null,
      vehicleData?.rego_expiry || null,
      vehicleData?.make || null,
      vehicleData?.model || null,
      vehicleData?.year || null,
      vehicleData?.colour || null,
      vehicleData?.vin || null,
      vehicleData?.stolen || false,
      vehicleData?.stolen_jurisdiction || null,
      vehicleData?.stolen_date || null,
      vehicleData?.wovr_status || null,
      vehicleData?.wovr_type || null,
      vehicleData?.ppsr_encumbered || false,
      watchlistHit?.reason || null,
      watchlistHit?.priority || null,
    )
    .run();
}

async function recordWatchlistAlert(
  env: Bindings,
  sighting: PlateSighting,
  watchlistHit: WatchlistHit,
  vehicleData: VehicleData,
) {
  if (!watchlistHit) {
    return;
  }

  await env.DB.prepare(
    `
      INSERT INTO watchlist_alerts (
        alert_id, plate_number, alert_type, priority,
        vehicle_make, vehicle_model, vehicle_colour,
        gps_lat, gps_lng, timestamp, details
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `,
  )
    .bind(
      crypto.randomUUID(),
      sighting.plate_number,
      watchlistHit.type,
      watchlistHit.priority,
      vehicleData?.make || null,
      vehicleData?.model || null,
      vehicleData?.colour || null,
      sighting.gps_lat,
      sighting.gps_lng,
      sighting.timestamp,
      JSON.stringify({ vehicleData, watchlistHit }),
    )
    .run();
}

async function broadcastWatchlistAlert(
  env: Bindings,
  sighting: PlateSighting,
  watchlistHit: WatchlistHit,
  vehicleData: VehicleData,
) {
  if (!watchlistHit) return;

  const dashboardId = env.DASHBOARD.idFromName('fleet-dashboard');
  const dashboard = env.DASHBOARD.get(dashboardId);
  await dashboard.fetch(
    new Request('https://internal/broadcast', {
      method: 'POST',
      body: JSON.stringify({
        type: 'watchlist_alert',
        data: {
          plate: sighting.plate_number,
          alert_type: watchlistHit.type,
          priority: watchlistHit.priority,
          vehicle: vehicleData,
          location: { lat: sighting.gps_lat, lng: sighting.gps_lng },
          timestamp: sighting.timestamp,
        },
      }),
    }),
  );
}

async function notifyWatchlist(
  env: Bindings,
  sighting: PlateSighting,
  watchlistHit: WatchlistHit,
  vehicleData: VehicleData,
) {
  if (!watchlistHit) return;
  if (watchlistHit.priority === 'critical' || watchlistHit.priority === 'high') {
    await env.NOTIFICATION_QUEUE.send({
      type: 'watchlist_alert',
      alert: {
        plate: sighting.plate_number,
        alert_type: watchlistHit.type,
        priority: watchlistHit.priority,
        vehicle: vehicleData,
      },
    });
  }
}

app.post('/', async (c) => {
  const sighting: PlateSighting = await c.req.json();
  const sightingId = crypto.randomUUID();

  const nevdis = new NEVDISClient(c.env.NEVDIS_API_URL, c.env.NEVDIS_API_KEY);
  const vehicleData = await nevdis.lookupPlate(sighting.plate_number, sighting.plate_state);

  const watchlistHit = await checkWatchlists(c.env.DB, sighting.plate_number, vehicleData);

  await saveSighting(c.env, sighting, sightingId, vehicleData, watchlistHit);
  await recordWatchlistAlert(c.env, sighting, watchlistHit, vehicleData);
  await broadcastWatchlistAlert(c.env, sighting, watchlistHit, vehicleData);
  await notifyWatchlist(c.env, sighting, watchlistHit, vehicleData);

  return c.json({
    success: true,
    sighting_id: sightingId,
    vehicle_data: vehicleData,
    watchlist_hit: watchlistHit,
  });
});

app.get('/:plate', async (c) => {
  const plate = c.req.param('plate');

  const sightings = await c.env.DB.prepare(
    `
    SELECT * FROM plate_sightings 
    WHERE plate_number = ? 
    ORDER BY timestamp DESC 
    LIMIT 100
  `,
  )
    .bind(plate)
    .all();

  return c.json({ plate, sightings: sightings.results });
});

export { app as platesRoutes };
