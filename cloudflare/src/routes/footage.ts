import { Hono } from 'hono';
import type { Bindings } from '../index';

const app = new Hono<{ Bindings: Bindings }>();

app.post('/', async (c) => {
  const payload = await c.req.json();
  // TODO: generate signed upload URLs for R2/Stream
  return c.json({ success: true, payload });
});

export { app as footageRoutes };
