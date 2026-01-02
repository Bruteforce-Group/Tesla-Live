import { Hono } from 'hono';
import { Bindings } from '../index';

const app = new Hono<{ Bindings: Bindings }>();

app.post('/', async (c) => {
  const alert = await c.req.json();
  // TODO: persist alerts and push to dashboard DO
  return c.json({ success: true, alert });
});

export { app as alertsRoutes };
