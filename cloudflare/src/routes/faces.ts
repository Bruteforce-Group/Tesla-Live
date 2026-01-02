import { Hono } from 'hono';
import { Bindings } from '../index';

const app = new Hono<{ Bindings: Bindings }>();

app.post('/', async (c) => {
  const payload = await c.req.json();
  // TODO: persist face sightings and push to vector search
  return c.json({ success: true, payload });
});

export { app as facesRoutes };
