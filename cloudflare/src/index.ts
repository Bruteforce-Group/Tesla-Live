import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';

import { DashboardDO } from './durable-objects/dashboard';
import { alertsRoutes } from './routes/alerts';
import { facesRoutes } from './routes/faces';
import { footageRoutes } from './routes/footage';
import { platesRoutes } from './routes/plates';
import { searchRoutes } from './routes/search';
import { tripsRoutes } from './routes/trips';

export { DashboardDO };

export type Bindings = {
  DB: D1Database;
  FOOTAGE: R2Bucket;
  KV: KVNamespace;
  NOTIFICATION_QUEUE: Queue;
  VIDEO_QUEUE: Queue;
  DASHBOARD: DurableObjectNamespace;
  FACE_INDEX: Vectorize;
  SCENE_INDEX: Vectorize;
  NEVDIS_API_KEY: string;
  NEVDIS_API_URL: string;
  API_KEY: string;
};

const app = new Hono<{ Bindings: Bindings }>();

app.use('*', logger());
app.use('*', cors());

app.use('/api/*', async (c, next) => {
  const apiKey = c.req.header('X-API-Key');
  if (!apiKey || apiKey !== c.env.API_KEY) {
    return c.json({ error: 'Unauthorized' }, 401);
  }
  await next();
});

app.route('/api/alerts', alertsRoutes);
app.route('/api/plates', platesRoutes);
app.route('/api/faces', facesRoutes);
app.route('/api/trips', tripsRoutes);
app.route('/api/footage', footageRoutes);
app.route('/api/search', searchRoutes);

app.get('/ws/dashboard', async (c) => {
  const id = c.env.DASHBOARD.idFromName('fleet-dashboard');
  const stub = c.env.DASHBOARD.get(id);
  return stub.fetch(c.req.raw);
});

app.get('/health', (c) => c.json({ status: 'ok', timestamp: new Date().toISOString() }));

export default app;
