import { Hono } from 'hono';
import { Bindings } from '../index';

const app = new Hono<{ Bindings: Bindings }>();

app.get('/', async (c) => {
  const trips = await c.env.DB.prepare('SELECT * FROM trips ORDER BY start_time DESC LIMIT 50').all();
  return c.json({ trips: trips.results });
});

export { app as tripsRoutes };
