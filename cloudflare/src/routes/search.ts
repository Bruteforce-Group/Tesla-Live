import { Hono } from 'hono';
import type { Bindings } from '../index';

const app = new Hono<{ Bindings: Bindings }>();

app.get('/', async (c) => {
  const query = (c.req.query('q') || '').trim();
  const objectType = c.req.query('object_type') || '';
  const audioLabel = c.req.query('audio_label') || '';
  const plate = c.req.query('plate') || '';
  const limit = Number(c.req.query('limit') || 50);

  const wildcard = (value: string) => `%${value}%`;

  const eventFilters: string[] = [];
  const params: any[] = [];
  if (query) {
    eventFilters.push(
      `(event_type LIKE ? OR object_type LIKE ? OR audio_label LIKE ? OR scene_description LIKE ?)`,
    );
    params.push(wildcard(query), wildcard(query), wildcard(query), wildcard(query));
  }
  if (objectType) {
    eventFilters.push(`object_type LIKE ?`);
    params.push(wildcard(objectType));
  }
  if (audioLabel) {
    eventFilters.push(`audio_label LIKE ?`);
    params.push(wildcard(audioLabel));
  }

  const whereClause = eventFilters.length ? `WHERE ${eventFilters.join(' AND ')}` : '';
  const eventsStmt = c.env.DB.prepare(
    `SELECT event_id, event_type, object_type, audio_label, audio_confidence, timestamp, gps_lat, gps_lng, severity, attributes, scene_description
     FROM events
     ${whereClause}
     ORDER BY timestamp DESC
     LIMIT ?`,
  ).bind(...params, limit);
  const events = (await eventsStmt.all()).results || [];

  const plateParams: any[] = [];
  const plateFilters: string[] = [];
  if (plate) {
    plateFilters.push(`plate_number LIKE ?`);
    plateParams.push(wildcard(plate));
  } else if (query) {
    plateFilters.push(`(plate_number LIKE ? OR vehicle_make LIKE ? OR vehicle_model LIKE ?)`);
    plateParams.push(wildcard(query), wildcard(query), wildcard(query));
  }
  const plateWhere = plateFilters.length ? `WHERE ${plateFilters.join(' AND ')}` : '';
  const platesStmt = c.env.DB.prepare(
    `SELECT plate_number, plate_state, vehicle_make, vehicle_model, vehicle_colour, timestamp, watchlist_hit, watchlist_priority, linked_event_id
     FROM plate_sightings
     ${plateWhere}
     ORDER BY timestamp DESC
     LIMIT ?`,
  ).bind(...plateParams, limit);
  const plates = (await platesStmt.all()).results || [];

  const facesStmt = c.env.DB.prepare(
    `SELECT sighting_id, matched_face_id, match_confidence, timestamp, gps_lat, gps_lng, linked_event_id
     FROM face_sightings
     WHERE (?1 IS NOT NULL AND matched_face_id LIKE ?2) OR (?1 = '' AND ?2 = '')
     ORDER BY timestamp DESC
     LIMIT ?3`,
  ).bind(query, wildcard(query || ''), limit);
  const faces = (await facesStmt.all()).results || [];

  return c.json({
    query,
    filters: { objectType, audioLabel, plate },
    events,
    plates,
    faces,
  });
});

export { app as searchRoutes };
